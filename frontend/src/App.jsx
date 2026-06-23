import { useState } from "react";

// The address of your FastAPI backend.
const API_URL = "http://localhost:8000";

function App() {
  // React "state" — like a variable the UI watches. When it changes,
  // the page re-renders. (Conceptually similar to Streamlit reruns.)
  const [status, setStatus] = useState("Not tested yet");
  const [result, setResult] = useState(null);

  // This function runs when the button is clicked.
  async function testApi() {
    setStatus("Calling API...");
    try {
      // fetch() sends an HTTP request — the JavaScript way to call your API.
      const response = await fetch(`${API_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: "The Eiffel Tower is 330 meters tall. Lemon water cures cancer.",
          source: "local",
          verifier: "nli",
        }),
      });

      if (!response.ok) {
        throw new Error(`API returned status ${response.status}`);
      }

      const data = await response.json();
      setStatus(`Success! Found ${data.claim_count} claims.`);
      setResult(data);
    } catch (err) {
      setStatus(`Error: ${err.message}. Is the API running?`);
      setResult(null);
    }
  }

  return (
    <div style={{ fontFamily: "sans-serif", padding: "2rem", maxWidth: "700px" }}>
      <h1>Misinformation Detector</h1>
      <p>React frontend — API connection test</p>

      <button onClick={testApi} style={{ padding: "0.6rem 1.2rem", fontSize: "1rem" }}>
        Test API
      </button>

      <p style={{ marginTop: "1rem" }}>
        <strong>Status:</strong> {status}
      </p>

      {/* If we got results, show them as raw JSON for now. */}
      {result && (
        <pre
          style={{
            background: "#f4f4f4",
            padding: "1rem",
            borderRadius: "6px",
            overflow: "auto",
            fontSize: "0.85rem",
          }}
        >
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}

export default App;