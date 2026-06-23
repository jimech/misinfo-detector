// ResultCard.jsx
// Displays ONE claim's result as a color-coded card.
// React components are just functions that return UI (JSX).

// Map each verdict to its colors, emoji, and label.
const VERDICT_STYLES = {
  supported: {
    color: "#1a7f37",
    bg: "#e6f4ea",
    border: "#1a7f37",
    emoji: "✅",
    label: "SUPPORTED",
  },
  contradicted: {
    color: "#b42318",
    bg: "#fdecea",
    border: "#b42318",
    emoji: "⚠️",
    label: "CONTRADICTED",
  },
  not_enough_evidence: {
    color: "#6c737f",
    bg: "#f2f4f7",
    border: "#6c737f",
    emoji: "❔",
    label: "NOT ENOUGH EVIDENCE",
  },
};

// The component receives one "result" via props (like a function argument).
function ResultCard({ result }) {
  const style = VERDICT_STYLES[result.verdict] || VERDICT_STYLES.not_enough_evidence;
  const confidencePct = Math.round(result.confidence * 100);

  return (
    <div
      style={{
        borderLeft: `6px solid ${style.border}`,
        background: style.bg,
        padding: "14px 18px",
        borderRadius: "8px",
        marginBottom: "14px",
      }}
    >
      {/* Verdict label line */}
      <div style={{ fontSize: "0.8rem", color: style.color, fontWeight: 700 }}>
        {style.emoji} {style.label} · {confidencePct}% confidence · {result.category}
      </div>

      {/* The claim text */}
      <div style={{ fontSize: "1.05rem", marginTop: "4px", color: "#111" }}>
        {result.claim}
      </div>

      {/* Safer rewrite, only for flagged claims that have one */}
      {result.safer_rewrite && (
        <div
          style={{
            borderLeft: "4px solid #1a7f37",
            background: "#e6f4ea",
            padding: "8px 12px",
            borderRadius: "6px",
            marginTop: "10px",
          }}
        >
          <div style={{ fontSize: "0.75rem", color: "#1a7f37", fontWeight: 700 }}>
            ✏️ SUGGESTED SAFER VERSION
          </div>
          <div style={{ fontSize: "0.95rem", marginTop: "3px", color: "#111" }}>
            {result.safer_rewrite}
          </div>
        </div>
      )}

      {/* Explanation */}
      <div style={{ fontSize: "0.9rem", marginTop: "10px", color: "#333" }}>
        <strong>Why:</strong> {result.explanation}
      </div>

      {/* Evidence list (collapsible via the browser's native <details>) */}
      {result.evidence && result.evidence.length > 0 && (
        <details style={{ marginTop: "8px" }}>
          <summary style={{ cursor: "pointer", fontSize: "0.85rem", color: "#555" }}>
            See evidence ({result.evidence.length})
          </summary>
          <ul style={{ fontSize: "0.85rem", color: "#444", marginTop: "6px" }}>
            {result.evidence.map((e, i) => (
              <li key={i} style={{ marginBottom: "4px" }}>
                <em>
                  ({e.support_type}, relevance {e.score.toFixed(2)})
                </em>{" "}
                <strong>{e.source_title}</strong> — {e.text}
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export default ResultCard;