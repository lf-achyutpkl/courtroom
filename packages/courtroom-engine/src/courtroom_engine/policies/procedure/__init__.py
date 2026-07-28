from __future__ import annotations

from courtroom_engine.context.projections import NodePurpose
from courtroom_engine.domain.case import Actor, ActorRole
from courtroom_engine.domain.procedure import (
    ActionType,
    ProcedureState,
    ProcedureValidationResult,
    TrialPhase,
)

PROCEDURE_POLICY_VERSION = "v2-alpha-procedure-1"


LAWYER_ROLES = {
    ActorRole.PLAINTIFF_LAWYER,
    ActorRole.PROSECUTION_LAWYER,
    ActorRole.DEFENSE_LAWYER,
}


def allowed_action_types(
    actor: Actor | None,
    node_purpose: NodePurpose,
    procedure: ProcedureState | None = None,
) -> tuple[ActionType, ...]:
    if node_purpose == NodePurpose.INITIAL_CASE_ANALYSIS:
        return ()
    if node_purpose == NodePurpose.ACTOR_EVALUATION:
        return (ActionType.EVALUATE,)
    if node_purpose == NodePurpose.COACHING:
        return (ActionType.COACH,)
    if actor is None:
        return ()
    phase = procedure.phase if procedure is not None else None
    if actor.role in LAWYER_ROLES:
        return _lawyer_actions(node_purpose, phase)
    if actor.role == ActorRole.WITNESS:
        return (
            (ActionType.ANSWER_PENDING_QUESTION,)
            if node_purpose == NodePurpose.WITNESS_ANSWER
            else ()
        )
    if actor.role == ActorRole.TRIAL_JUDGE:
        if node_purpose == NodePurpose.OBJECTION_RULING:
            return (ActionType.RULE_ON_OBJECTION, ActionType.ADMIT_EVIDENCE)
        if phase == TrialPhase.DELIBERATION:
            return (ActionType.DELIBERATE,)
        return (ActionType.INSTRUCT_JURY,)
    if actor.role == ActorRole.JURY:
        return (ActionType.DELIBERATE,) if phase == TrialPhase.DELIBERATION else ()
    return ()


def allowed_actions(
    actor: Actor | None,
    node_purpose: NodePurpose,
    procedure: ProcedureState | None = None,
) -> tuple[str, ...]:
    return tuple(
        action.value for action in allowed_action_types(actor, node_purpose, procedure)
    )


def validate_action_allowed(
    *,
    actor: Actor | None,
    node_purpose: NodePurpose,
    action_type: ActionType,
    procedure: ProcedureState,
) -> ProcedureValidationResult:
    allowed = allowed_action_types(actor, node_purpose, procedure)
    if action_type in allowed:
        return ProcedureValidationResult(valid=True, action_type=action_type)
    role = actor.role.value if actor is not None else "none"
    return ProcedureValidationResult(
        valid=False,
        action_type=action_type,
        reason=(
            f"{action_type.value} is not allowed for role {role}, "
            f"purpose {node_purpose.value}, phase {procedure.phase.value}"
        ),
    )


def _lawyer_actions(
    node_purpose: NodePurpose,
    phase: TrialPhase | None,
) -> tuple[ActionType, ...]:
    if node_purpose == NodePurpose.GLOBAL_STRATEGY:
        return (ActionType.PLAN_STRATEGY,)
    if node_purpose == NodePurpose.WITNESS_SELECTION:
        return (ActionType.SELECT_WITNESS,)
    if node_purpose == NodePurpose.EXAMINATION_OBJECTIVE:
        return (ActionType.PLAN_EXAMINATION_OBJECTIVE,)
    if node_purpose == NodePurpose.TACTICAL_ACTION_PLANNING:
        return (ActionType.PLAN_TACTICAL_ACTION,)
    if node_purpose == NodePurpose.QUESTION_GENERATION:
        return (ActionType.ASK_QUESTION,)
    if node_purpose == NodePurpose.OBJECTION_DECISION:
        return (ActionType.OBJECT,)
    if phase in {TrialPhase.OPENING, TrialPhase.CLOSING}:
        return (ActionType.ARGUE,)
    return ()
