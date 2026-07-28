from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

CaseId = Annotated[str, Field(pattern=r"^CASE-[A-Z0-9-]+$")]
PartyId = Annotated[str, Field(pattern=r"^PTY-[A-Z0-9-]+$")]
ActorId = Annotated[str, Field(pattern=r"^ACT-[A-Z0-9-]+$")]
MatterId = Annotated[str, Field(pattern=r"^(CLM|CHG)-[A-Z0-9-]+$")]
ElementId = Annotated[str, Field(pattern=r"^ELM-[A-Z0-9-]+$")]
FactId = Annotated[str, Field(pattern=r"^FAC-[A-Z0-9-]+$")]
EvidenceId = Annotated[str, Field(pattern=r"^EVD-[A-Z0-9-]+$")]
WitnessId = Annotated[str, Field(pattern=r"^WIT-[A-Z0-9-]+$")]
KnowledgeAtomId = Annotated[str, Field(pattern=r"^KNO-[A-Z0-9-]+$")]
ContradictionId = Annotated[str, Field(pattern=r"^CON-[A-Z0-9-]+$")]
ObjectiveId = Annotated[str, Field(pattern=r"^OBJ-[A-Z0-9-]+$")]


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", validate_assignment=True)


class CaseKind(StrEnum):
    CIVIL = "civil"
    CRIMINAL = "criminal"


class PartySide(StrEnum):
    PLAINTIFF = "plaintiff"
    PROSECUTION = "prosecution"
    DEFENSE = "defense"


class ActorRole(StrEnum):
    PLAINTIFF_LAWYER = "plaintiff_lawyer"
    PROSECUTION_LAWYER = "prosecution_lawyer"
    DEFENSE_LAWYER = "defense_lawyer"
    WITNESS = "witness"
    TRIAL_JUDGE = "trial_judge"
    JURY = "jury"
    EVALUATOR = "evaluator"
    COACH = "coach"


class VisibilityScope(StrEnum):
    PUBLIC_CASE = "public_case"
    PLAINTIFF_PRIVATE = "plaintiff_private"
    PROSECUTION_PRIVATE = "prosecution_private"
    DEFENSE_PRIVATE = "defense_private"
    WITNESS_PRIVATE = "witness_private"
    JUDGE_ONLY = "judge_only"
    EVALUATOR_ONLY = "evaluator_only"
    COACH_ONLY = "coach_only"


class CaseMetadata(DomainModel):
    case_id: CaseId
    title: str
    case_kind: CaseKind
    jurisdiction: str = "US-CA"
    trial_type: Literal["jury", "bench"] = "jury"


class Party(DomainModel):
    party_id: PartyId
    name: str
    side: PartySide


class Actor(DomainModel):
    actor_id: ActorId
    role: ActorRole
    name: str
    party_id: PartyId | None = None
    witness_id: WitnessId | None = None


class LegalElement(DomainModel):
    element_id: ElementId
    label: str
    description: str
    burden: Literal["preponderance", "clear_and_convincing", "beyond_reasonable_doubt"]
    proving_side: PartySide


class ClaimOrCharge(DomainModel):
    matter_id: MatterId
    case_kind: CaseKind
    title: str
    elements: tuple[LegalElement, ...]

    @model_validator(mode="after")
    def validate_prefix(self) -> "ClaimOrCharge":
        if self.case_kind == CaseKind.CIVIL and not self.matter_id.startswith("CLM-"):
            raise ValueError("civil matters must use CLM-* ids")
        if self.case_kind == CaseKind.CRIMINAL and not self.matter_id.startswith(
            "CHG-"
        ):
            raise ValueError("criminal matters must use CHG-* ids")
        return self


class Fact(DomainModel):
    fact_id: FactId
    text: str
    visibility: VisibilityScope = VisibilityScope.PUBLIC_CASE
    supports_element_ids: tuple[ElementId, ...] = ()
    disputed: bool = True


class EvidenceItem(DomainModel):
    evidence_id: EvidenceId
    title: str
    description: str
    offered_by: PartySide
    visibility: VisibilityScope = VisibilityScope.PUBLIC_CASE
    supports_fact_ids: tuple[FactId, ...] = ()
    foundation_required: bool = True


class KnowledgeAtom(DomainModel):
    knowledge_atom_id: KnowledgeAtomId
    witness_id: WitnessId
    text: str
    related_fact_ids: tuple[FactId, ...] = ()
    visibility: VisibilityScope = VisibilityScope.WITNESS_PRIVATE


class Witness(DomainModel):
    witness_id: WitnessId
    name: str
    called_by: PartySide
    public_summary: str
    knowledge_atom_ids: tuple[KnowledgeAtomId, ...]


class ExpectedContradiction(DomainModel):
    contradiction_id: ContradictionId
    description: str
    involved_fact_ids: tuple[FactId, ...] = ()
    visibility: VisibilityScope = VisibilityScope.EVALUATOR_ONLY


class CoachingReference(DomainModel):
    objective_id: ObjectiveId
    label: str
    ideal_action: str
    visibility: VisibilityScope = VisibilityScope.COACH_ONLY


class PrivateSimulationTruth(DomainModel):
    ground_truth_summary: str
    expected_contradictions: tuple[ExpectedContradiction, ...] = ()
    coaching_references: tuple[CoachingReference, ...] = ()


class AuthoredCaseTemplate(DomainModel):
    metadata: CaseMetadata
    parties: tuple[Party, ...]
    actors: tuple[Actor, ...]
    matters: tuple[ClaimOrCharge, ...]
    facts: tuple[Fact, ...]
    evidence: tuple[EvidenceItem, ...]
    witnesses: tuple[Witness, ...]
    witness_knowledge: tuple[KnowledgeAtom, ...]
    private_truth: PrivateSimulationTruth | None = None


class DerivedCaseIntelligence(DomainModel):
    material_fact_ids: tuple[FactId, ...] = ()
    evidence_fact_edges: tuple[tuple[EvidenceId, FactId], ...] = ()
    witness_fact_edges: tuple[tuple[WitnessId, FactId], ...] = ()
    initial_contradiction_ids: tuple[ContradictionId, ...] = ()


class CompiledCasePackage(DomainModel):
    package_id: UUID = Field(default_factory=uuid4)
    compiled_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: CaseMetadata
    parties: tuple[Party, ...]
    actors: tuple[Actor, ...]
    matters: tuple[ClaimOrCharge, ...]
    facts: tuple[Fact, ...]
    evidence: tuple[EvidenceItem, ...]
    witnesses: tuple[Witness, ...]
    witness_knowledge: tuple[KnowledgeAtom, ...]
    intelligence: DerivedCaseIntelligence
    private_truth: PrivateSimulationTruth | None = None


class TrialRuntimeState(DomainModel):
    session_id: UUID = Field(default_factory=uuid4)
    case_id: CaseId
    phase: str = "initialization"
    admitted_evidence_ids: tuple[EvidenceId, ...] = ()
    public_event_summaries: tuple[str, ...] = ()
    active_actor_id: ActorId | None = None
    current_witness_id: WitnessId | None = None
