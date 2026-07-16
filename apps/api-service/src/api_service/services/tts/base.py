from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GeneratedSpeech:
    audio_bytes: bytes
    duration_ms: int
    content_type: str = "audio/wav"


class TtsProvider(Protocol):
    def synthesize(
        self,
        *,
        text: str,
        voice: str,
        speed: float,
    ) -> GeneratedSpeech:
        """Convert a text turn into a single audio asset."""
        ...
