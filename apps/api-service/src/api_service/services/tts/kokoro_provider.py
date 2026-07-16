from __future__ import annotations

import io
import wave
from functools import cached_property

from .base import GeneratedSpeech, TtsProvider


SAMPLE_RATE_HZ = 24000


class KokoroTtsProvider(TtsProvider):
    @cached_property
    def _pipeline(self):
        try:
            from kokoro import KPipeline
        except ImportError as exc:
            raise RuntimeError(
                "Kokoro is not installed. Install the api-service TTS dependencies before running the audio worker."
            ) from exc

        return KPipeline(lang_code="a")

    def synthesize(
        self,
        *,
        text: str,
        voice: str,
        speed: float,
    ) -> GeneratedSpeech:
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError(
                "numpy is required for Kokoro audio generation."
            ) from exc

        audio_segments = []
        generator = self._pipeline(text, voice=voice, speed=speed)
        for _, _, audio in generator:
            audio_segments.append(audio)

        if not audio_segments:
            raise RuntimeError("Kokoro produced no audio for a transcript turn.")

        samples = np.concatenate(audio_segments)
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(SAMPLE_RATE_HZ)
            wav_file.writeframes((samples * 32767).astype(np.int16).tobytes())

        duration_ms = round((len(samples) / SAMPLE_RATE_HZ) * 1000)
        return GeneratedSpeech(audio_bytes=wav_buffer.getvalue(), duration_ms=duration_ms)
