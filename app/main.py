"""
app/main.py
------------
Streamlit web UI for the Misinformation Detector.

Paste a script -> pick an evidence source -> click Analyze -> see each
claim with a color-coded verdict, confidence, evidence, and explanation.

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
import requests
from src.retrieval_service import warm_up
from src.schemas import Verdict, ClaimResult
from src.transcriber import transcribe_uploaded


# The address where the FastAPI backend is running.
API_URL = "http://localhost:8000"


def call_analyze_api(text: str, source: str, verifier: str = "nli"):
    """
    Call the FastAPI /analyze endpoint over HTTP and return a list of
    ClaimResult objects rebuilt from the JSON response.

    This is what a frontend does: send a request, get JSON, display it.
    Raises a clear error if the API isn't reachable.
    """
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={"text": text, "source": source, "verifier": verifier},
            timeout=120,  # web/LLM modes can be slow
        )
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not reach the API. Make sure the backend is running:\n"
            "    uvicorn api.main:app --reload"
        )

    data = response.json()
    # Rebuild ClaimResult objects from the JSON so the rest of the
    # display code works unchanged.
    results = [ClaimResult(**item) for item in data["results"]]
    return results

# --- Load models ONCE ------------------------------------------------
# @st.cache_resource tells Streamlit: run this function a single time,
# then reuse the result on every future click. Without it, the models
# would reload on every interaction (very slow).
@st.cache_resource
def _load_models():
    """Warm up the local retriever/NLI models so the first analysis is fast."""
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
    # Show a safer rewrite prominently if the claim was flagged.
    if result.safer_rewrite:
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid #1a7f37;
                background: #e6f4ea;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 4px 0 8px 0;">
                <span style="font-size: 0.78em; color: #1a7f37; font-weight: 700;">
                    ✏️ SUGGESTED SAFER VERSION
                </span>
                <div style="font-size: 0.98em; margin-top: 3px; color: #111;">
                    {result.safer_rewrite}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Explanation + evidence tucked into an expander to keep it tidy.
    # Show a safer rewrite prominently if the claim was flagged.
    if result.safer_rewrite:
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid #1a7f37;
                background: #e6f4ea;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 4px 0 8px 0;">
                <span style="font-size: 0.78em; color: #1a7f37; font-weight: 700;">
                    ✏️ SUGGESTED SAFER VERSION
                </span>
                <div style="font-size: 0.98em; margin-top: 3px; color: #111;">
                    {result.safer_rewrite}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Explanation + evidence tucked into an expander to keep it tidy.
   # Show a safer rewrite prominently if the claim was flagged.
    if result.safer_rewrite:
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid #1a7f37;
                background: #e6f4ea;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 4px 0 8px 0;">
                <span style="font-size: 0.78em; color: #1a7f37; font-weight: 700;">
                    ✏️ SUGGESTED SAFER VERSION
                </span>
                <div style="font-size: 0.98em; margin-top: 3px; color: #111;">
                    {result.safer_rewrite}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Explanation + evidence tucked into an expander to keep it tidy.
    # Show a safer rewrite prominently if the claim was flagged.
    if result.safer_rewrite:
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid #1a7f37;
                background: #e6f4ea;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 4px 0 8px 0;">
                <span style="font-size: 0.78em; color: #1a7f37; font-weight: 700;">
                    ✏️ SUGGESTED SAFER VERSION
                </span>
                <div style="font-size: 0.98em; margin-top: 3px; color: #111;">
                    {result.safer_rewrite}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# Show a safer rewrite prominently if the claim was flagged.
    if result.safer_rewrite:
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid #1a7f37;
                background: #e6f4ea;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 4px 0 8px 0;">
                <span style="font-size: 0.78em; color: #1a7f37; font-weight: 700;">
                    ✏️ SUGGESTED SAFER VERSION
                </span>
                <div style="font-size: 0.98em; margin-top: 3px; color: #111;">
                    {result.safer_rewrite}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

  # Show a safer rewrite prominently if the claim was flagged.
    if result.safer_rewrite:
        st.markdown(
            f"""
            <div style="
                border-left: 4px solid #1a7f37;
                background: #e6f4ea;
                padding: 8px 14px;
                border-radius: 6px;
                margin: 4px 0 8px 0;">
                <span style="font-size: 0.78em; color: #1a7f37; font-weight: 700;">
                    ✏️ SUGGESTED SAFER VERSION
                </span>
                <div style="font-size: 0.98em; margin-top: 3px; color: #111;">
                    {result.safer_rewrite}
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

    st.title("🔎 Misinformation Detector")
    st.caption(
        "Paste a short-form video script. The system extracts factual claims "
        "and checks each one against an evidence source."
    )

    # Trigger the one-time local model load (shows a spinner the first time).
    with st.spinner("Loading models (first time only)..."):
        _load_models()

    # Let the user choose where evidence comes from.
    source_label = st.radio(
        "Evidence source",
        options=["Local corpus (fast, 12 curated facts)", 
                 "Wikipedia (live, broad)",
                 "Web (live, broadest, most current)",
        ],
        index=0,
        horizontal=True,
    )
    # Map the friendly label to the internal source string.
    if source_label.startswith("Wikipedia"):
        source = "wikipedia"
    elif source_label.startswith("Web"):
        source = "web"
    else:
        source = "local"

    # Text box for the script, pre-filled with the example.
    # Let the user choose how to provide the script.
    input_mode = st.radio(
        "Input method",
        options=["Paste a script", "Upload audio/video file"],
        index=0,
        horizontal=True,
    )

    script = ""  # will hold the text to analyze

    if input_mode == "Paste a script":
        script = st.text_area(
            "Video script",
            value=_EXAMPLE_SCRIPT,
            height=180,
        )
    else:
        # File uploader for audio/video.
        uploaded = st.file_uploader(
            "Upload an audio or video file",
            type=["mp3", "m4a", "wav", "mp4", "mov", "webm", "ogg"],
        )
        if uploaded is not None:
            st.caption(f"Uploaded: {uploaded.name}")
            # Transcribe button so it doesn't run on every rerun.
            if st.button("Transcribe file", type="secondary"):
                with st.spinner("Transcribing (this can take a bit on CPU)..."):
                    transcript = transcribe_uploaded(
                        uploaded.getvalue(), uploaded.name
                    )
                # Stash the transcript in session so it survives reruns.
                st.session_state["transcript"] = transcript

            # If we have a transcript, show it (editable) and use it.
            if "transcript" in st.session_state:
                script = st.text_area(
                    "Transcript (you can edit before analyzing)",
                    value=st.session_state["transcript"],
                    height=150,
                )

    # The analyze button.
    if st.button("Analyze script", type="primary"):
        if not script.strip():
            st.warning("Please paste a script first.")
            return

        if source == "wikipedia":
            spinner_msg = "Analyzing claims against Wikipedia (this can take a bit)..."
        elif source == "web":
            spinner_msg = "Searching the web for evidence (this can take a bit)..."
        else:
            spinner_msg = "Analyzing claims..."

        with st.spinner(spinner_msg):
            try:
                results = call_analyze_api(script, source=source)
            except RuntimeError as e:
                st.error(str(e))
                return

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