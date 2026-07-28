from __future__ import annotations

from courtroom_engine.domain.case import Actor, ActorRole
from courtroom_engine.domain.evidence import EvidenceItem, Fact
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState
from courtroom_engine.domain.visibility import VisibilityScope
from courtroom_engine.policies.access import (
    VISIBILITY_POLICY_VERSION,
    allowed_actions,
    allowed_scopes,
    excluded_categories,
    normalize_visibility,
)

from .projections import (
    CONTEXT_PROJECTION_VERSION,
    ActorCaseViewDTO,
    ActorContextDTO,
    ContextAuditRecord,
    ContextMetadata,
    ContextRequest,
    EvidenceContextDTO,
    FactContextDTO,
    ModelNodeContextDTO,
    NodePurpose,
    ProceduralContext,
    WitnessKnowledgeContextDTO,
)


class ContextBoundaryService:
    """Builds typed, role-safe model contexts from canonical case/state."""

    def build(
        self,
        *,
        case_package: CompiledCasePackage,
        state: TrialRuntimeState,
        request: ContextRequest,
    ) -> ModelNodeContextDTO:
        actor = self._find_actor(case_package, request.requesting_actor_id)
        if actor is None and request.node_purpose not in {
            NodePurpose.INITIAL_CASE_ANALYSIS,
            NodePurpose.ACTOR_EVALUATION,
            NodePurpose.COACHING,
        }:
            raise ValueError("actor context requires requesting_actor_id")

        allowed = allowed_scopes(actor, request.node_purpose)
        violation_messages: list[str] = []
        facts = self._project_facts(case_package.facts, allowed, violation_messages)
        evidence = self._project_evidence(
            case_package.evidence, allowed, violation_messages
        )
        witness_knowledge = self._project_witness_knowledge(
            case_package=case_package,
            actor=actor,
            request=request,
            allowed_scopes=allowed,
            violation_messages=violation_messages,
        )
        case_view = ActorCaseViewDTO(
            facts=facts,
            evidence=evidence,
            witness_knowledge=witness_knowledge,
            public_event_summaries=state.public_event_summaries[
                -request.recent_event_limit :
            ],
        )
        included_ids = self._included_ids(case_view)
        excluded = excluded_categories(
            actor,
            request.node_purpose,
            unknown_visibility=bool(violation_messages),
        )
        metadata = ContextMetadata(
            session_id=request.session_id,
            node_purpose=request.node_purpose,
            actor_id=request.requesting_actor_id,
            case_id=case_package.metadata.case_id,
            phase=state.phase,
            policy_version=VISIBILITY_POLICY_VERSION,
            included_object_ids=included_ids,
            excluded_categories=excluded,
        )
        draft_context = ModelNodeContextDTO(
            metadata=metadata,
            audit=ContextAuditRecord(
                session_id=request.session_id,
                node_purpose=request.node_purpose,
                actor_id=request.requesting_actor_id,
                case_id=case_package.metadata.case_id,
                included_object_ids=included_ids,
                excluded_categories=excluded,
                policy_version=VISIBILITY_POLICY_VERSION,
                projection_version=CONTEXT_PROJECTION_VERSION,
                estimated_context_size=0,
                violation_status=(
                    "violation_detected" if violation_messages else "clean"
                ),
                violation_messages=tuple(violation_messages),
            ),
            role_contract=self._role_contract(actor, request.node_purpose),
            task_instruction=self._task_instruction(request.node_purpose),
            procedure=ProceduralContext(
                current_phase=state.phase,
                active_actor_id=state.active_actor_id,
                current_witness_id=state.current_witness_id,
                allowed_action_types=allowed_actions(actor, request.node_purpose),
                prohibited_action_types=("access_hidden_truth", "invent_evidence"),
            ),
            actor=self._project_actor(actor),
            case_view=case_view,
        )
        estimated_size = len(
            draft_context.model_copy(
                update={
                    "audit": draft_context.audit.model_copy(
                        update={"estimated_context_size": 0}
                    )
                }
            ).model_dump_json()
        )
        context = draft_context.model_copy(
            update={
                "audit": draft_context.audit.model_copy(
                    update={"estimated_context_size": estimated_size}
                )
            }
        )
        self._validate_no_forbidden_context(context, actor, request.node_purpose)
        return context

    def _project_actor(self, actor: Actor | None) -> ActorContextDTO | None:
        if actor is None:
            return None
        return ActorContextDTO(
            actor_id=actor.actor_id,
            role=actor.role,
            name=actor.name,
            party_id=actor.party_id,
            witness_id=actor.witness_id,
        )

    def _project_facts(
        self,
        facts: tuple[Fact, ...],
        allowed: frozenset[VisibilityScope],
        violation_messages: list[str],
    ) -> tuple[FactContextDTO, ...]:
        projected: list[FactContextDTO] = []
        for fact in facts:
            visibility = normalize_visibility(fact.visibility)
            if visibility is None:
                violation_messages.append(
                    f"unknown fact visibility excluded: {fact.fact_id}"
                )
                continue
            if visibility not in allowed:
                continue
            projected.append(
                FactContextDTO(
                    fact_id=fact.fact_id,
                    text=fact.text,
                    supports_element_ids=fact.supports_element_ids,
                    disputed=fact.disputed,
                )
            )
        return tuple(projected)

    def _project_evidence(
        self,
        evidence_items: tuple[EvidenceItem, ...],
        allowed: frozenset[VisibilityScope],
        violation_messages: list[str],
    ) -> tuple[EvidenceContextDTO, ...]:
        projected: list[EvidenceContextDTO] = []
        for item in evidence_items:
            visibility = normalize_visibility(item.visibility)
            if visibility is None:
                violation_messages.append(
                    f"unknown evidence visibility excluded: {item.evidence_id}"
                )
                continue
            if visibility not in allowed:
                continue
            projected.append(
                EvidenceContextDTO(
                    evidence_id=item.evidence_id,
                    title=item.title,
                    description=item.description,
                    offered_by=item.offered_by,
                    supports_fact_ids=item.supports_fact_ids,
                    foundation_required=item.foundation_required,
                )
            )
        return tuple(projected)

    def _project_witness_knowledge(
        self,
        *,
        case_package: CompiledCasePackage,
        actor: Actor | None,
        request: ContextRequest,
        allowed_scopes: frozenset[VisibilityScope],
        violation_messages: list[str],
    ) -> tuple[WitnessKnowledgeContextDTO, ...]:
        if VisibilityScope.WITNESS_PRIVATE not in allowed_scopes:
            return ()
        witness_id = request.target_witness_id
        if actor is not None and actor.role == ActorRole.WITNESS:
            witness_id = actor.witness_id
        if witness_id is None:
            return ()

        projected: list[WitnessKnowledgeContextDTO] = []
        for atom in case_package.witness_knowledge:
            visibility = normalize_visibility(atom.visibility)
            if visibility is None:
                violation_messages.append(
                    "unknown witness knowledge visibility excluded: "
                    f"{atom.knowledge_atom_id}"
                )
                continue
            if atom.witness_id != witness_id or visibility not in allowed_scopes:
                continue
            projected.append(
                WitnessKnowledgeContextDTO(
                    knowledge_atom_id=atom.knowledge_atom_id,
                    witness_id=atom.witness_id,
                    text=atom.text,
                    related_fact_ids=atom.related_fact_ids,
                )
            )
        return tuple(projected)

    def _find_actor(
        self, case_package: CompiledCasePackage, actor_id: str | None
    ) -> Actor | None:
        if actor_id is None:
            return None
        return next(
            (actor for actor in case_package.actors if actor.actor_id == actor_id), None
        )

    def _role_contract(self, actor: Actor | None, node_purpose: NodePurpose) -> str:
        if node_purpose == NodePurpose.ACTOR_EVALUATION:
            return "Evaluate the run using complete audit context; cite observable records."
        if node_purpose == NodePurpose.COACHING:
            return "Produce coaching from grounded evaluator observations."
        if actor is None:
            return "Analyze public case structure only."
        return f"Act only within the authority of role: {actor.role.value}."

    def _task_instruction(self, node_purpose: NodePurpose) -> str:
        instructions = {
            NodePurpose.INITIAL_CASE_ANALYSIS: "Analyze case structure; do not draft courtroom dialogue.",
            NodePurpose.GLOBAL_STRATEGY: "Create strategic objectives; do not generate questions.",
            NodePurpose.WITNESS_SELECTION: "Select the next witness from available strategy objectives.",
            NodePurpose.TACTICAL_ACTION_PLANNING: "Choose one tactical action; do not phrase it as dialogue.",
            NodePurpose.QUESTION_GENERATION: "Generate one courtroom question from the selected action.",
            NodePurpose.OBJECTION_DECISION: "Decide whether a legally supported objection exists.",
            NodePurpose.OBJECTION_RULING: "Rule only on the pending objection or offer.",
            NodePurpose.WITNESS_ANSWER: "Answer as the witness using only supplied witness knowledge.",
            NodePurpose.ACTOR_EVALUATION: "Evaluate observable performance with citations.",
            NodePurpose.COACHING: "Convert grounded evaluation observations into coaching.",
        }
        return instructions[node_purpose]

    def _included_ids(self, case_view: ActorCaseViewDTO) -> tuple[str, ...]:
        ids: list[str] = []
        ids.extend(fact.fact_id for fact in case_view.facts)
        ids.extend(evidence.evidence_id for evidence in case_view.evidence)
        ids.extend(atom.knowledge_atom_id for atom in case_view.witness_knowledge)
        return tuple(ids)

    def _validate_no_forbidden_context(
        self,
        context: ModelNodeContextDTO,
        actor: Actor | None,
        node_purpose: NodePurpose,
    ) -> None:
        if node_purpose in {NodePurpose.ACTOR_EVALUATION, NodePurpose.COACHING}:
            return
        if actor is not None and actor.role == ActorRole.WITNESS:
            for atom in context.case_view.witness_knowledge:
                if atom.witness_id != actor.witness_id:
                    raise ValueError("witness context leaked another witness knowledge")
