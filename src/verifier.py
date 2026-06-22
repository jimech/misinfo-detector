"""
verifier.py
------------
Step 5 of the pipeline: decide whether retrieved evidence SUPPORTS,
CONTRADICTS, or is NOT ENOUGH for a claim.

We use Natural Language Inference (NLI). An NLI model reads a
(premise, hypothesis) pair and judges their relationship:
  - entailment    -> premise SUPPORTS hypothesis
  - contradiction -> premise CONTRADICTS hypothesis
  - neutral       -> not enough to decide

We set:
  premise    = an evidence text
  hypothesis = the claim

So entailment => "supported", contradiction => "contradicted",
neutral / weak => "not_enough_evidence".

PUBLIC FUNCTION:
  verify_claim(claim_text, evidence_list) -> (Verdict, confidence, scored_evidence)
"""

import numpy as np
from typing import Optional, Tuple, List
from sentence_transformers import CrossEncoder
from src.schemas import Evidence, Verdict

# Reuse sentence-transformers (already installed). This NLI model uses a
# RoBERTa tokenizer (no extra 'sentencepiece' install needed) and runs on
# CPU. Downloads once (~330 MB) on first use, then is cached.
_MODEL_NAME = "cross-encoder/nli-distilroberta-base"

# NLI models output three scores in THIS fixed order:
_LABELS = ["contradiction", "entailment", "neutral"]

# If the most relevant evidence scores below this retrieval relevance,
# we treat it as unrelated and lean toward "not enough evidence".
_RELEVANCE_FLOOR = 0.30

# How confident NLI must be before we commit to supported/contradicted.
_DECISION_THRESHOLD = 0.50

# Cache the model so it loads only once.
_model: Optional[CrossEncoder] = None


def _get_model() -> CrossEncoder:
    """Load the NLI model once, then reuse it."""
    global _model
    if _model is None:
        _model = CrossEncoder(_MODEL_NAME)
    return _model


def _softmax(logits: np.ndarray) -> np.ndarray:
    """Turn raw model scores into probabilities that add up to 1."""
    e = np.exp(logits - np.max(logits))
    return e / e.sum()


def verify_claim(
    claim_text: str,
    evidence_list: List[Evidence],
) -> Tuple[Verdict, float, List[Evidence]]:
    """
    Judge a claim against its retrieved evidence.

    Returns:
      verdict    : supported | contradicted | not_enough_evidence
      confidence : 0.0 - 1.0
      evidence   : the same evidence, each tagged with support_type
                   ("supports" / "contradicts" / "neutral")
    """
    # No evidence at all -> nothing to go on.
    if not evidence_list:
        return Verdict.not_enough_evidence, 0.0, []

    model = _get_model()

    # Build (premise=evidence, hypothesis=claim) pairs for every evidence.
    pairs = [(e.text, claim_text) for e in evidence_list]

    # One NLI prediction per pair. Each row = scores for [contra, entail, neutral].
    logits = np.array(model.predict(pairs, show_progress_bar=False))
    if logits.ndim == 1:          # safety if only one pair
        logits = logits.reshape(1, -1)

    # Track the single best "support" and best "contradict" signals
    # among RELEVANT evidence.
    best_entail = {"prob": 0.0, "idx": None}
    best_contra = {"prob": 0.0, "idx": None}

    scored_evidence: List[Evidence] = []

    for i, e in enumerate(evidence_list):
        probs = _softmax(logits[i])
        p_contra = float(probs[0])
        p_entail = float(probs[1])

        # Label this evidence for display in the UI later.
        top = int(np.argmax(probs))
        if _LABELS[top] == "entailment":
            support_type = "supports"
        elif _LABELS[top] == "contradiction":
            support_type = "contradicts"
        else:
            support_type = "neutral"

        scored_evidence.append(
            Evidence(
                source_title=e.source_title,
                text=e.text,
                support_type=support_type,
                score=e.score,  # keep the retrieval relevance score
            )
        )

        # Only let RELEVANT evidence influence the final verdict.
        if e.score >= _RELEVANCE_FLOOR:
            if p_entail > best_entail["prob"]:
                best_entail = {"prob": p_entail, "idx": i}
            if p_contra > best_contra["prob"]:
                best_contra = {"prob": p_contra, "idx": i}

    # --- Make the final decision -------------------------------------
    # Contradiction wins close calls: it's safer to FLAG a claim than to
    # wrongly bless misinformation as "supported".
    if best_contra["prob"] >= _DECISION_THRESHOLD and best_contra["prob"] >= best_entail["prob"]:
        return Verdict.contradicted, best_contra["prob"], scored_evidence

    if best_entail["prob"] >= _DECISION_THRESHOLD:
        return Verdict.supported, best_entail["prob"], scored_evidence

    # Nothing confident enough -> not enough evidence.
    # Confidence = how far we were from making a support/contradict call.
    weak_conf = 1.0 - max(best_entail["prob"], best_contra["prob"])
    return Verdict.not_enough_evidence, weak_conf, scored_evidence