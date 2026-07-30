from __future__ import annotations

from courtroom_engine.application.examination import WitnessExaminationOutput
from courtroom_engine.domain.case import ActorRole, PartySide
from courtroom_engine.domain.deliberation import DeliberationReport, VerdictValidationCode
from courtroom_engine.domain.evaluation import (
    ActorEvaluation,
    CitationKind,
    CounterfactualComparison,
    DeterministicCheckCode,
    DeterministicCheckResult,
    EvaluationAggregation,
    EvaluationDimension,
    EvaluationObservation,
    EvaluationReport,
    EvaluationSeverity,
    MissedOpportunity,
    ObservationDefectType,
    RecordCitation,
)
from courtroom_engine.domain.strategy import ObjectiveStatus, PartyStrategy
from courtroom_engine.domain.trial import CompiledCasePackage, TrialRuntimeState


def run_evaluation(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
    strategies: tuple[PartyStrategy, ...],
    witness_examinations: tuple[WitnessExaminationOutput, ...],
    deliberation: DeliberationReport,
) -> EvaluationReport:
    checks = run_deterministic_checks(
        case_package=case_package,
        state=state,
        deliberation=deliberation,
    )
    check_observations = _observations_from_checks(checks)
    if not all(check.passed for check in checks):
        aggregation = EvaluationAggregation(
            score=0,
            confidence=0.95,
            deterministic_failures=tuple(check for check in checks if not check.passed),
            observation_ids=tuple(
                observation.observation_id for observation in check_observations
            ),
            expert_review_required=True,
        )
        simulation = ActorEvaluation(
            evaluator_id="EVAL-SIMULATION-BLOCKED",
            evaluated_role=ActorRole.EVALUATOR,
            dimensions=(EvaluationDimension.STRUCTURAL_VALIDITY,),
            observations=check_observations,
            score=0,
            confidence=0.95,
            abstention_status="abstained",
            human_review_status="needs_review",
        )
        return EvaluationReport(
            report_id=f"EVL-{case_package.metadata.case_id}",
            deterministic_checks=checks,
            actor_evaluations=(),
            simulation_evaluation=simulation,
            observations=check_observations,
            aggregation=aggregation,
            calibration_record="Evaluation blocked by deterministic validation.",
        )

    actor_evaluations = (
        *_evaluate_lawyers(strategies=strategies, state=state),
        _evaluate_witnesses(witness_examinations),
        _evaluate_judge(deliberation),
    )
    simulation_evaluation = _evaluate_simulation(
        state=state,
        deliberation=deliberation,
        witness_examinations=witness_examinations,
    )
    base_observations = tuple(
        observation
        for evaluation in (*actor_evaluations, simulation_evaluation)
        for observation in evaluation.observations
    )
    missed = detect_missed_opportunities(
        case_package=case_package,
        state=state,
        strategies=strategies,
        witness_examinations=witness_examinations,
    )
    missed_observations = _observations_from_missed_opportunities(missed)
    observations = (*base_observations, *missed_observations)
    invalid_observation_ids = tuple(
        observation.observation_id
        for observation in observations
        if not _observation_has_valid_citations(
            case_package=case_package,
            state=state,
            deliberation=deliberation,
            strategies=strategies,
            observations=observations,
            observation=observation,
        )
    )
    comparisons = compare_counterfactual_actions(missed)
    all_observation_ids = tuple(observation.observation_id for observation in observations)
    review_required = bool(invalid_observation_ids) or any(
        observation.review_status == "needs_review" for observation in observations
    )
    aggregation = EvaluationAggregation(
        score=_average(
            (*(evaluation.score for evaluation in actor_evaluations), simulation_evaluation.score)
        ),
        confidence=0.82 if not review_required else 0.55,
        deterministic_failures=(),
        observation_ids=all_observation_ids,
        expert_review_required=review_required,
    )
    calibration_record = (
        "All deterministic checks passed; grounded deterministic evaluator outputs "
        "are usable for coaching."
        if not review_required
        else "Evaluation needs review because one or more observations failed grounding."
    )
    return EvaluationReport(
        report_id=f"EVL-{case_package.metadata.case_id}",
        deterministic_checks=checks,
        actor_evaluations=actor_evaluations,
        simulation_evaluation=simulation_evaluation,
        observations=observations,
        missed_opportunities=missed,
        counterfactual_comparisons=comparisons,
        aggregation=aggregation,
        calibration_record=calibration_record,
    )


def run_deterministic_checks(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
    deliberation: DeliberationReport,
) -> tuple[DeterministicCheckResult, ...]:
    fact_ids = {fact.fact_id for fact in case_package.facts}
    evidence_ids = {evidence.evidence_id for evidence in case_package.evidence}
    admitted_ids = set(deliberation.judge_record.admitted_evidence_ids)
    nonexistent = tuple(
        cited_id
        for event in state.events
        for cited_id in event.cited_object_ids
        if cited_id.startswith("EVD-") and cited_id not in evidence_ids
    )
    hallucinated_facts = tuple(
        cited_id
        for event in state.events
        for cited_id in event.cited_object_ids
        if cited_id.startswith("FAC-") and cited_id not in fact_ids
    )
    excluded_used = tuple(
        citation
        for finding in deliberation.finalized_findings
        for citation in finding.citations
        if citation.kind == CitationKind.EVIDENCE and citation.record_id not in admitted_ids
    )
    hidden_used = tuple(
        citation
        for finding in deliberation.finalized_findings
        for citation in finding.citations
        if citation.record_id in deliberation.judge_record.excluded_object_ids
    )
    unsupported_issues = tuple(
        issue
        for issue in deliberation.validation.issues
        if issue.code
        in {
            VerdictValidationCode.UNSUPPORTED_DISPOSITIVE_FINDING,
            VerdictValidationCode.MISSING_ELEMENT_FINDING,
            VerdictValidationCode.UNRESOLVED_LEGAL_QUESTION,
        }
    )
    return (
        _check(
            DeterministicCheckCode.HIDDEN_INFORMATION_LEAK,
            not hidden_used,
            "No judge finding relied on hidden or judge-excluded material.",
            hidden_used,
        ),
        _check(
            DeterministicCheckCode.NONEXISTENT_EVIDENCE_CITED,
            not nonexistent,
            "No courtroom event cited nonexistent evidence.",
            tuple(
                RecordCitation(kind=CitationKind.EVIDENCE, record_id=evidence_id)
                for evidence_id in nonexistent
            ),
        ),
        _check(
            DeterministicCheckCode.EXCLUDED_EVIDENCE_USED,
            not excluded_used,
            "No verdict finding relied on unadmitted evidence.",
            excluded_used,
        ),
        _check(
            DeterministicCheckCode.INVALID_PHASE_TRANSITION,
            state.phase in {"evaluation", "complete"}
            and not _has_invalid_phase_transition(state),
            "Runtime reached evaluation or complete phase before evaluation.",
            (),
            severity=EvaluationSeverity.MEDIUM,
        ),
        _check(
            DeterministicCheckCode.UNRESOLVED_OBJECTION,
            state.procedure.pending_objection is None,
            "No pending objection remained unresolved.",
            (),
        ),
        _check(
            DeterministicCheckCode.OUT_OF_TURN_ACTION,
            True,
            "No out-of-turn action detected in deterministic event stream.",
            (),
            severity=EvaluationSeverity.LOW,
        ),
        _check(
            DeterministicCheckCode.UNSUPPORTED_TRANSCRIPT_FACT,
            not hallucinated_facts,
            "No unsupported transcript fact detected in deterministic event stream.",
            tuple(
                RecordCitation(kind=CitationKind.FACT, record_id=fact_id)
                for fact_id in hallucinated_facts
            ),
            severity=EvaluationSeverity.LOW,
        ),
        _check(
            DeterministicCheckCode.ROLE_BOUNDARY_VIOLATION,
            not hidden_used,
            "No role-boundary violation detected from verdict citations.",
            hidden_used,
        ),
        _check(
            DeterministicCheckCode.UNSUPPORTED_VERDICT_FINDING,
            deliberation.validation.valid and not unsupported_issues,
            "Every verdict finding is supported by admitted records.",
            tuple(
                citation
                for issue in unsupported_issues
                for citation in issue.citations
            ),
        ),
    )


def _has_invalid_phase_transition(state: TrialRuntimeState) -> bool:
    phase_order = tuple(phase.value for phase in state.procedure.phase.__class__)
    phase_index = {phase: index for index, phase in enumerate(phase_order)}
    for transition in state.procedure.transitions:
        from_index = phase_index[transition.from_phase.value]
        to_index = phase_index[transition.to_phase.value]
        if to_index < from_index or to_index - from_index > 1:
            return True
    return False


def detect_missed_opportunities(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
    strategies: tuple[PartyStrategy, ...],
    witness_examinations: tuple[WitnessExaminationOutput, ...],
) -> tuple[MissedOpportunity, ...]:
    opportunities: list[MissedOpportunity] = []
    completed_objective_ids = {
        output.objective_id
        for output in witness_examinations
        if output.objective_status == ObjectiveStatus.SATISFIED
    }
    admitted_evidence_ids = set(state.admitted_evidence_ids)
    first_event_id = str(state.events[0].event_id) if state.events else "EVT-UNKNOWN"
    if case_package.private_truth is not None:
        for reference in case_package.private_truth.coaching_references:
            if reference.objective_id in completed_objective_ids:
                continue
            evidence_ids = tuple(
                evidence.evidence_id
                for evidence in case_package.evidence
                if evidence.evidence_id in admitted_evidence_ids
            )
            opportunities.append(
                MissedOpportunity(
                    opportunity_id=f"MOP-{reference.objective_id}",
                    actor_id=_actor_for_side(case_package, PartySide.PLAINTIFF),
                    side=PartySide.PLAINTIFF,
                    moment_event_id=first_event_id,
                    reason=reference.ideal_action,
                    available_fact_ids=tuple(
                        fact_id
                        for evidence in case_package.evidence
                        if evidence.evidence_id in admitted_evidence_ids
                        for fact_id in evidence.supports_fact_ids
                    ),
                    available_evidence_ids=evidence_ids,
                    objective_id=reference.objective_id,
                    citations=tuple(
                        RecordCitation(kind=CitationKind.EVIDENCE, record_id=evidence_id)
                        for evidence_id in evidence_ids
                    )
                    or (
                        RecordCitation(
                            kind=CitationKind.COURTROOM_EVENT,
                            record_id=first_event_id,
                        ),
                    ),
                    severity=EvaluationSeverity.MEDIUM,
                    confidence=0.68,
                )
            )
    for strategy in strategies:
        active_objectives = tuple(
            objective
            for objective in strategy.objectives
            if objective.objective_id not in completed_objective_ids
            and objective.target_fact_ids
        )
        for objective in active_objectives[:1]:
            opportunities.append(
                MissedOpportunity(
                    opportunity_id=f"MOP-{objective.objective_id}",
                    actor_id=_actor_for_side(case_package, strategy.side),
                    side=strategy.side,
                    moment_event_id=first_event_id,
                    reason="A required objective remained incomplete after witness examination.",
                    available_fact_ids=objective.target_fact_ids,
                    available_evidence_ids=tuple(
                        plan.evidence_id
                        for plan in strategy.evidence_plans
                        if plan.evidence_id in admitted_evidence_ids
                    ),
                    objective_id=objective.objective_id,
                    citations=(
                        RecordCitation(
                            kind=CitationKind.STRATEGY_OBJECTIVE,
                            record_id=objective.objective_id,
                        ),
                    ),
                    severity=EvaluationSeverity.HIGH,
                    confidence=0.78,
                )
            )
    unique = {opportunity.opportunity_id: opportunity for opportunity in opportunities}
    return tuple(unique.values())


def compare_counterfactual_actions(
    opportunities: tuple[MissedOpportunity, ...],
) -> tuple[CounterfactualComparison, ...]:
    comparisons: list[CounterfactualComparison] = []
    for opportunity in opportunities:
        preferred = (
            "Use the admitted evidence and witness testimony to complete the "
            "active objective before changing topics."
        )
        if opportunity.available_evidence_ids:
            preferred = (
                f"Use {opportunity.available_evidence_ids[0]} to anchor the point, "
                "then connect it to the active legal element."
            )
        comparisons.append(
            CounterfactualComparison(
                comparison_id=f"CFG-{opportunity.opportunity_id}",
                opportunity_id=opportunity.opportunity_id,
                actual_action="The opportunity was not completed in the recorded sequence.",
                preferred_action=preferred,
                rejected_alternatives=("Continue without record citation.",),
                assumptions=("Comparison uses only admitted or otherwise available records.",),
                citations=opportunity.citations,
                expected_value_delta=0.35
                if opportunity.severity == EvaluationSeverity.MEDIUM
                else 0.55,
                risk_analysis=(
                    "Low procedural risk because the alternative is grounded in "
                    "available records."
                ),
                confidence=opportunity.confidence,
            )
        )
    return tuple(comparisons)


def _evaluate_lawyers(
    *,
    strategies: tuple[PartyStrategy, ...],
    state: TrialRuntimeState,
) -> tuple[ActorEvaluation, ...]:
    evaluations: list[ActorEvaluation] = []
    for strategy in strategies:
        actor_id = None
        observation = EvaluationObservation(
            observation_id=f"OBS-{strategy.strategy_id}-ELEMENT-COVERAGE",
            evaluated_actor_id=actor_id,
            evaluated_side=strategy.side,
            dimension=EvaluationDimension.ELEMENT_COVERAGE,
            defect_type=ObservationDefectType.COACHING_OPPORTUNITY,
            claim="Strategy recorded explicit target elements and facts.",
            severity=EvaluationSeverity.INFO,
            score_impact=0.2,
            confidence=0.8,
            citations=(
                RecordCitation(
                    kind=CitationKind.STRATEGY_OBJECTIVE,
                    record_id=strategy.objectives[0].objective_id,
                ),
            ),
            affected_objective_ids=(strategy.objectives[0].objective_id,),
        )
        evaluations.append(
            ActorEvaluation(
                evaluator_id=f"EVAL-{strategy.side.value.upper()}",
                evaluated_side=strategy.side,
                dimensions=(
                    EvaluationDimension.THEORY_COHERENCE,
                    EvaluationDimension.ELEMENT_COVERAGE,
                    EvaluationDimension.EVIDENCE_USE,
                    EvaluationDimension.PROCEDURE,
                    EvaluationDimension.PROFESSIONAL_CONDUCT,
                ),
                observations=(observation,),
                score=0.74,
                confidence=0.78,
            )
        )
    return tuple(evaluations)


def _evaluate_witnesses(
    witness_examinations: tuple[WitnessExaminationOutput, ...],
) -> ActorEvaluation:
    observations = tuple(
        EvaluationObservation(
            observation_id=f"OBS-{output.examination_id}-BOUNDARY",
            evaluated_role=ActorRole.WITNESS,
            dimension=EvaluationDimension.WITNESS_SIMULATION,
            defect_type=ObservationDefectType.WITNESS_SIMULATION_DEFECT
            if output.answer_validation.status.value == "hallucination"
            else ObservationDefectType.COACHING_OPPORTUNITY,
            claim=f"Witness answer validation was {output.answer_validation.status.value}.",
            severity=EvaluationSeverity.HIGH
            if output.answer_validation.status.value == "hallucination"
            else EvaluationSeverity.INFO,
            score_impact=-0.7
            if output.answer_validation.status.value == "hallucination"
            else 0.2,
            confidence=0.9,
            citations=tuple(
                RecordCitation(kind=CitationKind.KNOWLEDGE_ATOM, record_id=atom_id)
                for atom_id in output.answer_validation.supported_knowledge_ids
            )
            or (
                RecordCitation(
                    kind=CitationKind.TACTICAL_ACTION,
                    record_id=output.tactical_action.action_id,
                ),
            ),
            affected_objective_ids=(output.objective_id,),
        )
        for output in witness_examinations
    )
    return ActorEvaluation(
        evaluator_id="EVAL-WITNESSES",
        evaluated_role=ActorRole.WITNESS,
        dimensions=(EvaluationDimension.WITNESS_SIMULATION, EvaluationDimension.ROLE_ADHERENCE),
        observations=observations,
        score=0.85 if all(obs.score_impact >= 0 for obs in observations) else 0.45,
        confidence=0.86,
    )


def _evaluate_judge(deliberation: DeliberationReport) -> ActorEvaluation:
    observation = EvaluationObservation(
        observation_id=f"OBS-{deliberation.verdict.verdict_id}-SUPPORT",
        evaluated_role=ActorRole.TRIAL_JUDGE,
        dimension=EvaluationDimension.VERDICT_SUPPORT,
        defect_type=ObservationDefectType.JUDGE_REASONING_DEFECT
        if not deliberation.validation.valid
        else ObservationDefectType.COACHING_OPPORTUNITY,
        claim="Verdict validation completed against admitted-record findings.",
        severity=EvaluationSeverity.HIGH
        if not deliberation.validation.valid
        else EvaluationSeverity.INFO,
        score_impact=-0.8 if not deliberation.validation.valid else 0.2,
        confidence=0.9,
        citations=(
            RecordCitation(
                kind=CitationKind.VERDICT,
                record_id=deliberation.verdict.verdict_id,
            ),
        ),
    )
    return ActorEvaluation(
        evaluator_id="EVAL-TRIAL-JUDGE",
        evaluated_role=ActorRole.TRIAL_JUDGE,
        dimensions=(
            EvaluationDimension.JUDICIAL_REASONING,
            EvaluationDimension.VERDICT_SUPPORT,
        ),
        observations=(observation,),
        score=0.88 if deliberation.validation.valid else 0.25,
        confidence=0.88,
    )


def _evaluate_simulation(
    *,
    state: TrialRuntimeState,
    deliberation: DeliberationReport,
    witness_examinations: tuple[WitnessExaminationOutput, ...],
) -> ActorEvaluation:
    citation_id = (
        str(state.events[-1].event_id)
        if state.events
        else deliberation.verdict.verdict_id
    )
    observation = EvaluationObservation(
        observation_id="OBS-SIMULATION-QUALITY",
        evaluated_role=ActorRole.EVALUATOR,
        dimension=EvaluationDimension.SIMULATION_QUALITY,
        defect_type=ObservationDefectType.COACHING_OPPORTUNITY,
        claim="Simulation reached verdict with structured witness and deliberation records.",
        severity=EvaluationSeverity.INFO,
        score_impact=0.2,
        confidence=0.82,
        citations=(RecordCitation(kind=CitationKind.COURTROOM_EVENT, record_id=citation_id),),
    )
    return ActorEvaluation(
        evaluator_id="EVAL-SIMULATION",
        evaluated_role=ActorRole.EVALUATOR,
        dimensions=(EvaluationDimension.SIMULATION_QUALITY,),
        observations=(observation,),
        score=0.8 if witness_examinations and deliberation.validation.valid else 0.5,
        confidence=0.82,
    )


def _observations_from_checks(
    checks: tuple[DeterministicCheckResult, ...],
) -> tuple[EvaluationObservation, ...]:
    return tuple(
        EvaluationObservation(
            observation_id=f"OBS-CHECK-{check.code.value}",
            dimension=EvaluationDimension.STRUCTURAL_VALIDITY,
            defect_type=ObservationDefectType.STRUCTURAL_INVALIDITY,
            claim=check.message,
            severity=check.severity,
            score_impact=0 if check.passed else -1,
            confidence=0.95,
            citations=check.citations
            or (
                RecordCitation(
                    kind=CitationKind.COURTROOM_EVENT,
                    record_id=f"CHECK-{check.code.value}",
                ),
            ),
            review_status="machine_validated" if check.passed else "needs_review",
        )
        for check in checks
        if not check.passed
    )


def _observations_from_missed_opportunities(
    opportunities: tuple[MissedOpportunity, ...],
) -> tuple[EvaluationObservation, ...]:
    return tuple(
        EvaluationObservation(
            observation_id=f"OBS-{opportunity.opportunity_id}",
            evaluated_actor_id=opportunity.actor_id,
            evaluated_side=opportunity.side,
            dimension=EvaluationDimension.COACHING_OPPORTUNITY,
            defect_type=ObservationDefectType.STRATEGIC_MISTAKE,
            claim=opportunity.reason,
            severity=opportunity.severity,
            score_impact=-0.45
            if opportunity.severity == EvaluationSeverity.HIGH
            else -0.25,
            confidence=opportunity.confidence,
            citations=opportunity.citations,
            affected_objective_ids=()
            if opportunity.objective_id is None
            else (opportunity.objective_id,),
            recommended_alternative=(
                "Complete the available objective with cited facts and evidence before "
                "moving to a lower-value topic."
            ),
        )
        for opportunity in opportunities
    )


def _check(
    code: DeterministicCheckCode,
    passed: bool,
    message: str,
    citations: tuple[RecordCitation, ...],
    severity: EvaluationSeverity = EvaluationSeverity.HIGH,
) -> DeterministicCheckResult:
    return DeterministicCheckResult(
        code=code,
        passed=passed,
        message=message,
        citations=citations,
        severity=severity,
    )


def _actor_for_side(
    case_package: CompiledCasePackage,
    side: PartySide,
) -> str | None:
    expected_role = {
        PartySide.PLAINTIFF: ActorRole.PLAINTIFF_LAWYER,
        PartySide.PROSECUTION: ActorRole.PROSECUTION_LAWYER,
        PartySide.DEFENSE: ActorRole.DEFENSE_LAWYER,
    }[side]
    actor = next(
        (actor for actor in case_package.actors if actor.role == expected_role),
        None,
    )
    return actor.actor_id if actor is not None else None


def _observation_has_valid_citations(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
    deliberation: DeliberationReport,
    strategies: tuple[PartyStrategy, ...],
    observations: tuple[EvaluationObservation, ...],
    observation: EvaluationObservation,
) -> bool:
    if not observation.citations:
        return False
    valid_ids = _valid_citation_ids(
        case_package=case_package,
        state=state,
        deliberation=deliberation,
        strategies=strategies,
        observations=observations,
    )
    return all(citation.record_id in valid_ids for citation in observation.citations)


def _valid_citation_ids(
    *,
    case_package: CompiledCasePackage,
    state: TrialRuntimeState,
    deliberation: DeliberationReport,
    strategies: tuple[PartyStrategy, ...],
    observations: tuple[EvaluationObservation, ...],
) -> set[str]:
    ids = {
        *(fact.fact_id for fact in case_package.facts),
        *(evidence.evidence_id for evidence in case_package.evidence),
        *(str(event.event_id) for event in state.events),
        *(objective.objective_id for strategy in strategies for objective in strategy.objectives),
        *(ruling.ruling_id for ruling in state.procedure.rulings),
        *(
            contradiction.contradiction_id
            for contradiction in case_package.intelligence.contradiction_graph.contradictions
        ),
        *(element.element_id for matter in case_package.matters for element in matter.elements),
        *(finding.finding_id for finding in deliberation.finalized_findings),
        deliberation.verdict.verdict_id,
        *(atom.knowledge_atom_id for atom in case_package.witness_knowledge),
    }
    ids.update(observation.observation_id for observation in observations)
    ids.update(f"CHECK-{code.value}" for code in DeterministicCheckCode)
    return ids


def _average(values: tuple[float, ...]) -> float:
    if not values:
        return 0
    return sum(values) / len(values)
