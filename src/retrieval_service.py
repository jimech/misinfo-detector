"""
retrieval_service.py
---------------------
Stable layer over evidence retrieval. Supports THREE sources:

  - "local"     : curated 12-fact corpus (fast, offline, reproducible).
  - "wikipedia" : live Wikipedia retrieval (broad, factual).
  - "web"       : live Tavily web search (broadest, most current).

The rest of the pipeline calls ONE function, get_evidence_for_claim(),
and just passes which source to use.
"""

from typing import Optional, List
from src.corpus import load_evidence
from src.retriever import EvidenceRetriever
from src.wiki_retriever import search_wikipedia
from src.web_retriever import search_web
from src.schemas import Evidence

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
        source:     "local", "wikipedia", or "web".
    """
    if source == "wikipedia":
        return search_wikipedia(claim_text, top_k=top_k)
    if source == "web":
        return search_web(claim_text, top_k=top_k)

    # Default: local curated corpus.
    retriever = _get_local_retriever()
    return retriever.search(claim_text, top_k=top_k)


def warm_up(source: str = "local") -> None:
    """Pre-load models so the first real query isn't slow."""
    if source == "wikipedia":
        search_wikipedia("test", top_k=1)
    elif source == "web":
        search_web("test", top_k=1)
    else:
        _get_local_retriever()