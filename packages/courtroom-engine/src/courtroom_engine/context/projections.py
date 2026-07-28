from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import ActorRole, PartySide
from courtroom_engine.domain.ids import (
    ActorId,
    CaseId,
    ElementId,
    EvidenceId,
    FactId,
    KnowledgeAtomId,
    PartyId,
    WitnessId,
)

CONTEXT_PROJECTION_VERSION = "v2-alpha-projection-1"


class NodePurpose(StrEnum):
    INITIAL_CASE_ANALYSIS = "initial_case_analysis"
    GLOBAL_STRATEGY = "global_strategy"
    WITNESS_SELECTION = "witness_selection"
    TACTICAL_ACTION_PLANNING = "tactical_action_planning"
    QUESTION_GENERATION = "question_generation"
    OBJECTION_DECISION = "objection_decision"
    OBJECTION_RULING = "objection_ruling"
    WITNESS_ANSWER = "witness_answer"
    ACTOR_EVALUATION = "actor_evaluation"
    COACHING = "coaching"


class ContextRequest(DomainModel):
    session_id: UUID
    node_purpose: NodePurpose
    requesting_actor_id: ActorId | None = None
    target_witness_id: WitnessId | None = None
    recent_event_limit: int = Field(default=8, ge=0, le=50)


class ContextMetadata(DomainModel):
    session_id: UUID
    node_purpose: NodePurpose
    actor_id: ActorId | None
    case_id: CaseId
    phase: str
    projection_version: str = CONTEXT_PROJECTION_VERSION
    policy_version: str
    included_object_ids: tuple[str, ...] = ()
    excluded_categories: tuple[str, ...] = ()


class ContextAuditRecord(DomainModel):
    session_id: UUID
    node_purpose: NodePurpose
    actor_id: ActorId | None
    case_id: CaseId
    included_object_ids: tuple[str, ...] = ()
    excluded_categories: tuple[str, ...] = ()
    policy_version: str
    projection_version: str
    estimated_context_size: int = Field(ge=0)
    violation_status: Literal["clean", "violation_detected"] = "clean"
    violation_messages: tuple[str, ...] = ()


class ProceduralContext(DomainModel):
    current_phase: str
    active_actor_id: ActorId | None = None
    current_witness_id: WitnessId | None = None
    allowed_action_types: tuple[str, ...] = ()
    prohibited_action_types: tuple[str, ...] = ()


class BaseNodeContext(DomainModel):
    metadata: ContextMetadata
    audit: ContextAuditRecord
    role_contract: str
    task_instruction: str
    procedure: ProceduralContext


class ActorContextDTO(DomainModel):
    actor_id: ActorId
    role: ActorRole
    name: str
    party_id: PartyId | None = None
    witness_id: WitnessId | None = None


class FactContextDTO(DomainModel):
    fact_id: FactId
    text: str
    supports_element_ids: tuple[ElementId, ...] = ()
    disputed: bool = True


class EvidenceContextDTO(DomainModel):
    evidence_id: EvidenceId
    title: str
    description: str
    offered_by: PartySide
    supports_fact_ids: tuple[FactId, ...] = ()
    foundation_required: bool = True


class WitnessKnowledgeContextDTO(DomainModel):
    knowledge_atom_id: KnowledgeAtomId
    witness_id: WitnessId
    text: str
    related_fact_ids: tuple[FactId, ...] = ()


class ActorCaseViewDTO(DomainModel):
    facts: tuple[FactContextDTO, ...] = ()
    evidence: tuple[EvidenceContextDTO, ...] = ()
    witness_knowledge: tuple[WitnessKnowledgeContextDTO, ...] = ()
    public_event_summaries: tuple[str, ...] = ()


class ModelNodeContextDTO(BaseNodeContext):
    actor: ActorContextDTO | None = None
    case_view: ActorCaseViewDTO
