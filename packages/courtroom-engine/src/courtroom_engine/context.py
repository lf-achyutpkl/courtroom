from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import Field

from .models import (
    Actor,
    ActorId,
    ActorRole,
    CompiledCasePackage,
    DomainModel,
    EvidenceItem,
    Fact,
    KnowledgeAtom,
    TrialRuntimeState,
    VisibilityScope,
    WitnessId,
)


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
    case_id: str
    phase: str
    projection_version: str = "v2-alpha"
    policy_version: str = "v2-alpha"
    included_object_ids: tuple[str, ...] = ()
    excluded_categories: tuple[str, ...] = ()


class ProceduralContext(DomainModel):
    current_phase: str
    active_actor_id: ActorId | None = None
    current_witness_id: WitnessId | None = None
    allowed_action_types: tuple[str, ...] = ()
    prohibited_action_types: tuple[str, ...] = ()


class BaseNodeContext(DomainModel):
    metadata: ContextMetadata
    role_contract: str
    task_instruction: str
    procedure: ProceduralContext


class ActorCaseView(DomainModel):
    facts: tuple[Fact, ...] = ()
    evidence: tuple[EvidenceItem, ...] = ()
    witness_knowledge: tuple[KnowledgeAtom, ...] = ()
    public_event_summaries: tuple[str, ...] = ()


class ModelNodeContext(BaseNodeContext):
    actor: Actor | None = None
    case_view: ActorCaseView


class ContextBoundaryService:
    """Builds typed, role-safe model contexts from canonical case/state."""

    def build(
        self,
        *,
        case_package: CompiledCasePackage,
        state: TrialRuntimeState,
        request: ContextRequest,
    ) -> ModelNodeContext:
        actor = self._find_actor(case_package, request.requesting_actor_id)
        if actor is None and request.node_purpose not in {
            NodePurpose.INITIAL_CASE_ANALYSIS,
            NodePurpose.ACTOR_EVALUATION,
            NodePurpose.COACHING,
        }:
            raise ValueError("actor context requires requesting_actor_id")

        allowed_scopes = self._allowed_scopes(actor, request.node_purpose)
        case_view = ActorCaseView(
            facts=tuple(
                fact for fact in case_package.facts if fact.visibility in allowed_scopes
            ),
            evidence=tuple(
                item
                for item in case_package.evidence
                if item.visibility in allowed_scopes
            ),
            witness_knowledge=self._witness_knowledge(
                case_package=case_package,
                actor=actor,
                request=request,
                allowed_scopes=allowed_scopes,
            ),
            public_event_summaries=state.public_event_summaries[
                -request.recent_event_limit :
            ],
        )
        context = ModelNodeContext(
            metadata=ContextMetadata(
                session_id=request.session_id,
                node_purpose=request.node_purpose,
                actor_id=request.requesting_actor_id,
                case_id=case_package.metadata.case_id,
                phase=state.phase,
                included_object_ids=self._included_ids(case_view),
                excluded_categories=self._excluded_categories(
                    actor, request.node_purpose
                ),
            ),
            role_contract=self._role_contract(actor, request.node_purpose),
            task_instruction=self._task_instruction(request.node_purpose),
            procedure=ProceduralContext(
                current_phase=state.phase,
                active_actor_id=state.active_actor_id,
                current_witness_id=state.current_witness_id,
                allowed_action_types=self._allowed_actions(actor, request.node_purpose),
                prohibited_action_types=("access_hidden_truth", "invent_evidence"),
            ),
            actor=actor,
            case_view=case_view,
        )
        self._validate_no_forbidden_context(context, actor, request.node_purpose)
        return context

    def _find_actor(
        self, case_package: CompiledCasePackage, actor_id: ActorId | None
    ) -> Actor | None:
        if actor_id is None:
            return None
        return next(
            (actor for actor in case_package.actors if actor.actor_id == actor_id), None
        )

    def _allowed_scopes(
        self, actor: Actor | None, node_purpose: NodePurpose
    ) -> set[VisibilityScope]:
        if node_purpose == NodePurpose.ACTOR_EVALUATION:
            return set(VisibilityScope)
        if node_purpose == NodePurpose.COACHING:
            return {
                VisibilityScope.PUBLIC_CASE,
                VisibilityScope.COACH_ONLY,
                VisibilityScope.EVALUATOR_ONLY,
            }
        if actor is None:
            return {VisibilityScope.PUBLIC_CASE}
        if actor.role in {ActorRole.PLAINTIFF_LAWYER, ActorRole.PROSECUTION_LAWYER}:
            return {
                VisibilityScope.PUBLIC_CASE,
                VisibilityScope.PLAINTIFF_PRIVATE,
                VisibilityScope.PROSECUTION_PRIVATE,
            }
        if actor.role == ActorRole.DEFENSE_LAWYER:
            return {VisibilityScope.PUBLIC_CASE, VisibilityScope.DEFENSE_PRIVATE}
        if actor.role == ActorRole.WITNESS:
            return {VisibilityScope.PUBLIC_CASE, VisibilityScope.WITNESS_PRIVATE}
        if actor.role in {ActorRole.TRIAL_JUDGE, ActorRole.JURY}:
            return {VisibilityScope.PUBLIC_CASE, VisibilityScope.JUDGE_ONLY}
        return {VisibilityScope.PUBLIC_CASE}

    def _witness_knowledge(
        self,
        *,
        case_package: CompiledCasePackage,
        actor: Actor | None,
        request: ContextRequest,
        allowed_scopes: set[VisibilityScope],
    ) -> tuple[KnowledgeAtom, ...]:
        if VisibilityScope.WITNESS_PRIVATE not in allowed_scopes:
            return ()
        witness_id = request.target_witness_id
        if actor is not None and actor.role == ActorRole.WITNESS:
            witness_id = actor.witness_id
        if witness_id is None:
            return ()
        return tuple(
            atom
            for atom in case_package.witness_knowledge
            if atom.witness_id == witness_id and atom.visibility in allowed_scopes
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

    def _allowed_actions(
        self, actor: Actor | None, node_purpose: NodePurpose
    ) -> tuple[str, ...]:
        if node_purpose == NodePurpose.WITNESS_ANSWER:
            return ("answer_pending_question",)
        if actor is None:
            return ()
        if actor.role in {
            ActorRole.PLAINTIFF_LAWYER,
            ActorRole.PROSECUTION_LAWYER,
            ActorRole.DEFENSE_LAWYER,
        }:
            return ("plan_strategy", "ask_question", "object", "argue")
        if actor.role == ActorRole.TRIAL_JUDGE:
            return ("rule_on_objection", "instruct_jury", "issue_verdict")
        return ()

    def _included_ids(self, case_view: ActorCaseView) -> tuple[str, ...]:
        ids: list[str] = []
        ids.extend(fact.fact_id for fact in case_view.facts)
        ids.extend(evidence.evidence_id for evidence in case_view.evidence)
        ids.extend(atom.knowledge_atom_id for atom in case_view.witness_knowledge)
        return tuple(ids)

    def _excluded_categories(
        self, actor: Actor | None, node_purpose: NodePurpose
    ) -> tuple[str, ...]:
        if node_purpose in {NodePurpose.ACTOR_EVALUATION, NodePurpose.COACHING}:
            return ()
        categories = ["synthetic_truth", "coaching_reference", "expected_verdict"]
        if actor is None or actor.role != ActorRole.WITNESS:
            categories.append("witness_private_knowledge_not_targeted")
        return tuple(categories)

    def _validate_no_forbidden_context(
        self,
        context: ModelNodeContext,
        actor: Actor | None,
        node_purpose: NodePurpose,
    ) -> None:
        if node_purpose in {NodePurpose.ACTOR_EVALUATION, NodePurpose.COACHING}:
            return
        forbidden = {VisibilityScope.EVALUATOR_ONLY, VisibilityScope.COACH_ONLY}
        for fact in context.case_view.facts:
            if fact.visibility in forbidden:
                raise ValueError(f"forbidden fact visibility leaked: {fact.fact_id}")
        for evidence in context.case_view.evidence:
            if evidence.visibility in forbidden:
                raise ValueError(
                    f"forbidden evidence visibility leaked: {evidence.evidence_id}"
                )
        if actor is not None and actor.role == ActorRole.WITNESS:
            for atom in context.case_view.witness_knowledge:
                if atom.witness_id != actor.witness_id:
                    raise ValueError("witness context leaked another witness knowledge")
