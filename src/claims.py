"""
claims.py
----------
Step 2 of the pipeline: extract atomic factual claims from sentences.

PUBLIC FUNCTION:  extract_claims(sentences) -> list[Claim]

Right now this uses simple rules (Option A). Later, an LLM-based
extractor can be dropped in by changing ONLY the body of
extract_claims() — everything that calls it stays the same.
"""

import re
import spacy
from src.schemas import Claim, Category

# Reuse spaCy's English model (same one T2 downloaded).
_nlp = spacy.load("en_core_web_sm")

# --- Signals that a sentence IS a checkable fact ---------------------

# Verbs/words that often introduce a factual assertion.
_FACTUAL_VERBS = {
    "is", "are", "was", "were", "causes", "cause", "cures", "cure",
    "contains", "contain", "prevents", "prevent", "increases", "increase",
    "reduces", "reduce", "kills", "kill", "costs", "cost", "equals",
    "means", "proves", "proven", "leads", "makes", "made", "has", "have",
}

# Phrases that signal a comparison (a checkable relationship).
_COMPARISON_PHRASES = [
    "better than", "worse than", "more than", "less than",
    "faster than", "stronger than", "cheaper than", "safer than",
]

# --- Signals that a sentence is NOT a checkable fact -----------------

# Opinion / hype markers — if a sentence is mostly this, we skip it.
_OPINION_MARKERS = [
    "i think", "i believe", "in my opinion", "imo", "i feel",
    "amazing", "awesome", "the best", "the worst", "beautiful",
    "incredible", "you won't believe", "trust me", "honestly",
]


def _looks_like_question(sentence: str) -> bool:
    """Questions aren't factual claims."""
    return sentence.strip().endswith("?")


def _is_mostly_opinion(sentence: str) -> bool:
    """True if the sentence is dominated by opinion/hype words."""
    low = sentence.lower()
    return any(marker in low for marker in _OPINION_MARKERS)


def _has_factual_signal(sentence: str) -> bool:
    """True if the sentence shows signs of a checkable fact."""
    low = sentence.lower()

    # 1) Comparison phrase present?
    if any(phrase in low for phrase in _COMPARISON_PHRASES):
        return True

    # Let spaCy analyse the sentence for numbers, entities, and verbs.
    doc = _nlp(sentence)

    # 2) Contains a number? (e.g. "330", "9.99", "50%")
    has_number = any(token.like_num for token in doc)
    if has_number:
        return True

    # 3) Contains a named entity? (person, place, org, date, etc.)
    has_entity = len(doc.ents) > 0
    if has_entity:
        return True

    # 4) Contains a factual verb?
    has_factual_verb = any(token.lemma_.lower() in _FACTUAL_VERBS for token in doc)
    if has_factual_verb:
        return True

    return False


def _split_compound(sentence: str) -> list[str]:
    """
    Try to split a sentence joined by 'and'/'because' into smaller
    atomic parts. This is a SIMPLE heuristic — the LLM version later
    will do this much better.

    Example:
      "it cures anxiety and works better than therapy"
      -> ["it cures anxiety", "works better than therapy"]
    """
    # Split on " and " or " because " (surrounded by spaces).
    parts = re.split(r"\s+(?:and|because)\s+", sentence, flags=re.IGNORECASE)
    parts = [p.strip(" .,!?") for p in parts if p.strip()]
    # Only treat as a real split if we got more than one meaningful part.
    return parts if len(parts) > 1 else [sentence]


def _guess_category(sentence: str) -> Category:
    """Very rough topic guess based on keywords. Default = other."""
    low = sentence.lower()
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


def extract_claims(sentences: list[str]) -> list[Claim]:
    """
    PUBLIC entry point. Turn sentences into a list of factual Claims.

    Steps:
      - skip questions and opinion-only sentences
      - keep sentences with a factual signal
      - try to split compound sentences into atomic pieces
      - guess a category for each claim
    """
    claims: list[Claim] = []

    for sentence in sentences:
        if _looks_like_question(sentence):
            continue
        if _is_mostly_opinion(sentence):
            continue
        if not _has_factual_signal(sentence):
            continue

        # Break compound sentences into smaller atomic claims.
        for part in _split_compound(sentence):
            # After splitting, re-check the part still has a factual signal.
            if _has_factual_signal(part):
                claims.append(
                    Claim(text=part, category=_guess_category(part))
                )

    return claims