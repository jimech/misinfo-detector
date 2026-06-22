"""
wiki_retriever.py
------------------
Live evidence retriever backed by Wikipedia's official API,
called directly with `requests` (reliable, sends a proper
User-Agent, and lets us see real errors).

Flow for a claim:
  1. Search Wikipedia for related page titles.
  2. Fetch the intro extract of the top pages.
  3. Split that text into sentences (reuse spaCy via preprocess).
  4. Rank those sentences by similarity to the claim (embeddings).
  5. Return the best sentences as Evidence objects.
"""

from typing import List, Optional, Tuple

import requests
import numpy as np
from sentence_transformers import SentenceTransformer

from src.schemas import Evidence
from src.preprocess import split_into_sentences

# How many Wikipedia pages to pull per claim.
_MAX_PAGES = 3
# How many sentences to keep from each page before final ranking.
_SENTENCES_PER_PAGE = 40

# Wikipedia's action API endpoint. No key needed.
_WIKI_URL = "https://en.wikipedia.org/w/api.php"
# Wikipedia asks API clients to identify themselves; this avoids blocks.
_WIKI_HEADERS = {
    "User-Agent": "MisinfoDetector/0.1 (educational portfolio project; contact: student@example.com)"
}

# Reuse one embedding model.
_embed_model: Optional[SentenceTransformer] = None


def _get_embed_model() -> SentenceTransformer:
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def _fetch_page_texts(claim_text: str) -> List[Tuple[str, str]]:
    """
    Search Wikipedia via its official API and return (title, text)
    for the top matching pages' intro extracts.
    """
    results: List[Tuple[str, str]] = []

    # --- 1) Search for relevant page titles ---
    try:
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": claim_text,
            "srlimit": _MAX_PAGES,
            "format": "json",
        }
        r = requests.get(
            _WIKI_URL, params=search_params, headers=_WIKI_HEADERS, timeout=10
        )
        r.raise_for_status()
        hits = r.json().get("query", {}).get("search", [])
        titles = [h["title"] for h in hits]
    except Exception as e:
        print(f"   [wiki search error] {type(e).__name__}: {e}")
        return results

    # --- 2) Fetch the intro extract of each page ---
    for title in titles:
        try:
            extract_params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True,        # only the intro section
                "explaintext": True,    # plain text, no HTML
                "titles": title,
                "format": "json",
            }
            r = requests.get(
                _WIKI_URL, params=extract_params, headers=_WIKI_HEADERS, timeout=10
            )
            r.raise_for_status()
            pages = r.json().get("query", {}).get("pages", {})
            for _, page in pages.items():
                text = page.get("extract", "")
                if text:
                    results.append((title, text))
        except Exception as e:
            print(f"   [wiki fetch error] {type(e).__name__}: {e}")
            continue

    return results


def search_wikipedia(claim_text: str, top_k: int = 3) -> List[Evidence]:
    """
    Return the top_k most relevant Wikipedia sentences for a claim,
    as Evidence objects with their relevance score filled in.
    """
    pages = _fetch_page_texts(claim_text)
    if not pages:
        return []

    candidates: List[Tuple[str, str]] = []
    for title, text in pages:
        sentences = split_into_sentences(text)[:_SENTENCES_PER_PAGE]
        for s in sentences:
            if len(s.split()) >= 5:
                candidates.append((s, title))

    if not candidates:
        return []

    model = _get_embed_model()
    claim_vec = model.encode([claim_text], normalize_embeddings=True)[0]

    sentence_texts = [c[0] for c in candidates]
    sentence_vecs = model.encode(sentence_texts, normalize_embeddings=True)

    scores = np.dot(sentence_vecs, claim_vec)
    top_idx = np.argsort(scores)[::-1][:top_k]

    evidence: List[Evidence] = []
    for idx in top_idx:
        sentence, title = candidates[idx]
        evidence.append(
            Evidence(
                source_title=f"Wikipedia: {title}",
                text=sentence,
                support_type="neutral",
                score=float(scores[idx]),
            )
        )
    return evidence