from __future__ import annotations

import unittest
from pathlib import Path

from courtroom_engine.application.deliberation import run_judicial_deliberation
from courtroom_engine.application.evaluation import run_evaluation
from courtroom_engine.application.examination import run_witness_examination
from courtroom_engine.application.planning import plan_party_strategy
from courtroom_engine.compiler import CaseCompiler
from courtroom_engine.domain.evaluation import DeterministicCheckCode
from courtroom_engine.domain.events import CourtroomEvent, CourtroomEventType
from courtroom_engine.domain.procedure import (
    EvidenceAdmissionRecord,
    EvidenceAdmissionStatus,
    PhaseTransitionRecord,
    ProcedureState,
    TrialPhase,
)
from courtroom_engine.domain.trial import TrialRuntimeState
from courtroom_engine.fixtures import build_reference_case


REPO_ROOT = Path(__file__).resolve().parents[3]


class TestingAcceptanceGateTests(unittest.TestCase):
    def test_compact_ai_vs_ai_vertical_slice_answers_reviewer_questions(self) -> None:
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
        intelligence = package.intelligence

        self.assertTrue(
            {
                element.element_id
                for matter in package.matters
                for element in matter.elements
            }
        )
        self.assertTrue(intelligence.material_fact_map.facts)
        self.assertTrue(intelligence.evidence_graph.relationships)
        self.assertTrue(intelligence.witness_knowledge_graph.relationships)
        self.assertTrue(intelligence.contradiction_graph.contradictions)
        self.assertTrue(intelligence.case_gaps)

        strategy = strategies[0]
        self.assertTrue(strategy.objectives)
        self.assertTrue(strategy.witness_plans)
        self.assertTrue(strategy.evidence_plans)
        self.assertTrue(deliberation.verdict.finding_ids)
        self.assertTrue(evaluation.observations)
        self.assertTrue(evaluation.counterfactual_comparisons)

    def test_regression_gates_block_invalid_phase_and_hallucinated_fact(self) -> None:
        package, runtime, strategies, examinations = _run_recorded_trial()
        invalid_procedure = runtime.procedure.model_copy(
            update={
                "transitions": (
                    PhaseTransitionRecord(
                        from_phase=TrialPhase.OPENING,
                        to_phase=TrialPhase.DELIBERATION,
                        reason="Skipped witness examination and closing.",
                    ),
                )
            }
        )
        invalid_runtime = runtime.model_copy(
            update={
                "events": (
                    *runtime.events,
                    CourtroomEvent(
                        event_type=CourtroomEventType.WITNESS_ANSWERED,
                        summary="Witness asserted an unauthored fact.",
                        cited_object_ids=("FAC-HALLUCINATED",),
                    ),
                ),
                "procedure": invalid_procedure,
            }
        )
        deliberation = run_judicial_deliberation(
            case_package=package,
            state=invalid_runtime,
        )

        evaluation = run_evaluation(
            case_package=package,
            state=invalid_runtime,
            strategies=strategies,
            witness_examinations=examinations,
            deliberation=deliberation,
        )

        failed_codes = {
            check.code for check in evaluation.deterministic_checks if not check.passed
        }
        self.assertFalse(evaluation.deterministic_validation_passed)
        self.assertIn(DeterministicCheckCode.INVALID_PHASE_TRANSITION, failed_codes)
        self.assertIn(DeterministicCheckCode.UNSUPPORTED_TRANSCRIPT_FACT, failed_codes)
        self.assertEqual(evaluation.actor_evaluations, ())
        self.assertEqual(evaluation.simulation_evaluation.abstention_status, "abstained")

    def test_courtroom_engine_has_no_langgraph_runtime_surface(self) -> None:
        pyproject = (REPO_ROOT / "packages/courtroom-engine/pyproject.toml").read_text()
        package_root = REPO_ROOT / "packages/courtroom-engine/src/courtroom_engine"

        self.assertNotIn("langgraph", pyproject)
        self.assertFalse((REPO_ROOT / "packages/courtroom-engine/langgraph.json").exists())
        self.assertFalse((package_root / "graph.py").exists())
        self.assertFalse((package_root / "studio.py").exists())
        self.assertFalse((package_root / "orchestration").exists())


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
    return package, runtime, (plaintiff_strategy, defense_strategy), (examination,)


if __name__ == "__main__":
    unittest.main()
