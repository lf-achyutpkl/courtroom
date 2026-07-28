from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import PartySide
from courtroom_engine.domain.ids import (
    ContradictionId,
    ElementId,
    EvidenceId,
    FactId,
    MatterId,
    WitnessId,
)

ANALYZER_VERSION = "case-intelligence-v1"


class ReviewStatus(StrEnum):
    MACHINE_DERIVED = "machine_derived"
    NEEDS_REVIEW = "needs_review"
    REVIEWED = "reviewed"


class ProofStatus(StrEnum):
    SUPPORTED = "supported"
    CONTESTED = "contested"
    UNSUPPORTED = "unsupported"


class DisputeStatus(StrEnum):
    DISPUTED = "disputed"
    UNDISPUTED = "undisputed"


class CaseGraphNodeType(StrEnum):
    MATTER = "matter"
    CLAIM_OR_CHARGE = "claim_or_charge"
    DEFENSE = "defense"
    LEGAL_ELEMENT = "legal_element"
    PARTY = "party"
    FACT = "fact"
    EVIDENCE = "evidence"
    WITNESS = "witness"
    AUTHORITY = "authority"
    REMEDY = "remedy"
    VERDICT_OUTCOME = "verdict_outcome"


class CaseGraphEdgeType(StrEnum):
    ASSERTS = "asserts"
    HAS_ELEMENT = "has_element"
    SUPPORTS_ELEMENT = "supports_element"
    SUPPORTS_FACT = "supports_fact"
    KNOWS_FACT = "knows_fact"
    OFFERS_EVIDENCE = "offers_evidence"
    HAS_OUTCOME = "has_outcome"


class EvidenceRelationshipType(StrEnum):
    EVIDENCE_TO_FACT = "evidence_to_fact"
    EVIDENCE_TO_ELEMENT = "evidence_to_element"
    EVIDENCE_TO_WITNESS = "evidence_to_witness"
    FOUNDATION = "foundation"
    AUTHENTICITY = "authenticity"
    ADMISSIBILITY = "admissibility"
    IMPEACHMENT = "impeachment"
    CONTRADICTION = "contradiction"


class ContradictionType(StrEnum):
    WITNESS_VS_WITNESS = "witness_vs_witness"
    WITNESS_VS_DOCUMENT = "witness_vs_document"
    WITNESS_VS_PRIOR_STATEMENT = "witness_vs_prior_statement"
    FACT_VS_TIMELINE = "fact_vs_timeline"
    CLAIM_VS_EVIDENCE = "claim_vs_evidence"
    INTERNAL_TESTIMONY = "internal_testimony"
    THEORY_INCONSISTENCY = "theory_inconsistency"


class CaseGapType(StrEnum):
    MISSING_BURDEN_PROOF = "missing_burden_proof"
    MISSING_FOUNDATION = "missing_foundation"
    UNSUPPORTED_MATERIAL_FACT = "unsupported_material_fact"
    UNRESOLVED_LEGAL_ISSUE = "unresolved_legal_issue"
    ONE_WITNESS_DEPENDENCY = "one_witness_dependency"
    WEAK_CORROBORATION = "weak_corroboration"
    TEMPORAL_GAP = "temporal_gap"
    CONTRADICTION_OPPORTUNITY = "contradiction_opportunity"


class TimelineRelationshipType(StrEnum):
    BEFORE = "before"
    AFTER = "after"
    SAME_TIME = "same_time"
    UNKNOWN_ORDER = "unknown_order"


class DerivedIntelligenceObject(DomainModel):
    source_ids: tuple[str, ...]
    derivation_method: str
    analyzer_version: str = ANALYZER_VERSION
    confidence_score: float = Field(ge=0, le=1)
    review_status: ReviewStatus = ReviewStatus.MACHINE_DERIVED


class AnalyzerDiagnostic(DomainModel):
    code: str
    message: str
    source_ids: tuple[str, ...] = ()
    severity: Literal["info", "warning", "error"] = "warning"


class CaseGraphNode(DerivedIntelligenceObject):
    node_id: str
    node_type: CaseGraphNodeType
    label: str


class CaseGraphEdge(DerivedIntelligenceObject):
    edge_id: str
    edge_type: CaseGraphEdgeType
    source_node_id: str
    target_node_id: str


class CaseGraph(DomainModel):
    nodes: tuple[CaseGraphNode, ...] = ()
    edges: tuple[CaseGraphEdge, ...] = ()


class EvidenceRelationship(DerivedIntelligenceObject):
    relationship_id: str
    relationship_type: EvidenceRelationshipType
    evidence_id: EvidenceId
    fact_id: FactId | None = None
    element_id: ElementId | None = None
    witness_id: WitnessId | None = None
    contradiction_id: ContradictionId | None = None
    description: str = ""


class EvidenceGraph(DomainModel):
    relationships: tuple[EvidenceRelationship, ...] = ()


class TimelineEvent(DerivedIntelligenceObject):
    event_id: str
    label: str
    source_fact_ids: tuple[FactId, ...] = ()
    approximate_date: str | None = None


class TimelineConstraint(DerivedIntelligenceObject):
    constraint_id: str
    relationship_type: TimelineRelationshipType
    source_event_id: str
    target_event_id: str


class TimelineGraph(DomainModel):
    events: tuple[TimelineEvent, ...] = ()
    sequence_constraints: tuple[TimelineConstraint, ...] = ()
    temporal_gap_ids: tuple[str, ...] = ()
    temporal_conflict_ids: tuple[str, ...] = ()


class ContradictionRecord(DerivedIntelligenceObject):
    contradiction_id: ContradictionId
    contradiction_type: ContradictionType
    description: str
    fact_ids: tuple[FactId, ...] = ()
    evidence_ids: tuple[EvidenceId, ...] = ()
    witness_ids: tuple[WitnessId, ...] = ()


class ContradictionGraph(DomainModel):
    contradictions: tuple[ContradictionRecord, ...] = ()


class MaterialFactRecord(DerivedIntelligenceObject):
    fact_id: FactId
    matter_id: MatterId
    element_id: ElementId
    supporting_side: PartySide
    opposing_side: PartySide
    dispute_status: DisputeStatus
    supporting_evidence_ids: tuple[EvidenceId, ...] = ()
    contradicting_evidence_ids: tuple[EvidenceId, ...] = ()
    knowledgeable_witness_ids: tuple[WitnessId, ...] = ()
    proof_status: ProofStatus


class MaterialFactMap(DomainModel):
    facts: tuple[MaterialFactRecord, ...] = ()


class WitnessKnowledgeRelationship(DerivedIntelligenceObject):
    relationship_id: str
    witness_id: WitnessId
    fact_id: FactId
    knowledge_atom_ids: tuple[str, ...]


class WitnessKnowledgeGraph(DomainModel):
    relationships: tuple[WitnessKnowledgeRelationship, ...] = ()


class CaseGap(DerivedIntelligenceObject):
    gap_id: str
    gap_type: CaseGapType
    description: str
    side: PartySide | None = None
    matter_id: MatterId | None = None
    element_id: ElementId | None = None
    fact_ids: tuple[FactId, ...] = ()
    evidence_ids: tuple[EvidenceId, ...] = ()
    witness_ids: tuple[WitnessId, ...] = ()
    severity: float = Field(ge=0, le=1)


class CaseIntelligenceReport(DomainModel):
    analyzer_version: str = ANALYZER_VERSION
    case_graph: CaseGraph
    evidence_graph: EvidenceGraph
    timeline_graph: TimelineGraph
    contradiction_graph: ContradictionGraph
    material_fact_map: MaterialFactMap
    witness_knowledge_graph: WitnessKnowledgeGraph
    case_gaps: tuple[CaseGap, ...] = ()
    diagnostics: tuple[AnalyzerDiagnostic, ...] = ()


DerivedCaseIntelligence = CaseIntelligenceReport
