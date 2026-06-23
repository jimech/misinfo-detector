// TechnicalDetails.jsx
// A "page" presenting the project's technical depth and research findings.
// Content is largely drawn from the README, formatted for in-app reading.

// Small reusable styled pieces to keep the JSX readable.
const sectionStyle = { marginBottom: "2rem" };
const h2Style = { fontSize: "1.3rem", marginBottom: "0.6rem", color: "#1a1a2e" };
const pStyle = { color: "#344054", marginTop: 0 };

function TechnicalDetails() {
  return (
    <div>
      <section style={sectionStyle}>
        <h2 style={h2Style}>Overview</h2>
        <p style={pStyle}>
          This system extracts factual claims from short-form video scripts (or
          transcribed audio/video) and checks each claim against real evidence,
          labeling it supported, contradicted, or not enough evidence. It is built
          as a backend pipeline, a REST API, and this web frontend.
        </p>
      </section>

      <section style={sectionStyle}>
        <h2 style={h2Style}>Architecture</h2>
        <p style={pStyle}>The pipeline runs six stages:</p>
        <pre
          className="card-shadow"
          style={{
            background: "#1a1a2e",
            color: "#e6e6e6",
            padding: "1rem",
            borderRadius: "8px",
            overflow: "auto",
            fontSize: "0.82rem",
            lineHeight: 1.5,
          }}
        >
{`Input (script or video)
   │
   ▼
Transcription      ── Whisper (audio/video → text)
   │
   ▼
Claim Extraction   ── local LLM (Ollama) splits text into atomic claims
   │
   ▼
Evidence Retrieval ── Local corpus | Wikipedia (live) | Web search (Tavily)
   │
   ▼
Verification       ── NLI model  OR  LLM-as-judge
   │
   ▼
Explanation + Safer Rewrite (grounded in evidence)`}
        </pre>
      </section>

      <section style={sectionStyle}>
        <h2 style={h2Style}>Evaluation &amp; Research Findings</h2>
        <p style={pStyle}>
          The system was evaluated on a 12-claim labeled test set spanning all three
          verdict types. Two controlled experiments were run.
        </p>

        <h3 style={{ fontSize: "1.05rem", marginBottom: "0.3rem" }}>
          Experiment 1 — Decision threshold tuning
        </h3>
        <p style={pStyle}>
          Lowering the NLI decision threshold (0.50 → 0.40) did not improve accuracy
          (75% in both cases); it merely shifted one error between categories. This
          showed the errors stemmed from model comprehension, not threshold placement.
          The higher threshold was retained because it produced fewer "false claim →
          supported" errors — the most harmful failure for a misinformation tool.
        </p>

        <h3 style={{ fontSize: "1.05rem", marginBottom: "0.3rem", marginTop: "1rem" }}>
          Experiment 2 — NLI vs. LLM-as-judge
        </h3>
        <p style={pStyle}>
          Both verifiers scored 75% accuracy but with very different error profiles:
        </p>
        <table
          className="card-shadow"
          style={{
            borderCollapse: "collapse",
            width: "100%",
            fontSize: "0.88rem",
            background: "white",
            borderRadius: "8px",
            overflow: "hidden",
          }}
        >
          <thead>
            <tr style={{ background: "#f2f4f7", textAlign: "left" }}>
              <th style={{ padding: "8px 12px" }}>Metric</th>
              <th style={{ padding: "8px 12px" }}>NLI</th>
              <th style={{ padding: "8px 12px" }}>LLM-as-judge</th>
            </tr>
          </thead>
          <tbody>
            <tr style={{ borderTop: "1px solid #eaecf0" }}>
              <td style={{ padding: "8px 12px" }}>Overall accuracy</td>
              <td style={{ padding: "8px 12px" }}>75%</td>
              <td style={{ padding: "8px 12px" }}>75%</td>
            </tr>
            <tr style={{ borderTop: "1px solid #eaecf0" }}>
              <td style={{ padding: "8px 12px" }}>"Not enough evidence" accuracy</td>
              <td style={{ padding: "8px 12px" }}>67%</td>
              <td style={{ padding: "8px 12px", fontWeight: 700 }}>100%</td>
            </tr>
            <tr style={{ borderTop: "1px solid #eaecf0" }}>
              <td style={{ padding: "8px 12px" }}>High-confidence wrong answers</td>
              <td style={{ padding: "8px 12px" }}>2 (0.96, 0.99)</td>
              <td style={{ padding: "8px 12px", fontWeight: 700 }}>0</td>
            </tr>
            <tr style={{ borderTop: "1px solid #eaecf0" }}>
              <td style={{ padding: "8px 12px" }}>Error type</td>
              <td style={{ padding: "8px 12px" }}>scattered (incl. dangerous)</td>
              <td style={{ padding: "8px 12px" }}>all safe (over-cautious)</td>
            </tr>
          </tbody>
        </table>
        <p style={{ ...pStyle, marginTop: "0.8rem" }}>
          The LLM judge never produced a confident false verdict — all its errors were
          appropriately-uncertain "not enough evidence" responses, making it the safer
          choice despite identical headline accuracy. The tradeoff is higher latency.
        </p>
      </section>

      <section style={sectionStyle}>
        <h2 style={h2Style}>Tech Stack</h2>
        <ul style={{ color: "#344054", lineHeight: 1.8 }}>
          <li><strong>Backend:</strong> Python, FastAPI (REST API)</li>
          <li><strong>NLP / ML:</strong> sentence-transformers (embeddings + NLI), spaCy, faster-whisper</li>
          <li><strong>LLM:</strong> Ollama (local, llama3.2) — claim extraction, judging, rewrites</li>
          <li><strong>Retrieval:</strong> semantic search; Wikipedia API; Tavily web search</li>
          <li><strong>Frontend:</strong> React (this app), calling the API over HTTP</li>
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={h2Style}>Key Design Decisions</h2>
        <ul style={{ color: "#344054", lineHeight: 1.8 }}>
          <li>
            <strong>Swappable evidence sources</strong> behind one interface — local,
            Wikipedia, and live web — selectable at runtime.
          </li>
          <li>
            <strong>Two interchangeable verifiers</strong> (NLI and LLM) with matching
            signatures, enabling direct comparison.
          </li>
          <li>
            <strong>Local LLM by design</strong> — free, private, no API key required,
            and swappable for a hosted model with a one-function change.
          </li>
          <li>
            <strong>Frontend/backend separation</strong> — the UI is a pure client of
            the REST API, so any frontend can use the same backend.
          </li>
        </ul>
      </section>

      <section style={sectionStyle}>
        <h2 style={h2Style}>Known Limitations</h2>
        <ul style={{ color: "#344054", lineHeight: 1.8 }}>
          <li>Verdict quality is bounded by evidence quality; the curated corpus is small, and live sources can be noisy.</li>
          <li>The NLI verifier can confidently misjudge topically-related but non-addressing evidence; the LLM judge mitigates this.</li>
          <li>Transcribed speech lacks punctuation, so claim extraction relies on an LLM rather than rule-based splitting.</li>
          <li>The small local model limits extraction and judgment quality; a hosted LLM would improve results.</li>
          <li>TikTok/Instagram block automated downloads, so uploaded video files are used instead of URLs.</li>
        </ul>
      </section>
    </div>
  );
}

export default TechnicalDetails;