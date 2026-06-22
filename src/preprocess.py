"""
preprocess.py
--------------
Step 1 of the pipeline: clean a raw script and split it into sentences.

A raw script is one big messy string. We:
  1. Tidy up the text (remove weird spacing, common filler words).
  2. Use spaCy to split it into proper sentences.

Sentences are the unit everything downstream works on.
"""

import re
import spacy

# Load spaCy's small English model ONCE when this file is imported.
# Loading is a bit slow, so we do it a single time and reuse it.
_nlp = spacy.load("en_core_web_sm")

# Common filler words/phrases in casual video scripts that add no meaning.
# We strip these so they don't clutter our sentences.
_FILLER_PATTERNS = [
    r"\bum+\b",       # um, ummm
    r"\buh+\b",       # uh, uhhh
    r"\blike,\s",     # "like, " used as filler
    r"\byou know\b",  # "you know"
    r"\bbasically\b",
    r"\bliterally\b",
]


def clean_text(text: str) -> str:
    """Tidy up raw script text before splitting."""
    # Make everything lowercase for filler-matching, but keep a copy?
    # We'll keep original case — only remove filler, don't lowercase the
    # whole thing, because casing can matter for names later.

    # Remove each filler pattern (case-insensitive).
    for pattern in _FILLER_PATTERNS:
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)

    # Collapse multiple spaces/newlines/tabs into a single space.
    text = re.sub(r"\s+", " ", text)

    # Remove spaces sitting right before punctuation (" ." -> ".").
    text = re.sub(r"\s+([.!?,])", r"\1", text)

    return text.strip()


def split_into_sentences(text: str) -> list[str]:
    """Clean the text, then split it into a list of sentences."""
    cleaned = clean_text(text)

    # spaCy reads the text and figures out sentence boundaries.
    doc = _nlp(cleaned)

    # doc.sents is spaCy's list of detected sentences.
    # We strip each one and drop any empty leftovers.
    sentences = [sent.text.strip() for sent in doc.sents]
    sentences = [s for s in sentences if s]

    return sentences