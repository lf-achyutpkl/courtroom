from __future__ import annotations

from courtroom_engine.context import (
    ContextBoundaryService,
    ContextRequest,
    NodePurpose,
    QuestionExecutionBriefDTO,
    TacticalActionPlanDTO,
)
from courtroom_engine.domain.case import Actor, ActorRole, PartySide
from courtroom_engine.domain.strategy import (
    CaseTheory,
    EvidencePlan,
    ObjectiveRuntimeState,
    OpponentRiskRecord,
    PartyStrategy,
    StrategicObjective,
    StrategyValidationRecord,
    StrategyValidationStatus,
    WitnessPlan,
)
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState


def plan_party_strategy(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
    side: PartySide,
    boundary: ContextBoundaryService | None = None,
) -> PartyStrategy:
    actor = _lawyer_for_side(case_package, side)
    context = (boundary or ContextBoundaryService()).build(
        case_package=case_package,
        state=state,
        request=ContextRequest(
            session_id=state.session_id,
            node_purpose=NodePurpose.GLOBAL_STRATEGY,
            requesting_actor_id=actor.actor_id,
        ),
    )
    material_records = tuple(
        record
        for record in context.case_view.intelligence.material_facts
        if record.supporting_side == side
    )
    target_fact_ids = tuple(record.fact_id for record in material_records)
    target_element_ids = tuple(dict.fromkeys(record.element_id for record in material_records))
    objective = StrategicObjective(
        objective_id=f"OBJ-{side.value.upper()}-FOUNDATION-01",
        description=f"Establish the strongest available {side.value} material facts.",
        target_element_ids=target_element_ids,
        target_fact_ids=target_fact_ids,
        priority=0.8 if target_fact_ids else 0.3,
        success_signals=tuple(f"Record supports {fact_id}" for fact_id in target_fact_ids)
        or ("No hidden material used.",),
        failure_signals=("Key fact remains unsupported.",),
    )
    strategy = PartyStrategy(
        strategy_id=f"STR-{side.value.upper()}-001",
        side=side,
        theory=CaseTheory(
            theory_id=f"THY-{side.value.upper()}-001",
            side=side,
            theme=f"{side.value.title()} theory from visible admissible proof",
            core_claim=(
                f"Use visible facts and witnesses to satisfy {side.value} objectives."
            ),
            target_element_ids=target_element_ids,
            supporting_fact_ids=target_fact_ids,
        ),
        objectives=(objective,),
        witness_plans=_plan_witnesses(case_package, side, objective.objective_id),
        evidence_plans=_plan_evidence(context, side, objective.objective_id),
        opponent_risks=_plan_opponent_risks(context, side),
        objective_states=(ObjectiveRuntimeState(objective_id=objective.objective_id),),
    )
    return strategy.model_copy(
        update={"validation": validate_party_strategy(strategy, context)}
    )


def validate_party_strategy(strategy: PartyStrategy, context) -> StrategyValidationRecord:
    visible_fact_ids = {fact.fact_id for fact in context.case_view.facts}
    visible_evidence_ids = {evidence.evidence_id for evidence in context.case_view.evidence}
    visible_witness_ids = {
        relationship.witness_id
        for relationship in context.case_view.intelligence.witness_fact_relationships
    }
    valid_element_ids = {
        record.element_id for record in context.case_view.intelligence.material_facts
    }
    invalid: list[str] = []
    messages: list[str] = []
    for objective in strategy.objectives:
        _collect_missing(invalid, objective.target_fact_ids, visible_fact_ids, "fact")
        _collect_missing(
            invalid, objective.target_element_ids, valid_element_ids, "element"
        )
        if not objective.success_signals:
            messages.append(f"{objective.objective_id} has no success signals")
    for plan in strategy.witness_plans:
        if visible_witness_ids and plan.witness_id not in visible_witness_ids:
            invalid.append(f"witness:{plan.witness_id}")
    for plan in strategy.evidence_plans:
        if plan.evidence_id not in visible_evidence_ids:
            invalid.append(f"evidence:{plan.evidence_id}")
        _collect_missing(invalid, plan.fact_ids, visible_fact_ids, "fact")
    status = (
        StrategyValidationStatus.INVALID
        if invalid or messages
        else StrategyValidationStatus.VALID
    )
    return StrategyValidationRecord(
        status=status,
        invalid_references=tuple(dict.fromkeys(invalid)),
        messages=tuple(messages),
    )


def build_tactical_action_plan(strategy: PartyStrategy, witness_id: str) -> TacticalActionPlanDTO:
    objective = strategy.objectives[0]
    return TacticalActionPlanDTO(
        action_id=f"ACTN-{objective.objective_id}-001",
        objective_id=objective.objective_id,
        action_type="ask_foundation_question",
        target_fact_ids=objective.target_fact_ids[:1],
        target_evidence_ids=tuple(
            plan.evidence_id
            for plan in strategy.evidence_plans
            if plan.through_witness_id == witness_id
        )[:1],
        target_witness_id=witness_id,
        expected_effect="Create admissible support for the active objective.",
    )


def build_question_execution_brief(
    action: TacticalActionPlanDTO,
) -> QuestionExecutionBriefDTO:
    if action.target_witness_id is None:
        raise ValueError("question generation requires a target witness")
    return QuestionExecutionBriefDTO(
        action_id=action.action_id,
        objective_id=action.objective_id,
        question_goal=action.expected_effect,
        target_witness_id=action.target_witness_id,
        allowed_fact_ids=action.target_fact_ids,
        allowed_evidence_ids=action.target_evidence_ids,
        prohibited_reference_ids=("party_strategy", "opponent_strategy"),
    )


def _lawyer_for_side(case_package: CompiledCasePackage, side: PartySide) -> Actor:
    expected = {
        PartySide.PLAINTIFF: ActorRole.PLAINTIFF_LAWYER,
        PartySide.PROSECUTION: ActorRole.PROSECUTION_LAWYER,
        PartySide.DEFENSE: ActorRole.DEFENSE_LAWYER,
    }[side]
    return next(actor for actor in case_package.actors if actor.role == expected)


def _plan_witnesses(
    case_package: CompiledCasePackage,
    side: PartySide,
    objective_id: str,
) -> tuple[WitnessPlan, ...]:
    plans: list[WitnessPlan] = []
    order = 1
    for witness in case_package.witnesses:
        if witness.called_by != side:
            continue
        plans.append(
            WitnessPlan(
                witness_id=witness.witness_id,
                calling_side=side,
                objective_ids=(objective_id,),
                direct_topics=(witness.public_summary,),
                cross_risks=("Opponent may test personal knowledge.",),
                order=order,
            )
        )
        order += 1
    return tuple(plans)


def _plan_evidence(context, side: PartySide, objective_id: str) -> tuple[EvidencePlan, ...]:
    plans: list[EvidencePlan] = []
    for evidence in context.case_view.evidence:
        if evidence.offered_by != side:
            continue
        witness_id = next(
            (
                relationship.witness_id
                for relationship in context.case_view.intelligence.witness_fact_relationships
                if relationship.fact_id in evidence.supports_fact_ids
            ),
            None,
        )
        plans.append(
            EvidencePlan(
                evidence_id=evidence.evidence_id,
                offering_side=side,
                objective_ids=(objective_id,),
                fact_ids=evidence.supports_fact_ids,
                through_witness_id=witness_id,
                foundation_required=evidence.foundation_required,
                expected_objections=("foundation",) if evidence.foundation_required else (),
                fallback="Proceed through witness testimony if excluded.",
            )
        )
    return tuple(plans)


def _plan_opponent_risks(context, side: PartySide) -> tuple[OpponentRiskRecord, ...]:
    risks: list[OpponentRiskRecord] = []
    for gap in context.case_view.intelligence.case_gaps:
        if gap.side in {None, side}:
            risks.append(
                OpponentRiskRecord(
                    risk_id=f"RISK-{side.value.upper()}-{gap.gap_id}",
                    side=side,
                    description=gap.description,
                    related_fact_ids=gap.fact_ids,
                    related_evidence_ids=gap.evidence_ids,
                    severity=gap.severity,
                )
            )
    return tuple(risks)


def _collect_missing(
    invalid: list[str],
    referenced_ids: tuple[str, ...],
    visible_ids: set[str],
    prefix: str,
) -> None:
    for referenced_id in referenced_ids:
        if referenced_id not in visible_ids:
            invalid.append(f"{prefix}:{referenced_id}")
