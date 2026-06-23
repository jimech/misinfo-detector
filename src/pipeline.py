"""
pipeline.py
------------
The full misinformation-detection pipeline behind ONE function.

analyze_script(text) runs all six steps in order:
  1. clean + split the script into sentences   (preprocess)
  2. extract atomic factual claims             (claims)
  3. retrieve relevant evidence per claim      (retrieval_service)
  4. verify each claim against its evidence    (verifier)
  5. attach a plain-English explanation        (explainer)
  -> returns a list of ClaimResult objects (the final display form)

The UI just calls analyze_script() and shows the results. It never
needs to know how the steps work inside.
"""

from typing import List
from src.schemas import ClaimResult
from src.preprocess import split_into_sentences
from src.claims import extract_claims
from src.retrieval_service import get_evidence_for_claim, warm_up
from src.verifier import verify_claim
from src.explainer import explain_verdict
from src.verifier import verify_claim
from src.verifier import verify_claim
from src.llm_verifier import verify_claim_llm


def analyze_script(
    text: str,
    top_k: int = 3,
    source: str = "local",
    verifier: str = "nli",
) -> List[ClaimResult]:
    """
    Run a raw script through the whole pipeline.

    Args:
        text:     the raw video script (one big string).
        top_k:    how many evidence items to retrieve per claim.
        source:   "local", "wikipedia", or "web".
        verifier: "nli" (fast NLI model) or "llm" (local LLM judge).

    Returns:
        A list of ClaimResult — one per extracted claim.
    """
    # Step 1: clean the script and split into sentences.
    sentences = split_into_sentences(text)

    # Step 2: pull out atomic factual claims.
    claims = extract_claims(sentences)

    # Pick the verification function.
    verify_fn = verify_claim_llm if verifier == "llm" else verify_claim

    results: List[ClaimResult] = []

    # Steps 3-5: for each claim, retrieve -> verify -> explain.
    for claim in claims:
        evidence = get_evidence_for_claim(claim.text, top_k=top_k, source=source)
        verdict, confidence, scored_evidence = verify_fn(claim.text, evidence)
        explanation = explain_verdict(claim.text, verdict, confidence, scored_evidence)

        results.append(
            ClaimResult(
                claim=claim.text,
                category=claim.category,
                verdict=verdict,
                confidence=confidence,
                evidence=scored_evidence,
                explanation=explanation,
            )
        )

    return results


# Re-export warm_up so the UI can pre-load models before first use,
# avoiding a slow first analysis. (Optional convenience.)
def preload() -> None:
    """Trigger model/retriever loading ahead of time."""
    warm_up()