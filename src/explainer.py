"""
explainer.py
-------------
Step 6 of the pipeline: turn a verdict + evidence into a short,
human-readable explanation.

We use simple sentence TEMPLATES (no AI model). The explanation only
repeats real evidence, so it is always accurate and never invents
anything. An LLM-based explainer could replace the body of
explain_verdict() later without changing anything else.

PUBLIC FUNCTION:
  explain_verdict(claim_text, verdict, confidence, evidence) -> str
"""

from typing import List
from src.schemas import Evidence, Verdict


def _confidence_word(confidence: float) -> str:
    """Turn a 0-1 number into a friendly strength word."""
    if confidence >= 0.75:
        return "strong"
    if confidence >= 0.50:
        return "moderate"
    return "weak"


def _find_best(evidence: List[Evidence], support_type: str) -> Evidence:
    """
    Return the evidence item whose support_type matches (e.g. the
    'contradicts' one), preferring higher relevance score. Returns
    None if none match.
    """
    matches = [e for e in evidence if e.support_type == support_type]
    if not matches:
        return None
    # Highest retrieval score first.
    matches.sort(key=lambda e: e.score, reverse=True)
    return matches[0]


def explain_verdict(
    claim_text: str,
    verdict: Verdict,
    confidence: float,
    evidence: List[Evidence],
) -> str:
    """Build a plain-English explanation string for one judged claim."""
    strength = _confidence_word(confidence)

    if verdict == Verdict.supported:
        best = _find_best(evidence, "supports")
        if best:
            return (
                f"This claim appears SUPPORTED ({strength} confidence). "
                f"According to {best.source_title}: \"{best.text}\""
            )
        # Fallback if labels are odd but verdict says supported.
        return f"This claim appears SUPPORTED ({strength} confidence) by the retrieved evidence."

    if verdict == Verdict.contradicted:
        best = _find_best(evidence, "contradicts")
        if best:
            return (
                f"⚠️ This claim appears CONTRADICTED ({strength} confidence). "
                f"According to {best.source_title}: \"{best.text}\" "
                f"Be cautious about repeating this claim."
            )
        return f"⚠️ This claim appears CONTRADICTED ({strength} confidence) by the retrieved evidence."

    # not_enough_evidence
    if evidence:
        closest = max(evidence, key=lambda e: e.score)
        return (
            f"There is NOT ENOUGH EVIDENCE to judge this claim. "
            f"The closest source found was {closest.source_title}, but it does not "
            f"clearly support or contradict the claim. Treat it as unverified."
        )
    return (
        "There is NOT ENOUGH EVIDENCE to judge this claim. No relevant sources "
        "were found, so it should be treated as unverified."
    )