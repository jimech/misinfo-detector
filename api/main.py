"""
api/main.py
------------
FastAPI backend for the Misinformation Detector.

Exposes the fact-checking pipeline as a REST API. Any frontend
(Streamlit, React, mobile, curl) can POST a script and get back
structured results as JSON.

Run it with:   uvicorn api.main:app --reload
Then open:     http://localhost:8000/docs   (interactive API docs)
"""

import sys
from pathlib import Path
from typing import List

# Make 'src' importable (same path trick as the Streamlit app).
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.pipeline import analyze_script
from src.schemas import ClaimResult

# Create the FastAPI application.
app = FastAPI(
    title="Misinformation Detector API",
    description="Extracts factual claims from text and checks them against evidence.",
    version="1.0.0",
)

# CORS: allows a browser-based frontend (like a React site on a
# different address) to call this API. Without this, browsers block
# cross-origin requests. "*" allows all origins — fine for development;
# you'd restrict it to your real frontend domain in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request and response shapes -------------------------------------
# What the client must SEND to /analyze.
class AnalyzeRequest(BaseModel):
    text: str                       # the script to analyze
    source: str = "local"           # "local" | "wikipedia" | "web"
    verifier: str = "nli"           # "nli" | "llm"
    top_k: int = 3                  # evidence items per claim


# What /analyze SENDS BACK.
class AnalyzeResponse(BaseModel):
    claim_count: int
    flagged_count: int              # how many were contradicted
    results: List[ClaimResult]      # the full per-claim results


# --- Endpoints -------------------------------------------------------
@app.get("/")
def root():
    """A simple health check so you can confirm the API is running."""
    return {"status": "ok", "service": "Misinformation Detector API"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """
    Analyze a script: extract claims, verify each, return results.

    Send JSON like:
      {"text": "...", "source": "web", "verifier": "nli"}
    """
    results = analyze_script(
        request.text,
        top_k=request.top_k,
        source=request.source,
        verifier=request.verifier,
    )

    flagged = sum(1 for r in results if r.verdict.value == "contradicted")

    return AnalyzeResponse(
        claim_count=len(results),
        flagged_count=flagged,
        results=results,
    )