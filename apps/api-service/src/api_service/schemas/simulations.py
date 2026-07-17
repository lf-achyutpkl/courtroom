from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..repositories.simulation_runs import SimulationRunStatus


class StartSimulationRequest(BaseModel):
    case_file_id: UUID


class StartSimulationResponse(BaseModel):
    simulation_run_id: UUID
    case_file_id: UUID
    status: SimulationRunStatus


class FrontendSchemaModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class SimulationRunCaseFileSummary(FrontendSchemaModel):
    id: UUID
    case_id: str = Field(serialization_alias="caseId")
    case_type: str = Field(serialization_alias="caseType")
    charge: str
    jurisdiction_label: str | None = Field(
        default=None,
        serialization_alias="jurisdictionLabel",
    )
    plaintiff_or_prosecution: str = Field(serialization_alias="plaintiffOrProsecution")
    defendant: str
    witness_count: int = Field(serialization_alias="witnessCount")
    evidence_count: int = Field(serialization_alias="evidenceCount")


class SimulationRunPlaybackSummary(FrontendSchemaModel):
    turn_count: int = Field(serialization_alias="turnCount")
    duration_ms: int = Field(serialization_alias="durationMs")
    model_name: str | None = Field(
        default=None,
        serialization_alias="modelName",
    )
    evaluation_score: float | None = Field(
        default=None,
        serialization_alias="evaluationScore",
    )
    verdict_label: str | None = Field(
        default=None,
        serialization_alias="verdictLabel",
    )
    dominant_scene: str | None = Field(
        default=None,
        serialization_alias="dominantScene",
    )


class SimulationRunCatalogItemResponse(FrontendSchemaModel):
    simulation_run_id: UUID = Field(serialization_alias="simulationRunId")
    status: SimulationRunStatus
    created_at: datetime = Field(serialization_alias="createdAt")
    completed_at: datetime | None = Field(
        default=None,
        serialization_alias="completedAt",
    )
    case_file: SimulationRunCaseFileSummary = Field(serialization_alias="caseFile")
    playback: SimulationRunPlaybackSummary


class PlaybackTranscriptCaseMetadata(FrontendSchemaModel):
    case_id: str = Field(serialization_alias="case_id")
    case_type: str = Field(serialization_alias="case_type")
    charge: str
    defendant: str
    prosecution: str


class PlaybackVoiceCharacter(FrontendSchemaModel):
    role: str | None = None
    name: str | None = None
    gender: str | None = None
    suggested_tone: str | None = Field(
        default=None,
        serialization_alias="suggested_tone",
    )


class PlaybackTranscriptTurn(FrontendSchemaModel):
    index: int
    scene: str
    speaker_id: str = Field(serialization_alias="speaker_id")
    text: str


class PlaybackTranscriptResponse(FrontendSchemaModel):
    case_metadata: PlaybackTranscriptCaseMetadata = Field(
        serialization_alias="case_metadata"
    )
    voice_character_map: dict[str, PlaybackVoiceCharacter] = Field(
        serialization_alias="voice_character_map"
    )
    audio_script_timeline: list[PlaybackTranscriptTurn] = Field(
        serialization_alias="audio_script_timeline"
    )


class PlaybackSubtitleChunk(FrontendSchemaModel):
    text: str
    start_ms: int = Field(serialization_alias="startMs")
    end_ms: int = Field(serialization_alias="endMs")


class PlaybackManifestTurnResponse(FrontendSchemaModel):
    turn_id: int = Field(serialization_alias="turnId")
    speaker_id: str = Field(serialization_alias="speakerId")
    scene: str
    text: str
    clean_text: str = Field(serialization_alias="cleanText")
    emotion: str | None = None
    audio_url: str = Field(serialization_alias="audioUrl")
    duration_ms: int = Field(serialization_alias="durationMs")
    subtitle_chunks: list[PlaybackSubtitleChunk] = Field(
        serialization_alias="subtitleChunks"
    )


class SimulationRunPlaybackResponse(FrontendSchemaModel):
    simulation_run_id: UUID = Field(serialization_alias="simulationRunId")
    status: SimulationRunStatus
    transcript: PlaybackTranscriptResponse
    playback_manifest: list[PlaybackManifestTurnResponse] = Field(
        serialization_alias="playbackManifest"
    )
