"""
transcriber.py
---------------
Turns an audio or video FILE into text using faster-whisper.

faster-whisper extracts the speech and returns a transcript. That
transcript then feeds into the existing pipeline (analyze_script),
so a real video can be fact-checked end to end.

The model auto-uses the GPU if one is available (much faster),
otherwise runs on CPU. ffmpeg must be installed on the system.

PUBLIC FUNCTION:
  transcribe_file(path) -> str   (the full transcript text)
"""

from typing import Optional
from faster_whisper import WhisperModel

# Model size: "small" is a good speed/accuracy balance.
# On a GPU you can bump this to "medium" or "large-v3" for better
# transcripts. On CPU, "small" or "base" keep it reasonable.
_MODEL_SIZE = "small"

# Cache the model so it loads only once (loading is slow).
_model: Optional[WhisperModel] = None


def _get_model() -> WhisperModel:
    """Load the Whisper model once, choosing GPU if available."""
    global _model
    if _model is None:
        # Try to detect a GPU. If torch isn't present or no CUDA GPU,
        # fall back to CPU automatically.
        device = "cpu"
        compute_type = "int8"  # efficient on CPU
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                compute_type = "float16"  # faster on GPU
        except Exception:
            pass  # no torch / no GPU -> stay on CPU

        print(f"[whisper] loading '{_MODEL_SIZE}' model on {device}...")
        _model = WhisperModel(_MODEL_SIZE, device=device, compute_type=compute_type)
    return _model


def transcribe_file(path: str) -> str:
    """
    Transcribe an audio or video file into a single text string.

    Args:
        path: path to the audio/video file (mp3, m4a, wav, mp4, mov...).

    Returns:
        The full transcript as one string. Empty string if nothing
        could be transcribed.
    """
    model = _get_model()

    # transcribe() returns an iterator of segments + info.
    # beam_size controls quality vs speed; 5 is a sensible default.
    segments, info = model.transcribe(path, beam_size=5)

    # Stitch all segment texts into one transcript.
    pieces = [segment.text.strip() for segment in segments]
    transcript = " ".join(p for p in pieces if p)

    return transcript.strip()

def transcribe_uploaded(file_bytes: bytes, filename: str) -> str:
    """
    Transcribe an uploaded file given its raw bytes.

    Streamlit provides uploads as in-memory bytes, but Whisper needs
    a real file path. We write the bytes to a temporary file, transcribe
    it, then delete the temp file.

    Args:
        file_bytes: the raw bytes of the uploaded file.
        filename:   original name (used to keep the right extension).

    Returns:
        The transcript text.
    """
    import tempfile
    import os

    # Keep the original extension so ffmpeg knows the format.
    suffix = os.path.splitext(filename)[1] or ".tmp"

    # Write bytes to a temporary file.
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        transcript = transcribe_file(tmp_path)
    finally:
        # Always clean up the temp file, even if transcription errors.
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    return transcript