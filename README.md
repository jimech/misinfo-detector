# 🔎 Misinformation Detector for Short-Form Video Scripts
 
An AI system that fact-checks the claims in short-form video content. Paste a script — or upload a video — and it extracts each factual claim, checks it against real evidence (live web, Wikipedia, or a curated corpus), labels it **supported / contradicted / not enough evidence**, explains the verdict, and suggests an accurate rewrite for anything false.
 
Built as a full-stack project: a Python ML pipeline, a FastAPI backend, and a React frontend.
 
---
 
## 🎬 Demo



https://github.com/user-attachments/assets/02127875-cdc9-4416-bec4-6624403ba0c8




*(Demo video embedded above — 75-second walkthrough: upload a video → automatic transcription → claim-by-claim fact-checking → safer rewrites → technical details.)*
 
---
 
## The Problem
 
Short-form video (TikTok, Reels, Shorts) is a primary news source for millions of people, and it's a fast vector for misinformation. Health myths, fabricated statistics, and false historical claims spread quickly and are rarely fact-checked. This project explores whether an AI pipeline can automatically surface and correct those claims.
 
## What It Does
 
Give it a script or a video, and for **each factual claim** it:
 
1. **Extracts** the claim from messy, run-on, spoken-style text.
2. **Retrieves evidence** from your chosen source (live web, Wikipedia, or a local corpus).
3. **Verifies** the claim against that evidence and assigns a verdict + confidence.
4. **Explains** the verdict in plain language, citing the evidence it used.
5. **Rewrites** contradicted claims into accurate versions.
## Features
 
- 📝 **Two input modes** — paste a script, or upload an audio/video file (transcribed automatically).
- 🌐 **Three evidence sources** — live web search (Tavily), live Wikipedia, or a curated local corpus.
- ⚖️ **Two verification methods** — a fast NLI model, or an LLM-as-judge (with a documented comparison of the two; see *Evaluation*).
- 🎙️ **Speech-to-text** — videos are transcribed with Whisper before analysis.
- ✏️ **Safer rewrites** — false claims get an accurate, suggested replacement.
- 🎨 **Polished web UI** — a React frontend with a live detector page and a technical-details page.
## How It Works
 
The analysis runs as a pipeline. Each claim flows through these stages:
 
```
            ┌─────────────┐
  script /  │  Transcribe │  (Whisper — only for uploaded audio/video)
  video ──► │  (optional) │
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │   Extract   │  Pull individual factual claims from the text
            │   claims    │  (LLM-based, with a rule-based fallback)
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │  Retrieve   │  Find relevant evidence for each claim
            │  evidence   │  (Web / Wikipedia / local corpus)
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │   Verify    │  supported / contradicted / not enough evidence
            │  + confidence│ (NLI model or LLM-as-judge)
            └──────┬──────┘
                   ▼
            ┌─────────────┐
            │  Explain &  │  Plain-language reason + a safer rewrite
            │   rewrite   │  for contradicted claims
            └─────────────┘
```
 
The frontend (React) calls the backend (FastAPI) over HTTP. The backend runs the pipeline and returns structured results that the UI renders as color-coded cards.
 
```
React frontend  ──HTTP──►  FastAPI backend  ──►  ML pipeline
 (Vite)                     /analyze                (claims, retrieval,
                            /transcribe              verification, rewrite)
```
 
## Tech Stack
 
| Layer | Tools |
|-------|-------|
| **Frontend** | React (Vite), glassmorphism UI |
| **Backend** | FastAPI, Uvicorn |
| **Claim extraction** | Ollama (Llama 3.2), with a rule-based fallback |
| **Evidence retrieval** | Tavily (web), Wikipedia API, sentence-transformers (semantic search over the local corpus) |
| **Verification** | Cross-encoder NLI (`nli-distilroberta-base`) and LLM-as-judge |
| **Transcription** | faster-whisper |
| **Schemas / validation** | Pydantic |
| **NLP preprocessing** | spaCy |
 
## Evaluation
 
A core part of this project was measuring the system rather than just building it. The pipeline is evaluated against a labeled test set, and two experiments are documented in full on the **Technical Details** page of the app.
 
**Experiment 1 — Threshold tuning.** Lowering the NLI decision threshold (0.50 → 0.40) did **not** change overall accuracy (75% either way); it only shifted *which* errors occurred. Conclusion: the errors come from model comprehension, not the threshold — so the threshold was kept conservative to minimize dangerous false-"supported" verdicts.
 
**Experiment 2 — NLI vs. LLM-as-judge.** Both methods scored 75% accuracy but with very different *error profiles*. The NLI model produced two high-confidence wrong answers (0.96 and 0.99) in dangerous directions. The LLM judge produced **zero** confident-wrong answers — all of its errors were safe, low-confidence "not enough evidence." Conclusion: for a misinformation use case, the LLM judge is **safer despite equal accuracy**, with latency as the tradeoff. The app defaults to NLI for speed but offers both.
 
> Takeaway: equal headline accuracy can hide very different real-world safety. *How* a model is wrong matters as much as how often.
 
## Running Locally
 
### Prerequisites
 
- **Python 3.9+** and **Node.js**
- **[Ollama](https://ollama.com)** with the Llama 3.2 model — for LLM claim extraction, judging, and rewrites:
```bash
  ollama pull llama3.2
```
- **ffmpeg** — required by Whisper for audio/video:
```bash
  brew install ffmpeg      # macOS
```
- A free **[Tavily](https://tavily.com)** API key — for live web search.
### Backend setup
 
```bash
# from the project root
python -m venv venv
source venv/bin/activate          # macOS/Linux
pip install -r requirements.txt
python -m spacy download en_core_web_sm
 
# add your Tavily key
cp .env.example .env
# then edit .env and set TAVILY_API_KEY=your-key-here
 
# run the API
uvicorn api.main:app --reload     # serves on http://localhost:8000
```
 
API docs are auto-generated at `http://localhost:8000/docs`.
 
### Frontend setup
 
```bash
# in a second terminal (venv NOT required for the frontend)
cd frontend
npm install
npm run dev                       # serves on http://localhost:5173
```
 
Open **http://localhost:5173** and you're running.
 
> **Note:** The local web app uses the full pipeline, including Whisper and a local LLM. These run on your machine — no cloud GPU needed — but transcription and LLM steps take a few seconds on CPU.
 
## Limitations
 
- **Claim extraction varies.** Spoken text lacks punctuation, so claim boundaries are sometimes merged or split. LLM extraction handles this better than rules, but it isn't perfect.
- **Verification accuracy is ~75%** on the test set. This is a research prototype, not a production fact-checker — verdicts should be treated as signals, not ground truth.
- **Evidence quality depends on the source.** Live web/Wikipedia retrieval is only as good as what's available and retrieved; the curated corpus is small by design.
- **CPU latency.** Transcription and LLM steps are noticeably slower without a GPU.
## Project Structure
 
```
misinfo-detector/
├── api/          # FastAPI backend (/analyze, /transcribe)
├── src/          # the ML pipeline (claims, retrieval, verification, rewrite, transcription)
├── frontend/     # React app (Vite)
├── app/          # Streamlit app (legacy / alternate UI)
├── data/         # curated evidence corpus + labeled test set
└── README.md
```
 
## Author
 
**Jimena Chinchilla**
[LinkedIn](https://linkedin.com/in/YOUR-LINKEDIN) · [GitHub](https://github.com/jimech)


