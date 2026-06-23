"""
rewriter.py
------------
Generates a "safer rewrite" for a contradicted claim.

When a claim is flagged as misinformation (contradicted), this asks
the local LLM to produce a corrected, accurate version — grounded in
the evidence that contradicted the original claim, NOT invented.

Runs LOCALLY via Ollama (free). Swapping to a paid API later changes
only _call_rewriter().

PUBLIC FUNCTION:
  suggest_safer_rewrite(claim_text, evidence_list) -> str
"""

from typing import List
from src.schemas import Evidence

_MODEL = "llama3.2"

# Instructions for the rewrite. We stress grounding in the evidence
# and keeping it short and clear.
_SYSTEM_PROMPT = """You correct misleading factual claims.

You are given a CLAIM that has been found to be false or misleading,
along with the EVIDENCE that contradicts it. Write a corrected,
accurate version of the claim.

Rules:
- Base the correction ONLY on the provided evidence.
- Keep it to one or two clear sentences.
- Make it factual and neutral, not preachy.
- Do not add information that is not supported by the evidence.

Return ONLY valid JSON in this format:
{"rewrite": "the corrected statement"}"""


def _call_rewriter(claim_text: str, evidence_list: List[Evidence]) -> str:
    """Send the claim + contradicting evidence to the LLM. Returns raw reply."""
    import ollama

    evidence_block = "\n".join(
        f"{i+1}. ({e.source_title}) {e.text}"
        for i, e in enumerate(evidence_list)
    )

    user_message = (
        f"CLAIM (false/misleading): {claim_text}\n\n"
        f"EVIDENCE:\n{evidence_block}\n\n"
        f"Write a corrected, accurate version."
    )

    response = ollama.chat(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        format="json",
        options={"temperature": 0.3},  # a little flexibility for phrasing
    )
    return response["message"]["content"]


def suggest_safer_rewrite(claim_text: str, evidence_list: List[Evidence]) -> str:
    """
    Return a corrected version of a contradicted claim, or an empty
    string if no rewrite could be produced.
    """
    import json

    if not evidence_list:
        return ""

    try:
        raw = _call_rewriter(claim_text, evidence_list)
        data = json.loads(raw)
        rewrite = (data.get("rewrite") or "").strip()
        return rewrite
    except Exception as e:
        print(f"   [rewrite error] {type(e).__name__}: {e}")
        return ""