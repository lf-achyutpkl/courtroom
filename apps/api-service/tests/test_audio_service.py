from __future__ import annotations

from typing import cast
from uuid import uuid4

from courtroom_domain import CaseFile

from api_service.services.storage.base import StoredObject
from api_service.services.tts.base import GeneratedSpeech
from api_service.services.tts.service import (
    SimulationAudioService,
    build_subtitle_chunks,
    parse_emotion_and_text,
)
from api_service.services.tts.voice_catalog import VoiceCatalog


class FakeTtsProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, float]] = []

    def synthesize(
        self,
        *,
        text: str,
        voice: str,
        speed: float,
    ) -> GeneratedSpeech:
        self.calls.append((text, voice, speed))
        return GeneratedSpeech(audio_bytes=b"wav-bytes", duration_ms=1800)


class FakeStorage:
    def __init__(self) -> None:
        self.keys: list[str] = []

    def upload_bytes(
        self,
        *,
        key: str,
        payload: bytes,
        content_type: str,
    ) -> StoredObject:
        self.keys.append(key)
        return StoredObject(
            bucket="courtroom-audio",
            key=key,
            url=f"https://cdn.example/{key}",
            content_type=content_type,
            size_bytes=len(payload),
        )


def build_case_file() -> CaseFile:
    return CaseFile.model_validate(
        {
            "case_id": str(uuid4()),
            "case_type": "criminal",
            "charge_or_claim": "Grand theft auto",
            "parties": {
                "plaintiff_or_prosecution": "People of California",
                "defendant": "Alex Rivera",
            },
            "ground_truth": "The defendant took a parked vehicle.",
            "evidence": [],
            "witnesses": [
                {
                    "witness_id": "W1",
                    "name": "Jordan Lee",
                    "persona": "Forensic accountant",
                    "called_by": "prosecution",
                    "knowledge_scope": "Ledger irregularities",
                }
            ],
        }
    )


def test_parse_emotion_and_text_removes_bracketed_tag() -> None:
    emotion, text = parse_emotion_and_text("[firm] The witness is ready.")

    assert emotion == "firm"
    assert text == "The witness is ready."


def test_build_subtitle_chunks_preserves_sentence_boundaries() -> None:
    chunks = build_subtitle_chunks("First sentence. Second sentence?", 2400)

    assert [chunk.text for chunk in chunks] == [
        "First sentence.",
        "Second sentence?",
    ]
    assert chunks[-1].endMs == 2400


def test_audio_service_builds_manifest_and_storage_metadata() -> None:
    provider = FakeTtsProvider()
    storage = FakeStorage()
    service = SimulationAudioService(
        provider=provider,
        storage=storage,
        voice_catalog=VoiceCatalog(),
    )

    manifest, audio_storage = service.generate_for_run(
        simulation_run_id=uuid4(),
        case_file=build_case_file(),
        simulation_result={
            "full_trial_transcript": [
                {
                    "scene": "direct",
                    "speaker_id": "W1",
                    "text": "[steady] I reviewed the ledger entries.",
                }
            ]
        },
    )

    assert len(manifest) == 1
    assert manifest[0]["cleanText"] == "I reviewed the ledger entries."
    stored_turns = cast(list[dict[str, object]], audio_storage["turns"])
    assert manifest[0]["audioUrl"] == stored_turns[0]["url"]
    assert storage.keys[0].endswith("/audio/1.wav")
    assert provider.calls[0][1] == "af_bella"


def test_audio_service_uses_existing_audio_script_timeline_when_available() -> None:
    provider = FakeTtsProvider()
    storage = FakeStorage()
    service = SimulationAudioService(
        provider=provider,
        storage=storage,
        voice_catalog=VoiceCatalog(),
    )

    manifest, _ = service.generate_for_run(
        simulation_run_id=uuid4(),
        case_file=build_case_file(),
        simulation_result={
            "audio_script_timeline": [
                {
                    "index": 7,
                    "scene": "ruling",
                    "speaker_id": "judge",
                    "text": "Objection sustained.",
                }
            ]
        },
    )

    assert manifest[0]["turnId"] == 7
    assert provider.calls[0][1] == "am_adam"
