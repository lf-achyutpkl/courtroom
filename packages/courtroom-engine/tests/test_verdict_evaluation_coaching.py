from __future__ import annotations

import unittest

from courtroom_engine.application.coaching import run_coaching
from courtroom_engine.application.deliberation import (
    run_judicial_deliberation,
    validate_verdict,
)
from courtroom_engine.application.evaluation import run_evaluation
from courtroom_engine.application.examination import run_witness_examination
from courtroom_engine.application.planning import plan_party_strategy
from courtroom_engine.compiler import CaseCompiler
from courtroom_engine.domain.deliberation import VerdictValidationCode
from courtroom_engine.domain.evaluation import (
    CitationKind,
    DeterministicCheckCode,
    EvaluationObservation,
    EvaluationSeverity,
    RecordCitation,
)
from courtroom_engine.domain.events import CourtroomEvent, CourtroomEventType
from courtroom_engine.domain.procedure import (
    EvidenceAdmissionRecord,
    EvidenceAdmissionStatus,
    ProcedureState,
    TrialPhase,
)
from courtroom_engine.domain.trial import TrialRuntimeState
from courtroom_engine.fixtures import build_reference_case


class VerdictEvaluationCoachingTests(unittest.TestCase):
    def test_judge_record_excludes_private_and_unadmitted_material(self) -> None:
        package, runtime, strategies, examinations = _run_recorded_trial()

        deliberation = run_judicial_deliberation(
            case_package=package,
            state=runtime,
        )

        self.assertEqual(deliberation.verdict.outcome.value, "plaintiff")
        self.assertIn("EVD-CAMERA", deliberation.judge_record.admitted_evidence_ids)
        self.assertIn("FAC-SPILL-NOTICED", deliberation.judge_record.admitted_fact_ids)
        self.assertIn(
            "FAC-DEFENSE-INSPECTION",
            deliberation.judge_record.excluded_object_ids,
        )
        self.assertIn(
            "CON-INSPECTION-VIDEO",
            deliberation.judge_record.excluded_object_ids,
        )
        self.assertNotIn(
            "FAC-DEFENSE-INSPECTION",
            deliberation.judge_record.admitted_fact_ids,
        )
        self.assertTrue(deliberation.validation.valid)

    def test_verdict_validation_rejects_excluded_evidence_reliance(self) -> None:
        package, runtime, _, _ = _run_recorded_trial()
        deliberation = run_judicial_deliberation(
            case_package=package,
            state=runtime,
        )
        bad_finding = deliberation.finalized_findings[0].model_copy(
            update={
                "citations": (
                    *deliberation.finalized_findings[0].citations,
                    RecordCitation(
                        kind=CitationKind.EVIDENCE,
                        record_id="EVD-NOT-ADMITTED",
                    ),
                )
            }
        )

        validation = validate_verdict(
            case_package=package,
            judge_record=deliberation.judge_record,
            legal_questions=deliberation.legal_questions,
            element_evaluations=deliberation.element_evaluations,
            burden_applications=deliberation.burden_applications,
            finalized_findings=(bad_finding,),
            verdict=deliberation.verdict,
        )

        self.assertFalse(validation.valid)
        self.assertIn(
            VerdictValidationCode.EXCLUDED_EVIDENCE_RELIANCE,
            {issue.code for issue in validation.issues},
        )

    def test_evaluation_blocks_when_deterministic_checks_fail(self) -> None:
        package, runtime, strategies, examinations = _run_recorded_trial()
        deliberation = run_judicial_deliberation(
            case_package=package,
            state=runtime,
        )
        invalid_runtime = runtime.model_copy(
            update={
                "events": (
                    *runtime.events,
                    CourtroomEvent(
                        event_type=CourtroomEventType.CLOSING_DELIVERED,
                        summary="Invalid citation.",
                        cited_object_ids=("EVD-DOES-NOT-EXIST",),
                    ),
                )
            }
        )

        evaluation = run_evaluation(
            case_package=package,
            state=invalid_runtime,
            strategies=strategies,
            witness_examinations=examinations,
            deliberation=deliberation,
        )

        self.assertFalse(evaluation.deterministic_validation_passed)
        self.assertEqual(evaluation.actor_evaluations, ())
        self.assertEqual(evaluation.simulation_evaluation.abstention_status, "abstained")
        self.assertIn(
            DeterministicCheckCode.NONEXISTENT_EVIDENCE_CITED,
            {
                check.code
                for check in evaluation.deterministic_checks
                if not check.passed
            },
        )

    def test_evaluation_observations_missed_opportunities_and_counterfactuals_are_grounded(
        self,
    ) -> None:
        package, runtime, strategies, examinations = _run_recorded_trial()
        deliberation = run_judicial_deliberation(
            case_package=package,
            state=runtime,
        )

        evaluation = run_evaluation(
            case_package=package,
            state=runtime,
            strategies=strategies,
            witness_examinations=examinations,
            deliberation=deliberation,
        )

        self.assertTrue(evaluation.deterministic_validation_passed)
        self.assertTrue(evaluation.observations)
        self.assertTrue(all(observation.citations for observation in evaluation.observations))
        self.assertTrue(evaluation.missed_opportunities)
        self.assertTrue(evaluation.counterfactual_comparisons)
        self.assertTrue(
            all(
                comparison.citations
                for comparison in evaluation.counterfactual_comparisons
            )
        )
        self.assertFalse(evaluation.aggregation.expert_review_required)

    def test_coaching_requires_grounded_evaluation_and_updates_skill_evidence(
        self,
    ) -> None:
        package, runtime, strategies, examinations = _run_recorded_trial()
        deliberation = run_judicial_deliberation(
            case_package=package,
            state=runtime,
        )
        evaluation = run_evaluation(
            case_package=package,
            state=runtime,
            strategies=strategies,
            witness_examinations=examinations,
            deliberation=deliberation,
        )

        coaching = run_coaching(evaluation=evaluation)

        self.assertTrue(coaching.moments)
        self.assertTrue(coaching.skill_profile_updates)
        for moment in coaching.moments:
            self.assertTrue(moment.available_information)
            self.assertIn(moment.observation_id, evaluation.aggregation.observation_ids)
        for update in coaching.skill_profile_updates:
            for evidence in update.appended_evidence:
                self.assertEqual(evidence.profile_scope, "ai_actor")
                self.assertTrue(evidence.citations)

    def test_coaching_refuses_citation_free_observations(self) -> None:
        package, runtime, strategies, examinations = _run_recorded_trial()
        deliberation = run_judicial_deliberation(
            case_package=package,
            state=runtime,
        )
        evaluation = run_evaluation(
            case_package=package,
            state=runtime,
            strategies=strategies,
            witness_examinations=examinations,
            deliberation=deliberation,
        )
        bad_observation = EvaluationObservation(
            observation_id="OBS-CITATION-FREE",
            dimension=evaluation.observations[0].dimension,
            defect_type=evaluation.observations[0].defect_type,
            claim="Ungrounded claim.",
            severity=EvaluationSeverity.HIGH,
            score_impact=-1,
            confidence=0.9,
            citations=(),
        )
        invalid_evaluation = evaluation.model_copy(
            update={"observations": (*evaluation.observations, bad_observation)}
        )

        with self.assertRaises(ValueError):
            run_coaching(evaluation=invalid_evaluation)


def _run_recorded_trial():
    package = CaseCompiler().compile(build_reference_case())
    runtime = TrialRuntimeState(
        case_id=package.metadata.case_id,
        phase=TrialPhase.EVALUATION.value,
        procedure=ProcedureState(phase=TrialPhase.EVALUATION),
    )
    plaintiff_strategy = plan_party_strategy(
        case_package=package,
        state=runtime,
        side=package.parties[0].side,
    )
    defense_strategy = plan_party_strategy(
        case_package=package,
        state=runtime,
        side=package.parties[1].side,
    )
    examination = run_witness_examination(
        case_package=package,
        state=runtime,
        strategy=plaintiff_strategy,
        witness_id="WIT-CASHIER",
    )
    admissions = (
        EvidenceAdmissionRecord(
            evidence_id="EVD-CAMERA",
            status=EvidenceAdmissionStatus.ADMITTED,
        ),
    )
    runtime = runtime.model_copy(
        update={
            "admitted_evidence_ids": ("EVD-CAMERA",),
            "events": examination.events,
            "procedure": runtime.procedure.model_copy(
                update={"evidence_admissions": admissions}
            ),
        }
    )
    return (
        package,
        runtime,
        (plaintiff_strategy, defense_strategy),
        (examination,),
    )


if __name__ == "__main__":
    unittest.main()
