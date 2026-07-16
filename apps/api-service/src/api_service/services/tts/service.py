from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from courtroom_domain import CaseFile

from ...core.config import (
    get_r2_access_key_id,
    get_r2_bucket_name,
    get_r2_endpoint_url,
    get_r2_public_base_url,
    get_r2_region,
    get_r2_secret_access_key,
    get_tts_provider_name,
)
from ..storage import ObjectStorageService, R2ObjectStorageService
from ..storage.base import StoredObject
from .base import TtsProvider
from .kokoro_provider import KokoroTtsProvider
from .types import PlaybackManifestTurn, SubtitleChunk
from .voice_catalog import VoiceCatalog


@dataclass(frozen=True)
class ScriptTurn:
    turn_id: int
    speaker_id: str
    scene: str
    text: str


class SimulationAudioService:
    def __init__(
        self,
        *,
        provider: TtsProvider,
        storage: ObjectStorageService,
        voice_catalog: VoiceCatalog,
    ) -> None:
        self.provider = provider
        self.storage = storage
        self.voice_catalog = voice_catalog

    def generate_for_run(
        self,
        *,
        simulation_run_id: UUID,
        case_file: CaseFile,
        simulation_result: dict[str, object],
    ) -> tuple[list[dict[str, object]], dict[str, object]]:
        script_turns = _extract_script_turns(simulation_result)
        manifest: list[dict[str, object]] = []
        storage_turns: list[dict[str, object]] = []

        for turn in script_turns:
            emotion, clean_text = parse_emotion_and_text(turn.text)
            preset = self.voice_catalog.resolve(
                speaker_id=turn.speaker_id,
                case_file=case_file,
            )
            speech = self.provider.synthesize(
                text=clean_text,
                voice=preset.voice,
                speed=preset.speed,
            )
            stored_object = self.storage.upload_bytes(
                key=_build_audio_object_key(simulation_run_id, turn.turn_id),
                payload=speech.audio_bytes,
                content_type=speech.content_type,
            )
            manifest_turn = PlaybackManifestTurn(
                turnId=turn.turn_id,
                speakerId=turn.speaker_id,
                scene=turn.scene,
                text=turn.text,
                cleanText=clean_text,
                emotion=emotion,
                audioUrl=stored_object.url,
                durationMs=speech.duration_ms,
                subtitleChunks=build_subtitle_chunks(clean_text, speech.duration_ms),
            )
            manifest.append(manifest_turn.to_dict())
            storage_turns.append(
                _storage_turn_dict(
                    turn=turn,
                    stored_object=stored_object,
                    preset_style=preset.style_preset,
                    preset_voice=preset.voice,
                )
            )

        return manifest, {
            "provider": "r2",
            "turns": storage_turns,
        }


def create_simulation_audio_service() -> SimulationAudioService:
    provider_name = get_tts_provider_name().lower()
    if provider_name != "kokoro":
        raise RuntimeError(f"Unsupported TTS provider: {provider_name}")

    return SimulationAudioService(
        provider=KokoroTtsProvider(),
        storage=R2ObjectStorageService(
            bucket_name=get_r2_bucket_name(),
            endpoint_url=get_r2_endpoint_url(),
            access_key_id=get_r2_access_key_id(),
            secret_access_key=get_r2_secret_access_key(),
            public_base_url=get_r2_public_base_url(),
            region_name=get_r2_region(),
        ),
        voice_catalog=VoiceCatalog(),
    )


def parse_emotion_and_text(text: str) -> tuple[str | None, str]:
    emotion = None
    cleaned = []
    token = ""
    in_brackets = False

    for char in text:
        if char == "[":
            in_brackets = True
            token = ""
            continue
        if char == "]" and in_brackets:
            in_brackets = False
            emotion = (token or "").strip().lower() or emotion
            token = ""
            continue
        if in_brackets:
            token += char
        else:
            cleaned.append(char)

    clean_text = " ".join("".join(cleaned).split())
    return emotion, clean_text


def build_subtitle_chunks(text: str, duration_ms: int) -> list[SubtitleChunk]:
    chunks = split_sentences(text)
    total_chars = sum(len(chunk) for chunk in chunks) or 1
    cursor = 0
    subtitle_chunks: list[SubtitleChunk] = []

    for index, chunk in enumerate(chunks):
        chunk_duration = (
            duration_ms - cursor
            if index == len(chunks) - 1
            else max(900, round((len(chunk) / total_chars) * duration_ms))
        )
        start_ms = cursor
        end_ms = min(duration_ms, start_ms + chunk_duration)
        cursor = end_ms
        subtitle_chunks.append(
            SubtitleChunk(
                text=chunk,
                startMs=start_ms,
                endMs=end_ms,
            )
        )

    return subtitle_chunks


def split_sentences(text: str) -> list[str]:
    chunks = []
    current = []
    for char in text:
        current.append(char)
        if char in ".!?":
            chunk = "".join(current).strip()
            if chunk:
                chunks.append(chunk)
            current = []

    if current:
        chunk = "".join(current).strip()
        if chunk:
            chunks.append(chunk)

    return chunks or [text]


def _build_audio_object_key(simulation_run_id: UUID, turn_id: int) -> str:
    return f"simulation-runs/{simulation_run_id}/audio/{turn_id}.wav"


def _extract_script_turns(simulation_result: dict[str, object]) -> list[ScriptTurn]:
    raw_timeline = simulation_result.get("audio_script_timeline")
    if isinstance(raw_timeline, list) and raw_timeline:
        return [_script_turn_from_timeline_entry(entry) for entry in raw_timeline]

    raw_transcript = simulation_result.get("full_trial_transcript")
    if isinstance(raw_transcript, list) and raw_transcript:
        return [
            _script_turn_from_transcript_entry(index=index, entry=entry)
            for index, entry in enumerate(raw_transcript, start=1)
        ]

    raise RuntimeError(
        "Simulation result does not contain audio_script_timeline or full_trial_transcript."
    )


def _script_turn_from_timeline_entry(entry: object) -> ScriptTurn:
    if not isinstance(entry, dict):
        raise RuntimeError("audio_script_timeline contains an invalid turn payload.")

    return ScriptTurn(
        turn_id=int(entry["index"]),
        speaker_id=str(entry["speaker_id"]),
        scene=str(entry["scene"]),
        text=str(entry["text"]),
    )


def _script_turn_from_transcript_entry(*, index: int, entry: object) -> ScriptTurn:
    if not isinstance(entry, dict):
        raise RuntimeError("full_trial_transcript contains an invalid turn payload.")

    return ScriptTurn(
        turn_id=index,
        speaker_id=str(entry["speaker_id"]),
        scene=str(entry["scene"]),
        text=str(entry["text"]),
    )


def _storage_turn_dict(
    *,
    turn: ScriptTurn,
    stored_object: StoredObject,
    preset_style: str,
    preset_voice: str,
) -> dict[str, object]:
    return {
        "turnId": turn.turn_id,
        "speakerId": turn.speaker_id,
        "bucket": stored_object.bucket,
        "key": stored_object.key,
        "url": stored_object.url,
        "contentType": stored_object.content_type,
        "sizeBytes": stored_object.size_bytes,
        "voice": preset_voice,
        "stylePreset": preset_style,
    }
