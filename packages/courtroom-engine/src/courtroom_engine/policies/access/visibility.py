from __future__ import annotations

from courtroom_engine.context.projections import NodePurpose
from courtroom_engine.domain.base import DomainModel
from courtroom_engine.domain.case import Actor, ActorRole
from courtroom_engine.domain.visibility import VisibilityScope

VISIBILITY_POLICY_VERSION = "v2-alpha-access-1"


class AccessPolicyDecision(DomainModel):
    allowed_scopes: frozenset[VisibilityScope]
    excluded_categories: tuple[str, ...]


def normalize_visibility(value: VisibilityScope | str) -> VisibilityScope | None:
    if isinstance(value, VisibilityScope):
        return value
    try:
        return VisibilityScope(value)
    except ValueError:
        return None


def allowed_scopes(
    actor: Actor | None, node_purpose: NodePurpose
) -> frozenset[VisibilityScope]:
    if node_purpose == NodePurpose.ACTOR_EVALUATION:
        return frozenset(VisibilityScope)
    if node_purpose == NodePurpose.COACHING:
        return frozenset(
            {
                VisibilityScope.PUBLIC_CASE,
                VisibilityScope.COACH_ONLY,
                VisibilityScope.EVALUATOR_ONLY,
            }
        )
    if actor is None:
        return frozenset({VisibilityScope.PUBLIC_CASE})
    if actor.role in {ActorRole.PLAINTIFF_LAWYER, ActorRole.PROSECUTION_LAWYER}:
        return frozenset(
            {
                VisibilityScope.PUBLIC_CASE,
                VisibilityScope.PLAINTIFF_PRIVATE,
                VisibilityScope.PROSECUTION_PRIVATE,
            }
        )
    if actor.role == ActorRole.DEFENSE_LAWYER:
        return frozenset({VisibilityScope.PUBLIC_CASE, VisibilityScope.DEFENSE_PRIVATE})
    if actor.role == ActorRole.WITNESS:
        return frozenset({VisibilityScope.PUBLIC_CASE, VisibilityScope.WITNESS_PRIVATE})
    if actor.role in {ActorRole.TRIAL_JUDGE, ActorRole.JURY}:
        return frozenset({VisibilityScope.PUBLIC_CASE, VisibilityScope.JUDGE_ONLY})
    return frozenset({VisibilityScope.PUBLIC_CASE})


def excluded_categories(
    actor: Actor | None, node_purpose: NodePurpose, unknown_visibility: bool = False
) -> tuple[str, ...]:
    if node_purpose in {NodePurpose.ACTOR_EVALUATION, NodePurpose.COACHING}:
        base: list[str] = []
    else:
        base = ["synthetic_truth", "coaching_reference", "expected_verdict"]
    if node_purpose != NodePurpose.ACTOR_EVALUATION:
        base.append("canonical_case_package")
    if actor is None or actor.role != ActorRole.WITNESS:
        base.append("witness_private_knowledge_not_targeted")
    if unknown_visibility:
        base.append("unknown_visibility")
    return tuple(dict.fromkeys(base))


def allowed_actions(actor: Actor | None, node_purpose: NodePurpose) -> tuple[str, ...]:
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
