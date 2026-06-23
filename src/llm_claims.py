"""
llm_claims.py
--------------
LLM-based atomic claim extraction using a local Ollama model.

Why this exists:
  Rule-based extraction (claims.py) struggles with run-on text,
  especially transcribed speech which lacks sentence punctuation.
  An LLM reads the text and cleanly separates atomic factual claims
  regardless of punctuation.

This runs a LOCAL model via Ollama (free, no API key). To switch to
a paid API later, only _call_llm() needs to change.

PUBLIC FUNCTION:
  extract_claims_llm(text) -> list[Claim]
"""

import json
from typing import List
from src.schemas import Claim, Category

# Which local Ollama model to use.
_MODEL = "llama3.2"

# The instruction we give the model. We ask for STRICT JSON so we can
# parse it reliably. Being very explicit reduces messy output.
_SYSTEM_PROMPT = """You extract atomic factual claims from text.

An atomic factual claim is a single, checkable statement of fact.
Rules:
- Split compound sentences into separate claims.
- Ignore opinions, questions, greetings, and hype.
- Each claim must be ONE checkable fact.
- Rephrase each claim as a clear, standalone statement.

Return ONLY valid JSON in this exact format, nothing else:
{"claims": ["claim one", "claim two", ...]}

If there are no factual claims, return {"claims": []}."""


def _call_llm(text: str) -> str:
    """
    Send the text to the local Ollama model and return its raw reply.
    Isolated here so swapping to a paid API later is a one-spot change.
    """
    import ollama

    response = ollama.chat(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        # format="json" asks Ollama to return valid JSON.
        format="json",
        options={"temperature": 0.0},  # deterministic, no creativity
    )
    return response["message"]["content"]


def _guess_category(claim_text: str) -> Category:
    """Same simple keyword categoriser used by the rule-based version."""
    low = claim_text.lower()
    if any(w in low for w in ["cancer", "anxiety", "vaccine", "diet", "cure", "health", "disease"]):
        return Category.health
    if any(w in low for w in ["stock", "crypto", "money", "invest", "price", "$", "profit"]):
        return Category.finance
    if any(w in low for w in ["study", "scientist", "research", "physics", "space", "climate"]):
        return Category.science
    if any(w in low for w in ["government", "president", "election", "policy", "senate"]):
        return Category.politics
    if any(w in low for w in ["celebrity", "actor", "singer", "movie", "famous"]):
        return Category.celebrity
    return Category.other


def extract_claims_llm(text: str) -> List[Claim]:
    """
    Extract atomic factual claims from text using the local LLM.
    Falls back to an empty list if the model output can't be parsed.
    """
    try:
        raw = _call_llm(text)
    except Exception as e:
        print(f"   [llm error] {type(e).__name__}: {e}")
        return []

    # Parse the JSON the model returned.
    try:
        data = json.loads(raw)
        claim_texts = data.get("claims", [])
    except Exception as e:
        print(f"   [llm parse error] {type(e).__name__}: {e}")
        print(f"   raw output was: {raw[:200]}")
        return []

    # Build Claim objects, skipping anything empty or too short.
    claims: List[Claim] = []
    for ct in claim_texts:
        ct = (ct or "").strip()
        if len(ct.split()) >= 3:  # ignore fragments
            claims.append(Claim(text=ct, category=_guess_category(ct)))

    return claims