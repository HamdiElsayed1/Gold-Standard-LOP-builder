"""
Voice transcription — thin wrapper around OpenAI's whisper-1 endpoint.

Reuses the OpenAI client from `orchestrator` so the McKinsey AI gateway
(`OPENAI_BASE_URL`) and key from `.env` are picked up automatically.

Whisper-1 hard limits enforced here:
  * 25 MB max file size
  * Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from orchestrator import _get_client

_WHISPER_MAX_BYTES = 25 * 1024 * 1024  # 25 MB
_WHISPER_FORMATS = {"mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"}


def _ext(filename: str) -> str:
    return Path(filename).suffix.lower().lstrip(".")


def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    """
    Send `audio_bytes` to whisper-1 and return the plain transcript.

    Raises
    ------
    ValueError
        If the audio is empty, exceeds 25 MB, or has an unsupported extension.
    """
    if not audio_bytes:
        raise ValueError("Audio is empty — record or upload a memo first.")

    size = len(audio_bytes)
    if size > _WHISPER_MAX_BYTES:
        size_mb = size / (1024 * 1024)
        raise ValueError(
            f"Audio is {size_mb:.1f} MB. whisper-1 accepts up to 25 MB. "
            "Please record a shorter memo or compress the file."
        )

    ext = _ext(filename)
    if ext and ext not in _WHISPER_FORMATS:
        raise ValueError(
            f"Unsupported audio format '.{ext}'. "
            f"whisper-1 accepts: {', '.join(sorted(_WHISPER_FORMATS))}."
        )

    safe_name = filename if ext else f"{filename}.wav"
    buffer = BytesIO(audio_bytes)
    buffer.name = safe_name

    response = _get_client().audio.transcriptions.create(
        model="whisper-1",
        file=(safe_name, buffer),
        response_format="text",
    )

    if isinstance(response, str):
        return response.strip()
    return (getattr(response, "text", "") or "").strip()
