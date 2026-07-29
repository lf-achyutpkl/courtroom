from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import ActorRole, PartySide
from courtroom_engine.domain.evaluation import RecordCitation
from courtroom_engine.domain.ids import ActorId, ObjectiveId

COACHING_VERSION = "coaching-v1"


class CoachingSkill(StrEnum):
    LEGAL_GROUNDING = "legal_grounding"
    ISSUE_SPOTTING = "issue_spotting"
    THEORY_DEVELOPMENT = "theory_development"
    OBJECTIVE_SELECTION = "objective_selection"
    PROCEDURE = "procedure"
    ROLE_ADHERENCE = "role_adherence"
    EVIDENCE_USE = "evidence_use"
    FOUNDATION = "foundation"
    CONTRADICTION_HANDLING = "contradiction_handling"
    WITNESS_CONTROL = "witness_control"
    OBJECTION_HANDLING = "objection_handling"
    ADAPTATION = "adaptation"
    OPENING = "opening"
    CLOSING = "closing"
    JUDICIAL_REASONING = "judicial_reasoning"
    PROFESSIONAL_CONDUCT = "professional_conduct"


class CoachingMoment(DomainModel):
    moment_id: str
    observation_id: str
    actor_id: ActorId | None = None
    role: ActorRole | None = None
    side: PartySide | None = None
    transcript_location: str
    skill: CoachingSkill
    what_happened: str
    affected_objective_ids: tuple[ObjectiveId, ...] = ()
    available_information: tuple[RecordCitation, ...]
    why_it_mattered: str
    better_action: str
    example_wording: str
    expected_response: str
    recovery_option: str
    severity: str
    confidence: float = Field(ge=0, le=1)


class BetterActionSequence(DomainModel):
    sequence_id: str
    moment_id: str
    steps: tuple[str, ...]
    citations: tuple[RecordCitation, ...]


class SkillEvidence(DomainModel):
    evidence_id: str
    actor_id: ActorId | None
    role: ActorRole | None
    side: PartySide | None = None
    skill: CoachingSkill
    source_observation_id: str
    citations: tuple[RecordCitation, ...]
    direction: Literal["positive", "negative", "neutral"]
    strength: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    recency_weight: float = Field(default=1, ge=0, le=1)
    source_evaluator_version: str
    profile_scope: Literal["ai_actor", "human_learner"] = "ai_actor"


class SkillProfileUpdate(DomainModel):
    actor_id: ActorId | None
    role: ActorRole | None
    profile_scope: Literal["ai_actor", "human_learner"] = "ai_actor"
    appended_evidence: tuple[SkillEvidence, ...]


class CoachingReport(DomainModel):
    report_id: str
    source_evaluation_report_id: str
    moments: tuple[CoachingMoment, ...]
    better_action_sequences: tuple[BetterActionSequence, ...]
    improvement_plan: tuple[str, ...]
    skill_profile_updates: tuple[SkillProfileUpdate, ...]
    coaching_version: str = COACHING_VERSION
