from __future__ import annotations

from courtroom_engine.domain.coaching import (
    BetterActionSequence,
    CoachingMoment,
    CoachingReport,
    CoachingSkill,
    SkillEvidence,
    SkillProfileUpdate,
)
from courtroom_engine.domain.evaluation import (
    EvaluationDimension,
    EvaluationObservation,
    EvaluationReport,
    EvaluationSeverity,
    ObservationDefectType,
)


def run_coaching(*, evaluation: EvaluationReport) -> CoachingReport:
    validate_coaching_ready(evaluation)
    learning_observations = select_high_value_learning_moments(evaluation)
    moments = tuple(
        _build_coaching_moment(observation)
        for observation in learning_observations
    )
    sequences = tuple(
        BetterActionSequence(
            sequence_id=f"SEQ-{moment.moment_id}",
            moment_id=moment.moment_id,
            steps=(
                "Reconstruct the record available at that moment.",
                moment.better_action,
                "Ask or argue only from cited facts and admitted evidence.",
                "Connect the answer back to the affected legal objective.",
            ),
            citations=moment.available_information,
        )
        for moment in moments
    )
    skill_updates = _build_skill_updates(moments, learning_observations)
    plan = tuple(dict.fromkeys(_practice_theme(moment.skill) for moment in moments))
    return CoachingReport(
        report_id=f"COACH-{evaluation.report_id}",
        source_evaluation_report_id=evaluation.report_id,
        moments=moments,
        better_action_sequences=sequences,
        improvement_plan=plan,
        skill_profile_updates=skill_updates,
    )


def validate_coaching_ready(evaluation: EvaluationReport) -> None:
    if not evaluation.deterministic_validation_passed:
        raise ValueError("coaching requires deterministic validation to pass")
    if evaluation.aggregation.expert_review_required:
        raise ValueError("coaching requires grounded evaluation observations")
    citation_free = [
        observation.observation_id
        for observation in evaluation.observations
        if not observation.citations
    ]
    if citation_free:
        raise ValueError(
            "coaching refuses citation-free evaluation observations: "
            + ", ".join(citation_free)
        )


def select_high_value_learning_moments(
    evaluation: EvaluationReport,
) -> tuple[EvaluationObservation, ...]:
    selected = [
        observation
        for observation in evaluation.observations
        if observation.dimension == EvaluationDimension.COACHING_OPPORTUNITY
        or observation.defect_type
        in {
            ObservationDefectType.STRATEGIC_MISTAKE,
            ObservationDefectType.EXECUTION_PROBLEM,
            ObservationDefectType.LEGAL_GROUNDING_PROBLEM,
            ObservationDefectType.JUDGE_REASONING_DEFECT,
        }
    ]
    selected.sort(
        key=lambda observation: (
            _severity_rank(observation.severity),
            abs(observation.score_impact),
            observation.confidence,
        ),
        reverse=True,
    )
    return tuple(selected[:5])


def _build_coaching_moment(observation: EvaluationObservation) -> CoachingMoment:
    skill = _skill_for_observation(observation)
    return CoachingMoment(
        moment_id=f"CM-{observation.observation_id}",
        observation_id=observation.observation_id,
        actor_id=observation.evaluated_actor_id,
        role=observation.evaluated_role,
        side=observation.evaluated_side,
        transcript_location=observation.citations[0].record_id,
        skill=skill,
        what_happened=observation.claim,
        affected_objective_ids=observation.affected_objective_ids,
        available_information=observation.citations,
        why_it_mattered=_why_it_matters(observation),
        better_action=observation.recommended_alternative
        or "Use the cited record to complete the active legal objective.",
        example_wording=_example_wording(skill),
        expected_response="The record becomes clearer on the targeted legal point.",
        recovery_option=(
            "Return to the objective at the next permitted turn and ground the point "
            "in admitted evidence or witness testimony."
        ),
        severity=observation.severity.value,
        confidence=observation.confidence,
    )


def _build_skill_updates(
    moments: tuple[CoachingMoment, ...],
    observations: tuple[EvaluationObservation, ...],
) -> tuple[SkillProfileUpdate, ...]:
    observation_by_id = {observation.observation_id: observation for observation in observations}
    grouped: dict[tuple[str | None, str | None, str], list[SkillEvidence]] = {}
    for moment in moments:
        observation = observation_by_id[moment.observation_id]
        evidence = SkillEvidence(
            evidence_id=f"SKE-{moment.moment_id}",
            actor_id=moment.actor_id,
            role=moment.role,
            side=moment.side,
            skill=moment.skill,
            source_observation_id=moment.observation_id,
            citations=moment.available_information,
            direction="negative"
            if observation.score_impact < 0
            else "positive",
            strength=abs(observation.score_impact),
            confidence=moment.confidence,
            source_evaluator_version=observation.evaluator_version,
            profile_scope="ai_actor",
        )
        key = (
            evidence.actor_id,
            evidence.role.value if evidence.role is not None else None,
            evidence.profile_scope,
        )
        grouped.setdefault(key, []).append(evidence)
    return tuple(
        SkillProfileUpdate(
            actor_id=evidence_list[0].actor_id,
            role=evidence_list[0].role,
            profile_scope=evidence_list[0].profile_scope,
            appended_evidence=tuple(evidence_list),
        )
        for evidence_list in grouped.values()
    )


def _skill_for_observation(observation: EvaluationObservation) -> CoachingSkill:
    mapping = {
        EvaluationDimension.LEGAL_GROUNDING: CoachingSkill.LEGAL_GROUNDING,
        EvaluationDimension.THEORY_COHERENCE: CoachingSkill.THEORY_DEVELOPMENT,
        EvaluationDimension.ELEMENT_COVERAGE: CoachingSkill.ISSUE_SPOTTING,
        EvaluationDimension.OBJECTIVE_SELECTION: CoachingSkill.OBJECTIVE_SELECTION,
        EvaluationDimension.EVIDENCE_USE: CoachingSkill.EVIDENCE_USE,
        EvaluationDimension.FOUNDATION: CoachingSkill.FOUNDATION,
        EvaluationDimension.CONTRADICTION_HANDLING: CoachingSkill.CONTRADICTION_HANDLING,
        EvaluationDimension.OBJECTIONS: CoachingSkill.OBJECTION_HANDLING,
        EvaluationDimension.ADAPTATION: CoachingSkill.ADAPTATION,
        EvaluationDimension.OPENING: CoachingSkill.OPENING,
        EvaluationDimension.CLOSING: CoachingSkill.CLOSING,
        EvaluationDimension.PROCEDURE: CoachingSkill.PROCEDURE,
        EvaluationDimension.ROLE_ADHERENCE: CoachingSkill.ROLE_ADHERENCE,
        EvaluationDimension.PROFESSIONAL_CONDUCT: CoachingSkill.PROFESSIONAL_CONDUCT,
        EvaluationDimension.JUDICIAL_REASONING: CoachingSkill.JUDICIAL_REASONING,
        EvaluationDimension.VERDICT_SUPPORT: CoachingSkill.JUDICIAL_REASONING,
        EvaluationDimension.COACHING_OPPORTUNITY: CoachingSkill.EVIDENCE_USE,
    }
    return mapping.get(observation.dimension, CoachingSkill.LEGAL_GROUNDING)


def _why_it_matters(observation: EvaluationObservation) -> str:
    if observation.affected_objective_ids:
        return (
            "The moment affected objective "
            f"{', '.join(observation.affected_objective_ids)} and could change case "
            "strength if handled differently."
        )
    return "The moment affects how reliably the trial record supports later decisions."


def _example_wording(skill: CoachingSkill) -> str:
    examples = {
        CoachingSkill.FOUNDATION: (
            "Do you recognize this exhibit, and how do you know what it shows?"
        ),
        CoachingSkill.CONTRADICTION_HANDLING: (
            "Earlier you said the opposite; which statement should the court rely on?"
        ),
        CoachingSkill.EVIDENCE_USE: (
            "Directing your attention to the admitted exhibit, what fact does it show?"
        ),
        CoachingSkill.OBJECTION_HANDLING: "Objection, foundation.",
    }
    return examples.get(skill, "What fact in the record supports that point?")


def _practice_theme(skill: CoachingSkill) -> str:
    labels = {
        CoachingSkill.FOUNDATION: "Practice laying foundation before using exhibits.",
        CoachingSkill.CONTRADICTION_HANDLING: (
            "Practice committing testimony before confronting contradictions."
        ),
        CoachingSkill.EVIDENCE_USE: (
            "Practice tying admitted evidence to required legal elements."
        ),
        CoachingSkill.JUDICIAL_REASONING: (
            "Practice explaining verdict findings from the admitted record only."
        ),
    }
    return labels.get(skill, f"Practice {skill.value.replace('_', ' ')} with citations.")


def _severity_rank(severity: EvaluationSeverity) -> int:
    return {
        EvaluationSeverity.INFO: 0,
        EvaluationSeverity.LOW: 1,
        EvaluationSeverity.MEDIUM: 2,
        EvaluationSeverity.HIGH: 3,
        EvaluationSeverity.CRITICAL: 4,
    }[severity]
