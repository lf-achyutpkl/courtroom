from __future__ import annotations

from collections import Counter

from ..repositories.case_files import StoredCaseFile
from ..repositories.simulation_runs import StoredSimulationRun
from ..schemas.simulations import (
    PlaybackManifestTurnResponse,
    PlaybackSubtitleChunk,
    PlaybackTranscriptCaseMetadata,
    PlaybackTranscriptResponse,
    PlaybackTranscriptTurn,
    PlaybackVoiceCharacter,
    SimulationRunCaseFileSummary,
    SimulationRunCatalogItemResponse,
    SimulationRunPlaybackResponse,
    SimulationRunPlaybackSummary,
)


def build_simulation_catalog_item(
    run: StoredSimulationRun,
    case_file: StoredCaseFile,
) -> SimulationRunCatalogItemResponse:
    manifest = _validated_audio_manifest(run.audio_manifest)

    return SimulationRunCatalogItemResponse(
        simulation_run_id=run.id,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        case_file=SimulationRunCaseFileSummary(
            id=case_file.id,
            case_id=case_file.case_file.case_id,
            case_type=case_file.case_file.case_type,
            charge=case_file.case_file.charge_or_claim,
            jurisdiction_label=_build_jurisdiction_label(case_file),
            plaintiff_or_prosecution=case_file.case_file.parties.plaintiff_or_prosecution,
            defendant=case_file.case_file.parties.defendant,
            witness_count=len(case_file.case_file.witnesses),
            evidence_count=len(case_file.case_file.evidence),
        ),
        playback=SimulationRunPlaybackSummary(
            turn_count=len(manifest),
            duration_ms=sum(turn.duration_ms for turn in manifest),
            model_name=_extract_model_name(run.result),
            evaluation_score=None,
            verdict_label=_extract_verdict_label(run.result),
            dominant_scene=_extract_dominant_scene(manifest),
        ),
    )


def build_simulation_playback_response(
    run: StoredSimulationRun,
    case_file: StoredCaseFile,
) -> SimulationRunPlaybackResponse:
    manifest = _validated_audio_manifest(run.audio_manifest)
    transcript_turns = _build_transcript_turns(run.result)

    return SimulationRunPlaybackResponse(
        simulation_run_id=run.id,
        status=run.status,
        transcript=PlaybackTranscriptResponse(
            case_metadata=PlaybackTranscriptCaseMetadata(
                case_id=case_file.case_file.case_id,
                case_type=case_file.case_file.case_type,
                charge=case_file.case_file.charge_or_claim,
                defendant=case_file.case_file.parties.defendant,
                prosecution=case_file.case_file.parties.plaintiff_or_prosecution,
            ),
            voice_character_map=_build_voice_character_map(case_file),
            audio_script_timeline=transcript_turns,
        ),
        playback_manifest=manifest,
    )


def _build_voice_character_map(
    case_file: StoredCaseFile,
) -> dict[str, PlaybackVoiceCharacter]:
    characters: dict[str, PlaybackVoiceCharacter] = {
        "judge": PlaybackVoiceCharacter(role="Judge", suggested_tone="Measured"),
        "prosecution": PlaybackVoiceCharacter(
            role="Prosecution",
            name=case_file.case_file.parties.plaintiff_or_prosecution,
            suggested_tone="Firm",
        ),
        "defense": PlaybackVoiceCharacter(
            role="Defense",
            name=case_file.case_file.parties.defendant,
            suggested_tone="Measured",
        ),
    }

    for witness in case_file.case_file.witnesses:
        characters[witness.witness_id] = PlaybackVoiceCharacter(
            role=f"{witness.called_by.title()} Witness",
            name=witness.name,
            suggested_tone="Steady",
        )

    return characters


def _build_transcript_turns(
    result: dict[str, object] | None,
) -> list[PlaybackTranscriptTurn]:
    if result is None:
        raise ValueError("Simulation run does not contain a generated result.")

    raw_timeline = result.get("audio_script_timeline")
    if isinstance(raw_timeline, list):
        return [
            PlaybackTranscriptTurn(
                index=_read_turn_index(turn, fallback=index),
                scene=_read_required_str(turn, "scene"),
                speaker_id=_read_required_str(turn, "speaker_id"),
                text=_read_required_str(turn, "text"),
            )
            for index, turn in enumerate(raw_timeline, start=1)
        ]

    raw_transcript = result.get("full_trial_transcript")
    if isinstance(raw_transcript, list):
        return [
            PlaybackTranscriptTurn(
                index=index,
                scene=_read_required_str(turn, "scene"),
                speaker_id=_read_required_str(turn, "speaker_id"),
                text=_read_required_str(turn, "text"),
            )
            for index, turn in enumerate(raw_transcript, start=1)
        ]

    raise ValueError(
        "Simulation run result does not include audio_script_timeline or full_trial_transcript."
    )


def _validated_audio_manifest(
    manifest: list[dict[str, object]] | None,
) -> list[PlaybackManifestTurnResponse]:
    if not manifest:
        raise ValueError("Simulation run does not contain generated audio manifest data.")

    turns: list[PlaybackManifestTurnResponse] = []
    for entry in manifest:
        turns.append(
            PlaybackManifestTurnResponse(
                turn_id=_read_required_int(entry, "turnId"),
                speaker_id=_read_required_str(entry, "speakerId"),
                scene=_read_required_str(entry, "scene"),
                text=_read_required_str(entry, "text"),
                clean_text=_read_required_str(entry, "cleanText"),
                emotion=_read_optional_str(entry, "emotion"),
                audio_url=_read_required_str(entry, "audioUrl"),
                duration_ms=_read_required_int(entry, "durationMs"),
                subtitle_chunks=_build_subtitle_chunks(entry.get("subtitleChunks")),
            )
        )
    return turns


def _build_subtitle_chunks(value: object) -> list[PlaybackSubtitleChunk]:
    if not isinstance(value, list):
        raise ValueError("Simulation run audio manifest contains invalid subtitle chunks.")

    chunks: list[PlaybackSubtitleChunk] = []
    for chunk in value:
        if not isinstance(chunk, dict):
            raise ValueError("Simulation run audio manifest contains invalid subtitle chunks.")
        chunks.append(
            PlaybackSubtitleChunk(
                text=_read_required_str(chunk, "text"),
                start_ms=_read_required_int(chunk, "startMs"),
                end_ms=_read_required_int(chunk, "endMs"),
            )
        )
    return chunks


def _extract_verdict_label(result: dict[str, object] | None) -> str | None:
    if result is None:
        return None

    verdict = result.get("verdict")
    if not isinstance(verdict, dict):
        return None

    outcome = verdict.get("outcome")
    return outcome if isinstance(outcome, str) else None


def _extract_dominant_scene(
    manifest: list[PlaybackManifestTurnResponse],
) -> str | None:
    if not manifest:
        return None

    scene_counts = Counter(turn.scene for turn in manifest)
    return scene_counts.most_common(1)[0][0]


def _extract_model_name(result: dict[str, object] | None) -> str | None:
    if result is None:
        return None

    run = result.get("run")
    if not isinstance(run, dict):
        return None

    model_name = run.get("model_name")
    if not isinstance(model_name, str) or not model_name.strip():
        return None

    return model_name


def _build_jurisdiction_label(case_file: StoredCaseFile) -> str | None:
    jurisdiction = case_file.case_file.jurisdiction
    parts = [jurisdiction.state, jurisdiction.court]
    return ", ".join(part for part in parts if part)


def _read_required_str(payload: object, key: str) -> str:
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object payload while reading '{key}'.")

    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Simulation payload is missing a valid '{key}' field.")
    return value


def _read_optional_str(payload: object, key: str) -> str | None:
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object payload while reading '{key}'.")

    value = payload.get(key)
    return value if isinstance(value, str) else None


def _read_required_int(payload: object, key: str) -> int:
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object payload while reading '{key}'.")

    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"Simulation payload is missing a valid '{key}' field.")
    return value


def _read_turn_index(payload: object, *, fallback: int) -> int:
    if not isinstance(payload, dict):
        return fallback

    value = payload.get("index")
    return value if isinstance(value, int) else fallback
