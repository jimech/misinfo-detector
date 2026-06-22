"""
retriever.py
-------------
Turns the evidence corpus into searchable vectors (embeddings) and
finds the most relevant evidence for a given claim — by MEANING,
not just matching keywords.

How it works:
  - Each evidence text becomes a vector (list of numbers) via a
    sentence-embedding model.
  - A claim is turned into a vector the same way.
  - Cosine similarity measures how close the claim is to each piece
    of evidence. Higher score = more related in meaning.

We wrap this in a class so the model + evidence vectors are computed
ONCE and reused for every search (computing them is the slow part).
"""

import numpy as np
from sentence_transformers import SentenceTransformer
from src.schemas import Evidence


class EvidenceRetriever:
    """Embeds the corpus once, then finds top matches for any claim."""

    def __init__(self, evidence: list[Evidence], model_name: str = "all-MiniLM-L6-v2"):
        # "all-MiniLM-L6-v2" is a small, fast, well-known embedding model.
        # It downloads automatically the first time (about 90 MB).
        self.model = SentenceTransformer(model_name)
        self.evidence = evidence

        # Pull out just the text of each evidence item.
        texts = [e.text for e in evidence]

        # Turn every evidence text into a vector, ONCE, here.
        # normalize_embeddings=True makes cosine similarity a simple dot product.
        self.evidence_vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    def search(self, claim_text: str, top_k: int = 3) -> list[Evidence]:
        """
        Return the top_k most relevant evidence items for a claim.
        Each returned Evidence has its .score filled in (the similarity).
        """
        # Embed the claim the same way we embedded the evidence.
        claim_vector = self.model.encode(
            [claim_text],
            normalize_embeddings=True,
            show_progress_bar=False,
        )[0]

        # Cosine similarity = dot product (because vectors are normalized).
        # This gives one score per evidence item.
        scores = np.dot(self.evidence_vectors, claim_vector)

        # Get the indices of the highest-scoring evidence, best first.
        top_indices = np.argsort(scores)[::-1][:top_k]

        # Build a result list, copying each Evidence and attaching its score.
        results: list[Evidence] = []
        for idx in top_indices:
            e = self.evidence[idx]
            results.append(
                Evidence(
                    source_title=e.source_title,
                    text=e.text,
                    support_type=e.support_type,   # still "neutral" for now
                    score=float(scores[idx]),      # how relevant it is
                )
            )
        return results