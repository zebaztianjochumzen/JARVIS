"""Whisper-based speech-to-text using faster-whisper.

Lazily loads the model on first call. Model size is controlled by the
WHISPER_MODEL env var (default: base). Runs on CPU with int8 quantisation
so no GPU is required.
"""

import os
import tempfile

_model = None
_model_size: str = ""


def _get_model():
    global _model, _model_size
    size = os.environ.get("WHISPER_MODEL", "base")
    if _model is None or _model_size != size:
        from faster_whisper import WhisperModel
        _model = WhisperModel(size, device="cpu", compute_type="int8")
        _model_size = size
        print(f"[STT] faster-whisper '{size}' loaded on CPU (int8)", flush=True)
    return _model


def transcribe_bytes(audio_bytes: bytes, audio_format: str = "webm") -> str:
    """Transcribe raw audio bytes and return the spoken text.

    Supports any format ffmpeg understands (webm, mp4, ogg, wav, mp3).
    Returns an empty string if nothing was detected.
    """
    model = _get_model()

    ext = audio_format if audio_format.startswith(".") else f".{audio_format}"
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        segments, _info = model.transcribe(
            tmp_path,
            beam_size=5,
            language="en",
            condition_on_previous_text=False,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
        )
        return " ".join(seg.text.strip() for seg in segments).strip()
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def transcribe_file(path: str) -> str:
    """Transcribe an audio file at the given absolute path."""
    with open(path, "rb") as f:
        ext = os.path.splitext(path)[1] or ".wav"
        return transcribe_bytes(f.read(), audio_format=ext)
