# Misinformation Detector for Short-Form Video Scripts

Detects misleading factual claims in short-form video content (TikTok, Reels, Shorts).
Paste a script — or upload a video — and the system extracts each factual claim,
checks it against real evidence, labels it **supported / contradicted / not enough
evidence**, and suggests a corrected version for flagged claims.

> Status: working prototype. Verdict accuracy depends on evidence quality and is
> not a substitute for professional fact-checking.

---

## What it does

Given a script or an uploaded audio/video file, the system:

1. **Transcribes** uploaded audio/video to text (via Whisper).
2. **Extracts atomic factual claims** from the text (via a local LLM).
3. **Retrieves evidence** for each claim from one of three sources.
4. **Verifies** each claim: supported, contradicted, or not enough evidence.
5. **Explains** the verdict, citing the evidence.
6. **Suggests a safer rewrite** for claims flagged as misinformation.

### Example

Input (spoken in a video):
> "The Eiffel Tower is 330 meters tall, drinking lemon water cures cancer,
> and bananas are a good source of potassium."

Output:

| Claim | Verdict | Evidence |
|---|---|---|
| The Eiffel Tower is 330 meters tall | Supported | Confirms ~330m height |
| Drinking lemon water cures cancer |  Contradicted | WHO: lemon water does not cure cancer |
| Bananas are a good source of potassium | Supported (web) | American Heart Association |

For the contradicted claim, it also suggests:
> "Lemon water provides vitamin C and hydration but does not cure or prevent cancer."

---

## Architecture

The system is split into a **backend pipeline** (`src/`), a **REST API** (`api/`),
and a **web UI** (`app/`).

***Frontend / backend separation:** the Streamlit UI calls the FastAPI backend over
HTTP, so the same API can serve any frontend (web, mobile, CLI).

```
Input (script or video)
        │
        ▼
[ Transcription ]  ── Whisper (uploaded audio/video → text)
        │
        ▼
[ Claim Extraction ]  ── local LLM (Ollama) splits text into atomic claims
        │
        ▼
[ Evidence Retrieval ]  ── one of three sources:
        │                    • Local curated corpus
        │                    • Wikipedia (live)
        │                    • Web search (Tavily, live)
        ▼
[ Verification ]  ── two interchangeable verifiers:
        │              • NLI model (fast)
        │              • LLM-as-judge (Ollama, better calibrated)
        ▼
[ Explanation + Safer Rewrite ]  ── grounded in retrieved evidence
        │
        ▼
   Results (JSON / UI cards)
```
---

## Key features

- **Three evidence sources**, switchable at runtime: curated corpus (fast, offline,
  reproducible), Wikipedia (broad), and live web search via Tavily (current,
  authoritative).
- **Two verifiers**, with a documented comparison: an NLI model and an LLM-as-judge.
- **Video / audio ingestion** via Whisper — upload a clip and fact-check what's said.
- **Local LLM** (Ollama) for claim extraction and rewriting — free, private, no API
  key required; swappable for a hosted API.
- **Safer rewrites** of flagged claims, grounded in the contradicting evidence.
- **REST API** (FastAPI) with auto-generated interactive docs.

---

## Tech stack

- **Backend:** Python, FastAPI
- **NLP / ML:** sentence-transformers (embeddings + NLI), spaCy, faster-whisper
- **LLM:** Ollama (local, `llama3.2`)
- **Retrieval:** semantic search over embeddings; Wikipedia API; Tavily web search
- **Frontend:** Streamlit
- **Validation:** Pydantic schemas throughout

---

## How to run

### Prerequisites
- Python 3.9+
- [ffmpeg](https://ffmpeg.org/) (for audio/video transcription) — `brew install ffmpeg`
- [Ollama](https://ollama.com/) with the `llama3.2` model — `ollama pull llama3.2`
- A [Tavily](https://tavily.com/) API key (free tier) for web-search mode

### Setup
```bash
git clone https://github.com/jimech/misinfo-detector.git
cd misinfo-detector

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm

# Add your Tavily key (see .env.example)
cp .env.example .env              # then edit .env and paste your key
```

### Run the backend API
```bash
uvicorn api.main:app --reload
# Interactive docs at http://localhost:8000/docs
```

### Run the web UI (in a second terminal)
```bash
streamlit run app/main.py
# Opens at http://localhost:8501
```

The UI calls the API, so keep both running.

---

## Evaluation

The system was evaluated on a 12-claim labeled test set spanning all three verdict
types. Two experiments are documented:

### Experiment 1 — Decision threshold tuning
Lowering the NLI decision threshold (0.50 → 0.40) did **not** improve accuracy
(75% in both cases); it merely shifted one error between *not_enough_evidence* and
*supported*. This showed the errors stemmed from model comprehension, not threshold
placement. The higher threshold was kept because it produced fewer "false claim →
supported" errors — the most harmful error type for a misinformation tool.

### Experiment 2 — NLI vs. LLM-as-judge
Both verifiers scored 75% accuracy, but with **very different error profiles**:

| | NLI | LLM-as-judge |
|---|---|---|
| Overall accuracy | 75% | 75% |
| `not_enough_evidence` accuracy | 67% | **100%** |
| High-confidence wrong answers | 2 (conf. 0.96, 0.99) | **0** |
| Error## Project structure

```
misinfo-detector/
├── api/          # FastAPI backend (REST endpoints)
├── app/          # Streamlit web UI
├── src/          # Core pipeline
│   ├── preprocess.py      # clean + split text
│   ├── claims.py          # claim extraction (rules + LLM)
│   ├── llm_claims.py      # LLM claim extractor
│   ├── corpus.py          # static evidence loader
│   ├── retriever.py       # semantic search over corpus
│   ├── wiki_retriever.py  # Wikipedia evidence
│   ├── web_retriever.py   # Tavily web evidence
│   ├── retrieval_service.py  # source switcher
│   ├── verifier.py        # NLI verification
│   ├── llm_verifier.py    # LLM-as-judge verification
│   ├── rewriter.py        # safer-rewrite generator
│   ├── explainer.py       # plain-English explanations
│   ├── transcriber.py     # Whisper transcription
│   ├── pipeline.py        # orchestrates everything
│   └── evaluate.py        # evaluation + metrics
├── data/         # evidence corpus + test set
└── requirements.txt
```

---

## Future work

- React frontend + deployment for a public-facing version.
- Hosted-LLM option for higher-quality extraction and judging.
- Larger evaluation set; per-source accuracy comparison.
- Evidence caching for repeat claims.