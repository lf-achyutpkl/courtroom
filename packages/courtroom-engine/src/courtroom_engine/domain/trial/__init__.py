from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import Actor, CaseMetadata, Party
from courtroom_engine.domain.case_intelligence import CaseIntelligenceReport
from courtroom_engine.domain.evidence import EvidenceItem, Fact
from courtroom_engine.domain.ids import ActorId, CaseId, EvidenceId, WitnessId
from courtroom_engine.domain.legal import ClaimOrCharge
from courtroom_engine.domain.simulation_truth import PrivateSimulationTruth
from courtroom_engine.domain.witnesses import KnowledgeAtom, Witness

DerivedCaseIntelligence = CaseIntelligenceReport


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
