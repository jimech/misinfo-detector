"""
retrieval_service.py
---------------------
A thin, stable layer over the retriever.

Why this exists:
  - Building the retriever embeds the whole corpus (slow), so we do
    it ONCE and cache it. Every later call reuses the same retriever.
  - The rest of the pipeline calls ONE function,
    get_evidence_for_claim(), and never needs to know how retrieval
    works inside. Swapping the corpus for a live search API later
    would change only this file.
"""

from typing import Optional
from src.corpus import load_evidence
from src.retriever import EvidenceRetriever
from src.schemas import Evidence

# Module-level cache for the retriever. Starts empty (None).
# We fill it the first time it's needed, then reuse it.
_retriever: Optional[EvidenceRetriever] = None

def _get_retriever() -> EvidenceRetriever:
    """Build the retriever once (lazy), then return the cached one."""
    global _retriever
    if _retriever is None:
        evidence = load_evidence()
        _retriever = EvidenceRetriever(evidence)
    return _retriever


def get_evidence_for_claim(claim_text: str, top_k: int = 3) -> list[Evidence]:
    """
    PUBLIC entry point: return the top_k most relevant evidence
    items for a single claim. Each item has its .score filled in.
    """
    retriever = _get_retriever()
    return retriever.search(claim_text, top_k=top_k)


def warm_up() -> None:
    """
    Optional: trigger the (slow) retriever build ahead of time.
    Handy for the UI later, so the first real search isn't slow.
    """
    _get_retriever()