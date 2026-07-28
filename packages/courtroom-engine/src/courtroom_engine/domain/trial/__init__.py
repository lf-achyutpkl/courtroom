from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import Field

from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import Actor, CaseMetadata, Party
from courtroom_engine.domain.case_intelligence import CaseIntelligenceReport
from courtroom_engine.domain.evidence import EvidenceItem, Fact
from courtroom_engine.domain.events import CourtroomEvent
from courtroom_engine.domain.ids import ActorId, CaseId, EvidenceId, WitnessId
from courtroom_engine.domain.legal import ClaimOrCharge
from courtroom_engine.domain.procedure import ProcedureState, TrialPhase
from courtroom_engine.domain.simulation_truth import PrivateSimulationTruth
from courtroom_engine.domain.strategy import PartyStrategy
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
    procedure: ProcedureState = Field(default_factory=ProcedureState)
    admitted_evidence_ids: tuple[EvidenceId, ...] = ()
    public_event_summaries: tuple[str, ...] = ()
    events: tuple[CourtroomEvent, ...] = ()
    phase_outputs: dict[str, str] = Field(default_factory=dict)
    party_strategies: tuple[PartyStrategy, ...] = ()
    active_actor_id: ActorId | None = None
    current_witness_id: WitnessId | None = None

    def with_phase(self, phase: TrialPhase, summary: str | None = None) -> TrialRuntimeState:
        event_summaries = self.public_event_summaries
        if summary is not None:
            event_summaries = (*event_summaries, summary)
        return self.model_copy(
            update={
                "phase": phase.value,
                "procedure": self.procedure.model_copy(update={"phase": phase}),
                "public_event_summaries": event_summaries,
            }
        )
