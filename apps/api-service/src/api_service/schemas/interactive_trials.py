from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PublicModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


class CreateInteractiveTrialRunRequest(BaseModel):
    case_file_id: UUID
    human_attorney_side: Literal["prosecution", "defense"] = "defense"
    human_witness_plan: list[str] = Field(
        min_length=1,
        validation_alias=AliasChoices("humanWitnessPlan", "human_witness_plan"),
    )


class PendingWitnessResponse(PublicModel):
    witness_id: str = Field(serialization_alias="witnessId")
    name: str
    persona: str
    called_by: str = Field(serialization_alias="calledBy")


class PendingHumanTurnContextResponse(PublicModel):
    action: Literal["opening", "closing", "question", "objection"]
    attorney_side: Literal["prosecution", "defense"] = Field(
        serialization_alias="attorneySide"
    )
    instruction: str
    examination_phase: Literal["direct", "cross"] | None = Field(
        default=None, serialization_alias="examinationPhase"
    )
    witness: PendingWitnessResponse | None = None


class PendingHumanTurnResponse(PublicModel):
    turn_id: UUID = Field(serialization_alias="turnId")
    scene: str
    attorney_side: str = Field(serialization_alias="attorneySide")
    context: PendingHumanTurnContextResponse


class InteractiveTrialRunResponse(PublicModel):
    interactive_trial_run_id: UUID = Field(serialization_alias="interactiveTrialRunId")
    case_file_id: UUID = Field(serialization_alias="caseFileId")
    human_attorney_side: str = Field(serialization_alias="humanAttorneySide")
    human_witness_plan: list[str] = Field(serialization_alias="humanWitnessPlan")
    status: str
    transcript: list[dict[str, object]] = Field(default_factory=list)
    live_transcript: list[dict[str, object]] = Field(
        default_factory=list, serialization_alias="liveTranscript"
    )
    result: dict[str, object] | None = None
    pending_human_turn: PendingHumanTurnResponse | None = Field(
        default=None, serialization_alias="pendingHumanTurn"
    )
    error_message: str | None = Field(default=None, serialization_alias="errorMessage")
    created_at: datetime = Field(serialization_alias="createdAt")
    completed_at: datetime | None = Field(
        default=None, serialization_alias="completedAt"
    )


class UploadAuthorizationRequest(BaseModel):
    content_type: str


class SubmitParticipantTurnRequest(BaseModel):
    object: bool
    is_final: bool | None = None


class UploadAuthorizationResponse(PublicModel):
    turn_id: UUID = Field(serialization_alias="turnId")
    upload_url: str = Field(serialization_alias="uploadUrl")
    required_headers: dict[str, str] = Field(serialization_alias="requiredHeaders")
    expires_in_seconds: int = Field(serialization_alias="expiresInSeconds")
    max_size_bytes: int = Field(serialization_alias="maxSizeBytes")


class SubmitParticipantTurnResponse(PublicModel):
    turn_id: UUID = Field(serialization_alias="turnId")
    status: str
