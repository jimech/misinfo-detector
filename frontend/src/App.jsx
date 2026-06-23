import { useState } from "react";
import ResultCard from "./ResultCard";
import TechnicalDetails from "./TechnicalDetails";

const API_URL = "http://localhost:8000";

const EXAMPLE_SCRIPT =
  "Okay listen up! Drinking lemon water every morning cures cancer, trust me. " +
  "The Eiffel Tower is 330 meters tall. Marie Curie won the Nobel Prize in " +
  "Literature. Studies show getting 7 to 9 hours of sleep is healthy.";

function App() {
  const [page, setPage] = useState("home"); // "home" or "tech"
  const [inputMode, setInputMode] = useState("paste"); // "paste" or "upload"
  const [transcribing, setTranscribing] = useState(false);
  const [script, setScript] = useState(EXAMPLE_SCRIPT);
  const [source, setSource] = useState("local");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function analyze() {
    setLoading(true);
    setError("");
    setResults(null);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: script, source: source, verifier: "nli" }),
      });
      if (!response.ok) throw new Error(`API returned status ${response.status}`);
      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(`${err.message}. Is the API running?`);
    } finally {
      setLoading(false);
    }
  }

  // Upload a file to /transcribe and put the result in the script box.
  async function transcribeFile(file) {
    setTranscribing(true);
    setError("");
    try {
      // FormData is how you send files in a browser HTTP request.
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_URL}/transcribe`, {
        method: "POST",
        body: formData, // no Content-Type header — the browser sets it
      });
      if (!response.ok) throw new Error(`Transcription failed (status ${response.status})`);
      const data = await response.json();
      setScript(data.transcript); // drop the transcript into the editable box
    } catch (err) {
      setError(`${err.message}. Is the API running?`);
    } finally {
      setTranscribing(false);
    }
  }

  return (
    <div
      style={{
        maxWidth: "760px",
        margin: "0 auto",
        padding: "2rem 1.5rem",
      }}
    >
      {/* Nav bar with two links */}
      <nav
        style={{
          display: "flex",
          gap: "1.5rem",
          borderBottom: "1px solid #eaecf0",
          paddingBottom: "0.8rem",
          marginBottom: "1.5rem",
        }}
      >
        <span
          onClick={() => setPage("home")}
          style={{
            cursor: "pointer",
            fontWeight: page === "home" ? 700 : 400,
            color: page === "home" ? "#1a1a2e" : "#667085",
            borderBottom: page === "home" ? "2px solid #1a1a2e" : "2px solid transparent",
            paddingBottom: "0.4rem",
          }}
        >
          🔎 Detector
        </span>
        <span
          onClick={() => setPage("tech")}
          style={{
            cursor: "pointer",
            fontWeight: page === "tech" ? 700 : 400,
            color: page === "tech" ? "#1a1a2e" : "#667085",
            borderBottom: page === "tech" ? "2px solid #1a1a2e" : "2px solid transparent",
            paddingBottom: "0.4rem",
          }}
        >
          📄 Technical Details
        </span>
      </nav>

      {/* Show the technical page if selected, otherwise the detector */}
      {page === "tech" ? (
        <TechnicalDetails />
      ) : (
        <>
          <header style={{ marginBottom: "1.5rem" }}>
            <h1 style={{ margin: 0, fontSize: "1.9rem" }}>🔎 Misinformation Detector</h1>
            <p style={{ color: "#667085", marginTop: "0.4rem", marginBottom: 0 }}>
              Paste a script or upload a video. Each factual claim is checked against evidence.
            </p>
          </header>

          {/* Input method toggle */}
          <div style={{ marginBottom: "1rem", display: "flex", gap: "1rem" }}>
            <label style={{ fontSize: "0.9rem", cursor: "pointer" }}>
              <input
                type="radio"
                checked={inputMode === "paste"}
                onChange={() => setInputMode("paste")}
              />{" "}
              Paste a script
            </label>
            <label style={{ fontSize: "0.9rem", cursor: "pointer" }}>
              <input
                type="radio"
                checked={inputMode === "upload"}
                onChange={() => setInputMode("upload")}
              />{" "}
              Upload audio/video
            </label>
          </div>

          {/* File picker (only in upload mode) */}
          {inputMode === "upload" && (
            <div style={{ marginBottom: "1rem" }}>
              <input
                type="file"
                accept=".mp3,.m4a,.wav,.mp4,.mov,.webm,.ogg"
                onChange={(e) => {
                  if (e.target.files[0]) transcribeFile(e.target.files[0]);
                }}
                disabled={transcribing}
              />
              {transcribing && (
                <span style={{ marginLeft: "0.5rem", color: "#667085", fontSize: "0.9rem" }}>
                  Transcribing… (can take a bit)
                </span>
              )}
            </div>
          )}

          {/* Script input (editable; holds pasted text or the transcript) */}
          <textarea
            value={script}
            onChange={(e) => setScript(e.target.value)}
            rows={6}
            style={{
              width: "100%",
              padding: "12px",
              fontSize: "1rem",
              borderRadius: "8px",
              border: "1px solid #ccc",
              fontFamily: "inherit",
              boxSizing: "border-box",
            }}
          />

          {/* Source selector + Analyze button */}
          <div style={{ display: "flex", gap: "12px", alignItems: "center", marginTop: "12px" }}>
            <label style={{ fontSize: "0.9rem" }}>
              Evidence source:{" "}
              <select
                value={source}
                onChange={(e) => setSource(e.target.value)}
                style={{ padding: "6px", fontSize: "0.9rem" }}
              >
                <option value="local">Local corpus</option>
                <option value="wikipedia">Wikipedia (live)</option>
                <option value="web">Web (live)</option>
              </select>
            </label>

            <button
              onClick={analyze}
              disabled={loading}
              style={{
                padding: "0.6rem 1.4rem",
                fontSize: "1rem",
                background: loading ? "#999" : "#1a1a2e",
                color: "white",
                border: "none",
                borderRadius: "8px",
                cursor: loading ? "default" : "pointer",
              }}
            >
              {loading ? "Analyzing..." : "Analyze script"}
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div style={{ marginTop: "1rem", color: "#b42318" }}>⚠️ {error}</div>
          )}

          {/* Results */}
          {results && (
            <div style={{ marginTop: "1.5rem" }}>
              <h2 style={{ fontSize: "1.2rem" }}>
                Found {results.claim_count} claims · {results.flagged_count} flagged
              </h2>
              {results.results.length === 0 && (
                <p style={{ color: "#666" }}>
                  No factual claims detected. Try a script with concrete statements.
                </p>
              )}
              {results.results.map((r, i) => (
                <ResultCard key={i} result={r} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default App;