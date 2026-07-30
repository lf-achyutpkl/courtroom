from __future__ import annotations

import importlib.util
import json
import sys
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
from courtroom_engine.graph import V2AiAiState, build_v2_ai_ai_graph


REPO_ROOT = Path(__file__).resolve().parents[3]


class TestingAcceptanceGateTests(unittest.TestCase):
    def test_compact_ai_vs_ai_vertical_slice_answers_reviewer_questions(self) -> None:
        result = build_v2_ai_ai_graph().invoke(V2AiAiState())

        package = result["case_package"]
        runtime = result["runtime"]
        strategy = next(iter(result["strategies"].values()))
        deliberation = result["deliberation"]
        evaluation = result["evaluation"]
        coaching = result["coaching"]
        intelligence = package.intelligence

        self.assertEqual(result["status"], "coaching_complete")
        self.assertEqual(runtime.phase, TrialPhase.COMPLETE.value)

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

        self.assertTrue(strategy.objectives)
        self.assertTrue(strategy.witness_plans)
        self.assertTrue(strategy.evidence_plans)
        self.assertTrue(deliberation.verdict.finding_ids)
        self.assertTrue(evaluation.observations)
        self.assertTrue(evaluation.counterfactual_comparisons)
        self.assertTrue(coaching.moments)

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

    def test_langstudio_v2_graph_export_is_registered_and_importable(self) -> None:
        langgraph_config = json.loads(
            (REPO_ROOT / "apps/agent-service/langgraph.json").read_text()
        )

        self.assertIn("trial", langgraph_config["graphs"])
        self.assertIn("examine-witness", langgraph_config["graphs"])
        self.assertEqual(
            langgraph_config["graphs"]["trial-v2-ai-ai"],
            "./src/v2/ai_ai_graph.py:graph",
        )

        app_src = REPO_ROOT / "apps/agent-service/src"
        sys.path.insert(0, str(app_src))
        try:
            spec = importlib.util.spec_from_file_location(
                "v2_ai_ai_graph_smoke",
                app_src / "v2/ai_ai_graph.py",
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(str(app_src))

        result = module.graph.invoke(V2AiAiState())
        self.assertEqual(result["status"], "coaching_complete")


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
