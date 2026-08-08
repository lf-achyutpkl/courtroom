from __future__ import annotations

import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TranscriptionError(ValueError):
    """Raised when a human turn cannot be transcribed."""


def transcribe_deepgram(payload: dict[str, object]) -> str:
    """Transcribe a Studio base64 audio payload using Deepgram prerecorded STT."""
    encoded = payload.get("audio_base64")
    mime_type = payload.get("mime_type")
    if not isinstance(encoded, str) or not encoded.strip():
        raise TranscriptionError("audio_base64 is required for a human voice turn")
    if not isinstance(mime_type, str) or not mime_type.startswith("audio/"):
        raise TranscriptionError("mime_type must be an audio/* MIME type")
    try:
        audio = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise TranscriptionError("audio_base64 is not valid base64") from exc
    if not audio:
        raise TranscriptionError("audio payload is empty")
    api_key = os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise TranscriptionError("DEEPGRAM_API_KEY must be set for human voice turns")

    query = urlencode({"model": "nova-3", "language": "en-US", "smart_format": "true"})
    request = Request(
        f"https://api.deepgram.com/v1/listen?{query}",
        data=audio,
        headers={"Authorization": f"Token {api_key}", "Content-Type": mime_type},
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:  # nosec B310 - fixed provider URL
            body = json.loads(response.read())
    except (HTTPError, URLError, TimeoutError) as exc:
        raise TranscriptionError("Deepgram transcription request failed") from exc
    try:
        transcript = body["results"]["channels"][0]["alternatives"][0][
            "transcript"
        ].strip()
    except (KeyError, IndexError, TypeError, AttributeError) as exc:
        raise TranscriptionError("Deepgram returned no usable transcript") from exc
    if not transcript:
        raise TranscriptionError("Deepgram returned an empty transcript")
    return transcript
