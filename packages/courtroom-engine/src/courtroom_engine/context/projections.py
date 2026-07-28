from __future__ import annotations

from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import ActorRole, PartySide
from courtroom_engine.domain.case_intelligence import (
    CaseGapType,
    DisputeStatus,
    EvidenceRelationshipType,
    ProofStatus,
)
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


class MaterialFactContextDTO(DomainModel):
    fact_id: FactId
    element_id: ElementId
    supporting_side: PartySide
    opposing_side: PartySide
    dispute_status: DisputeStatus
    supporting_evidence_ids: tuple[EvidenceId, ...] = ()
    knowledgeable_witness_ids: tuple[WitnessId, ...] = ()
    proof_status: ProofStatus


class EvidenceRelationshipContextDTO(DomainModel):
    relationship_id: str
    relationship_type: EvidenceRelationshipType
    evidence_id: EvidenceId
    fact_id: FactId | None = None
    element_id: ElementId | None = None
    witness_id: WitnessId | None = None


class WitnessFactContextDTO(DomainModel):
    relationship_id: str
    witness_id: WitnessId
    fact_id: FactId


class CaseGapContextDTO(DomainModel):
    gap_id: str
    gap_type: CaseGapType
    description: str
    side: PartySide | None = None
    element_id: ElementId | None = None
    fact_ids: tuple[FactId, ...] = ()
    evidence_ids: tuple[EvidenceId, ...] = ()
    witness_ids: tuple[WitnessId, ...] = ()
    severity: float = Field(ge=0, le=1)


class PublicCaseIntelligenceContextDTO(DomainModel):
    material_facts: tuple[MaterialFactContextDTO, ...] = ()
    evidence_relationships: tuple[EvidenceRelationshipContextDTO, ...] = ()
    witness_fact_relationships: tuple[WitnessFactContextDTO, ...] = ()
    case_gaps: tuple[CaseGapContextDTO, ...] = ()


class ActorCaseViewDTO(DomainModel):
    facts: tuple[FactContextDTO, ...] = ()
    evidence: tuple[EvidenceContextDTO, ...] = ()
    witness_knowledge: tuple[WitnessKnowledgeContextDTO, ...] = ()
    intelligence: PublicCaseIntelligenceContextDTO = Field(
        default_factory=PublicCaseIntelligenceContextDTO
    )
    public_event_summaries: tuple[str, ...] = ()


class ModelNodeContextDTO(BaseNodeContext):
    actor: ActorContextDTO | None = None
    case_view: ActorCaseViewDTO
