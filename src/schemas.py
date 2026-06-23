"""
schemas.py
-----------
Defines the data shapes used across the whole pipeline.

Think of these as "forms" that every part of the system fills in.
Using Pydantic means the data is automatically checked: if a field
is the wrong type, we find out right away instead of much later.
"""

from enum import Enum
from pydantic import BaseModel, Field


# An Enum is a fixed set of allowed values.
# A claim's category can ONLY be one of these — nothing else is allowed.
class Category(str, Enum):
    health = "health"
    finance = "finance"
    science = "science"
    politics = "politics"
    celebrity = "celebrity"
    other = "other"


# The final verdict for a claim can ONLY be one of these three.
class Verdict(str, Enum):
    supported = "supported"
    contradicted = "contradicted"
    not_enough_evidence = "not_enough_evidence"


# One piece of evidence we found for a claim.
class Evidence(BaseModel):
    source_title: str                 # where the evidence came from
    text: str                         # the actual evidence sentence(s)
    support_type: str = "neutral"     # "supports" | "contradicts" | "neutral"
    score: float = 0.0                # how relevant it is (filled in later)


# One factual claim pulled out of the script.
class Claim(BaseModel):
    text: str                                  # the claim itself
    category: Category = Category.other        # its topic, default "other"


# The full result for one claim, after we've checked it.
# This is what the UI will display.
class ClaimResult(BaseModel):
    claim: str                                       # the claim text
    category: Category = Category.other
    verdict: Verdict = Verdict.not_enough_evidence   # our judgement
    confidence: float = 0.0                          # 0.0 to 1.0
    evidence: list[Evidence] = Field(default_factory=list)  # supporting evidence
    explanation: str = ""                            # plain-English reasoning
    safer_rewrite: str = ""                          # corrected version (if flagged)