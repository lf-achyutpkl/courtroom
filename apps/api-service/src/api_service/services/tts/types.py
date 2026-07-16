from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SubtitleChunk:
    text: str
    startMs: int
    endMs: int

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PlaybackManifestTurn:
    turnId: int
    speakerId: str
    scene: str
    text: str
    cleanText: str
    emotion: str | None
    audioUrl: str
    durationMs: int
    subtitleChunks: list[SubtitleChunk]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["subtitleChunks"] = [chunk.to_dict() for chunk in self.subtitleChunks]
        return payload
