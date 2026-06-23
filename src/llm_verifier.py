"""
llm_verifier.py
----------------
LLM-based claim verification using a local Ollama model.

Instead of an NLI model, we ask an LLM to read the claim and its
retrieved evidence, then decide: supported, contradicted, or
not_enough_evidence — with a confidence and a short reason.

This handles cases NLI struggled with: it can be explicitly told to
answer "not enough evidence" when evidence is topically related but
doesn't actually address the claim.

Runs LOCALLY via Ollama (free, no API key). Swapping to a paid API
later changes only _call_judge().

PUBLIC FUNCTION:
  verify_claim_llm(claim_text, evidence_list)
      -> (Verdict, confidence, scored_evidence)
"""

import json
from typing import List, Tuple, Optional
from src.schemas import Evidence, Verdict

# Which local Ollama model to use (same one from claim extraction).
_MODEL = "llama3.2"

# Below this retrieval relevance, evidence is treated as unrelated.
_RELEVANCE_FLOOR = 0.30

# The judge's instructions. We demand strict JSON for reliable parsing.
_SYSTEM_PROMPT = """You are a careful fact-checking judge.

You are given a CLAIM and several pieces of EVIDENCE. Decide whether the
evidence supports, contradicts, or is insufficient for the claim.

Strict rules:
- "supported": the evidence clearly confirms the claim.
- "contradicted": the evidence clearly refutes the claim.
- "not_enough_evidence": the evidence does not directly address the
  claim, is only loosely related, or is ambiguous. When in doubt,
  choose this. Do NOT guess.

Base your decision ONLY on the evidence provided. Do not use outside
knowledge. If the evidence is about a related topic but does not
actually confirm or refute THIS specific claim, choose
"not_enough_evidence".

Return ONLY valid JSON in this exact format:
{"verdict": "supported|contradicted|not_enough_evidence", "confidence": 0.0-1.0, "reason": "one short sentence"}"""


def _call_judge(claim_text: str, evidence_list: List[Evidence]) -> str:
    """
    Send the claim + evidence to the local LLM and return its raw reply.
    Isolated so swapping to a paid API later is a one-spot change.
    """
    import ollama

    # Format the evidence as a numbered list for the prompt.
    evidence_block = "\n".join(
        f"{i+1}. ({e.source_title}) {e.text}"
        for i, e in enumerate(evidence_list)
    )

    user_message = (
        f"CLAIM: {claim_text}\n\n"
        f"EVIDENCE:\n{evidence_block}\n\n"
        f"Decide: supported, contradicted, or not_enough_evidence."
    )

    response = ollama.chat(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        format="json",
        options={"temperature": 0.0},  # deterministic
    )
    return response["message"]["content"]


def _label_evidence(evidence_list: List[Evidence], verdict: Verdict) -> List[Evidence]:
    """
    Tag evidence with a support_type for display. The LLM gives one
    overall verdict, so we mark the most relevant evidence with it.
    """
    scored: List[Evidence] = []
    # Find the highest-scoring (most relevant) evidence index.
    best_idx = max(range(len(evidence_list)), key=lambda i: evidence_list[i].score) if evidence_list else None

    for i, e in enumerate(evidence_list):
        if i == best_idx and verdict == Verdict.supported:
            tag = "supports"
        elif i == best_idx and verdict == Verdict.contradicted:
            tag = "contradicts"
        else:
            tag = "neutral"
        scored.append(
            Evidence(
                source_title=e.source_title,
                text=e.text,
                support_type=tag,
                score=e.score,
            )
        )
    return scored


def verify_claim_llm(
    claim_text: str,
    evidence_list: List[Evidence],
) -> Tuple[Verdict, float, List[Evidence]]:
    """
    Judge a claim against its evidence using the local LLM.

    Returns (verdict, confidence, scored_evidence). Falls back to
    "not_enough_evidence" if the LLM errors or returns junk.
    """
    if not evidence_list:
        return Verdict.not_enough_evidence, 0.0, []

    # Drop clearly-unrelated evidence before judging.
    relevant = [e for e in evidence_list if e.score >= _RELEVANCE_FLOOR]
    if not relevant:
        # Nothing relevant enough -> not enough evidence.
        return Verdict.not_enough_evidence, 0.0, _label_evidence(evidence_list, Verdict.not_enough_evidence)

    # Ask the LLM.
    try:
        raw = _call_judge(claim_text, relevant)
        data = json.loads(raw)
        verdict_str = data.get("verdict", "not_enough_evidence")
        confidence = float(data.get("confidence", 0.0))
    except Exception as e:
        print(f"   [llm judge error] {type(e).__name__}: {e}")
        return Verdict.not_enough_evidence, 0.0, _label_evidence(evidence_list, Verdict.not_enough_evidence)

    # Map the string to our Verdict enum, defaulting safely.
    try:
        verdict = Verdict(verdict_str)
    except ValueError:
        verdict = Verdict.not_enough_evidence

    scored = _label_evidence(evidence_list, verdict)
    return verdict, confidence, scored