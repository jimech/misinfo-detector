"""
web_retriever.py
-----------------
Live evidence retriever backed by the Tavily web search API.

Like the Wikipedia retriever, it returns the SAME Evidence shape,
so the rest of the pipeline doesn't change.

The API key is read from a .env file via python-dotenv. The key is
NEVER written in this code — it stays in .env, which git ignores.

Flow for a claim:
  1. Send the claim to Tavily's search API.
  2. Tavily returns clean text snippets from across the web.
  3. Split those snippets into sentences (reuse spaCy).
  4. Rank sentences by similarity to the claim (embeddings).
  5. Return the best ones as Evidence objects.
"""

import os
from typing import List, Optional, Tuple

import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from src.schemas import Evidence
from src.preprocess import split_into_sentences

# Load variables from .env into the environment (reads TAVILY_API_KEY).
load_dotenv()

# How many web results to request, and sentence cap per result.
_MAX_RESULTS = 5
_SENTENCES_PER_RESULT = 30

# Reuse one embedding model.
_embed_model: Optional[SentenceTransformer] = None
# Cache the Tavily client so we build it once.
_tavily_client = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def _get_tavily_client():
    """Build the Tavily client once, using the key from the environment."""
    global _tavily_client
    if _tavily_client is None:
        from tavily import TavilyClient

        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError(
                "TAVILY_API_KEY not found. Make sure you created a .env file "
                "in the project root with TAVILY_API_KEY=your-key, and that "
                "python-dotenv is installed."
            )
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


def _fetch_web_snippets(claim_text: str) -> List[Tuple[str, str]]:
    """
    Query Tavily and return (source_title, text) pairs from the
    web results. Fails gracefully on any error.
    """
    results: List[Tuple[str, str]] = []
    try:
        client = _get_tavily_client()
        # search_depth="basic" is fast and counts as one search.
        response = client.search(
            query=claim_text,
            search_depth="basic",
            max_results=_MAX_RESULTS,
        )
    except Exception as e:
        print(f"   [web search error] {type(e).__name__}: {e}")
        return results

    # Each result has a title, url, and "content" (a clean text snippet).
    for item in response.get("results", []):
        title = item.get("title", "Web source")
        url = item.get("url", "")
        content = item.get("content", "")
        if content:
            # Use a short, readable source label.
            label = f"{title}" if title else url
            results.append((label, content))

    return results


def search_web(claim_text: str, top_k: int = 3) -> List[Evidence]:
    """
    Return the top_k most relevant web sentences for a claim,
    as Evidence objects with their relevance score filled in.
    """
    snippets = _fetch_web_snippets(claim_text)
    if not snippets:
        return []

    # Break snippets into candidate sentences.
    candidates: List[Tuple[str, str]] = []
    for source_title, content in snippets:
        sentences = split_into_sentences(content)[:_SENTENCES_PER_RESULT]
        for s in sentences:
            if len(s.split()) >= 5:
                candidates.append((s, source_title))

    if not candidates:
        return []

    # Rank candidate sentences by similarity to the claim.
    model = _get_embed_model()
    claim_vec = model.encode([claim_text], normalize_embeddings=True)[0]

    sentence_texts = [c[0] for c in candidates]
    sentence_vecs = model.encode(sentence_texts, normalize_embeddings=True)

    scores = np.dot(sentence_vecs, claim_vec)
    top_idx = np.argsort(scores)[::-1][:top_k]

    evidence: List[Evidence] = []
    for idx in top_idx:
        sentence, source_title = candidates[idx]
        evidence.append(
            Evidence(
                source_title=f"Web: {source_title}",
                text=sentence,
                support_type="neutral",
                score=float(scores[idx]),
            )
        )
    return evidence