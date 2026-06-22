"""
retrieval_service.py
---------------------
Stable layer over evidence retrieval. Now supports TWO sources:

  - "local"     : the curated 12-fact corpus (fast, offline, used by
                  the test set so evaluation stays reproducible).
  - "wikipedia" : live Wikipedia retrieval (works on almost any claim).

The rest of the pipeline still calls ONE function,
get_evidence_for_claim(), and just passes which source to use.
"""

from typing import Optional, List
from src.corpus import load_evidence
from src.retriever import EvidenceRetriever
from src.wiki_retriever import search_wikipedia
from src.schemas import Evidence

# Cache for the static (local) retriever.
_retriever: Optional[EvidenceRetriever] = None


def _get_local_retriever() -> EvidenceRetriever:
    """Build the static-corpus retriever once, then reuse it."""
    global _retriever
    if _retriever is None:
        evidence = load_evidence()
        _retriever = EvidenceRetriever(evidence)
    return _retriever


def get_evidence_for_claim(
    claim_text: str,
    top_k: int = 3,
    source: str = "local",
) -> List[Evidence]:
    """
    Return the top_k most relevant evidence items for a claim.

    Args:
        claim_text: the claim to find evidence for.
        top_k:      how many evidence items to return.
        source:     "local" (curated corpus) or "wikipedia" (live).
    """
    if source == "wikipedia":
        return search_wikipedia(claim_text, top_k=top_k)

    # Default: local curated corpus.
    retriever = _get_local_retriever()
    return retriever.search(claim_text, top_k=top_k)


def warm_up(source: str = "local") -> None:
    """Pre-load models so the first real query isn't slow."""
    if source == "wikipedia":
        # Trigger the embedding model load via a tiny throwaway query.
        search_wikipedia("test", top_k=1)
    else:
        _get_local_retriever()