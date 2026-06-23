import { useState } from "react";
import ResultCard from "./ResultCard";

const API_URL = "http://localhost:8000";

const EXAMPLE_SCRIPT =
  "Okay listen up! Drinking lemon water every morning cures cancer, trust me. " +
  "The Eiffel Tower is 330 meters tall. Marie Curie won the Nobel Prize in " +
  "Literature. Studies show getting 7 to 9 hours of sleep is healthy.";

function App() {
  // State for the script text, the results, loading status, and errors.
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

  return (
    <div
      style={{
        fontFamily: "system-ui, sans-serif",
        maxWidth: "760px",
        margin: "0 auto",
        padding: "2rem 1.5rem",
        color: "#111",
      }}
    >
      <h1 style={{ marginBottom: "0.2rem" }}>🔎 Misinformation Detector</h1>
      <p style={{ color: "#666", marginTop: 0 }}>
        Paste a short-form video script. Each factual claim is checked against evidence.
      </p>

      {/* Script input */}
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
    </div>
  );
}

export default App;