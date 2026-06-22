"""
app/main.py
------------
Streamlit web UI for the Misinformation Detector.

Paste a script -> click Analyze -> see each claim with a color-coded
verdict, confidence, evidence, and explanation.

Run it with:   streamlit run app/main.py
"""

import sys
from pathlib import Path

# --- Make 'src' importable -------------------------------------------
# Streamlit runs this file directly, so Python doesn't automatically
# know where the project root is. We add the project root to the path
# so "from src...." imports work.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
from src.pipeline import analyze_script
from src.retrieval_service import warm_up
from src.schemas import Verdict


# --- Load models ONCE ------------------------------------------------
# @st.cache_resource tells Streamlit: run this function a single time,
# then reuse the result on every future click. Without it, the models
# would reload on every interaction (very slow).
@st.cache_resource
def _load_models():
    """Warm up the retriever/NLI models so the first analysis is fast."""
    warm_up()
    return True


# --- Visual helpers --------------------------------------------------
# Map each verdict to a color, emoji, and label for display.
_VERDICT_STYLE = {
    Verdict.supported: {
        "color": "#1a7f37",      # green
        "bg": "#e6f4ea",
        "emoji": "✅",
        "label": "SUPPORTED",
    },
    Verdict.contradicted: {
        "color": "#b42318",      # red
        "bg": "#fdecea",
        "emoji": "⚠️",
        "label": "CONTRADICTED",
    },
    Verdict.not_enough_evidence: {
        "color": "#6c737f",      # grey
        "bg": "#f2f4f7",
        "emoji": "❔",
        "label": "NOT ENOUGH EVIDENCE",
    },
}

# A default example script so users can try the app instantly.
_EXAMPLE_SCRIPT = (
    "Okay listen up! Drinking lemon water every morning cures cancer, trust me. "
    "The Eiffel Tower is 330 meters tall. Marie Curie won the Nobel Prize in "
    "Literature. Studies show getting 7 to 9 hours of sleep is healthy. "
    "Also, eating one carrot makes you completely invisible."
)


def _render_result(result):
    """Draw one claim result as a colored card."""
    style = _VERDICT_STYLE[result.verdict]

    # A colored box for the claim + verdict.
    st.markdown(
        f"""
        <div style="
            border-left: 6px solid {style['color']};
            background: {style['bg']};
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 6px;">
            <span style="font-size: 0.8em; color: {style['color']};
                  font-weight: 700;">
                {style['emoji']} {style['label']} · {result.confidence:.0%} confidence
                · {result.category.value}
            </span>
            <div style="font-size: 1.05em; margin-top: 4px; color: #111;">
                {result.claim}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Explanation + evidence tucked into an expander to keep it tidy.
    with st.expander("See explanation and evidence"):
        st.write(f"**Explanation:** {result.explanation}")
        st.write("**Evidence considered:**")
        for e in result.evidence:
            tag = e.support_type
            st.markdown(
                f"- *({tag}, relevance {e.score:.2f})* "
                f"**{e.source_title}** — {e.text}"
            )


# --- Page layout -----------------------------------------------------
def main():
    st.set_page_config(page_title="Misinformation Detector", page_icon="🔎")

    st.title(" Misinformation Detector")
    st.caption(
        "Paste a short-form video script. The system extracts factual claims "
        "and checks each one against an evidence corpus."
    )

    # Trigger the one-time model load (shows a spinner the first time).
    with st.spinner("Loading models (first time only)..."):
        _load_models()

    # Text box for the script, pre-filled with the example.
    script = st.text_area(
        "Video script",
        value=_EXAMPLE_SCRIPT,
        height=180,
    )

    # The analyze button.
    if st.button("Analyze script", type="primary"):
        if not script.strip():
            st.warning("Please paste a script first.")
            return

        with st.spinner("Analyzing claims..."):
            results = analyze_script(script)

        if not results:
            st.info(
                "No factual claims were detected in this script. "
                "Try one with concrete, checkable statements."
            )
            return

        # Small summary line.
        n_contra = sum(1 for r in results if r.verdict == Verdict.contradicted)
        st.subheader(f"Found {len(results)} claims · {n_contra} flagged")

        # Draw each result.
        for r in results:
            _render_result(r)


if __name__ == "__main__":
    main()