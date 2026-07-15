import json
import tempfile
import unittest
from pathlib import Path

from src.evaluation.baseline import build_baseline_report, calculate_aggregate_metrics
from src.evaluation.reports import (
    PerCaseEvaluationResult,
    build_report_path,
    write_baseline_report,
)
from src.evaluation.rubric import RubricEvaluatorConfig, RubricScore, TokenUsage
from src.utils.types import RunMetadata, RunTrialResponse, TranscriptTurn
from src.utils.validation import DeterministicValidationError


def fake_runner(request):
    return RunTrialResponse(
        full_trial_transcript=[
            TranscriptTurn(
                scene="verdict",
                speaker_id="judge",
                text="Verdict cites the case evidence.",
            )
        ],
        run=RunMetadata(
            run_id=f"run-{request.case_file.case_id}",
            case_id=request.case_file.case_id,
            graph_version="v1",
            prompt_version="v1",
            model_name="gpt-4o-mini",
            judge_model_name="gpt-4o-mini",
            environment="test",
            deterministic_validation_passed=True,
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
            duration_ms=1000,
        ),
    )


PASSING_FACTS_BY_CASE_ID = {
    "case-ledger-theft": "after-hours payments and badge access",
    "case-warehouse-injury": "backup alarm failed inspection",
    "case-sealed-medical-record": "sealed record and supervisor approval",
}


def rule_passing_runner(request):
    fact_text = PASSING_FACTS_BY_CASE_ID[request.case_file.case_id]
    evidence_ids = [evidence.evidence_id for evidence in request.case_file.evidence]
    evidence_text = " ".join(evidence_ids)
    return RunTrialResponse(
        full_trial_transcript=[
            TranscriptTurn(scene="opening", speaker_id="prosecution", text="Opening."),
            TranscriptTurn(
                scene="direct",
                speaker_id="witness",
                text=f"Direct testimony cites {evidence_text}.",
                cited_chunk_ids=evidence_ids,
            ),
            TranscriptTurn(scene="cross", speaker_id="defense", text="Cross."),
            TranscriptTurn(scene="closing", speaker_id="prosecution", text="Closing."),
            TranscriptTurn(
                scene="verdict",
                speaker_id="judge",
                text=f"Verdict relies on {fact_text}.",
                cited_chunk_ids=evidence_ids,
            ),
        ],
        run=RunMetadata(
            run_id=f"run-{request.case_file.case_id}",
            case_id=request.case_file.case_id,
            graph_version="v1",
            prompt_version="v1",
            model_name="gpt-4o-mini",
            judge_model_name="gpt-4o-mini",
            environment="test",
            deterministic_validation_passed=True,
            started_at="2026-01-01T00:00:00+00:00",
            completed_at="2026-01-01T00:00:01+00:00",
            duration_ms=1000,
        ),
    )


def passing_rubric_judge(_rubric_input):
    return {
        "scores": [
            RubricScore(
                dimension=dimension,
                score=0.95,
                threshold=0.0,
                passed=True,
                rationale=f"{dimension} passed.",
            )
            for dimension in [
                "legal_grounding",
                "procedural_realism",
                "role_adherence",
                "contradiction_handling",
                "verdict_support",
                "unsafe_content_handling",
            ]
        ],
        "rationale": "Rubric passed.",
        "token_usage": TokenUsage(
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
        ),
    }


def deterministic_failing_runner(request):
    response = fake_runner(request)
    response = response.model_copy(
        update={
            "run": response.run.model_copy(
                update={"deterministic_validation_passed": False}
            )
        }
    )
    exc = DeterministicValidationError(["final transcript turn must be the verdict"])
    exc.generated_output = response
    exc.node_telemetry = []
    raise exc


class BaselineWorkflowTest(unittest.TestCase):
    def test_baseline_report_shape(self) -> None:
        report = build_baseline_report(runner=fake_runner)

        self.assertEqual(report.dataset_version, "domain-eval-v1")
        self.assertEqual(report.graph_version, "v1")
        self.assertEqual(report.prompt_version, "v1")
        self.assertEqual(len(report.case_results), 3)
        self.assertEqual(report.aggregate_metrics.total_cases, 3)
        self.assertEqual(report.aggregate_metrics.deterministic_failed, 0)
        self.assertEqual(report.aggregate_metrics.deterministic_pass_rate, 1.0)
        self.assertEqual(report.aggregate_metrics.pass_rate, 0.0)
        self.assertEqual(report.aggregate_metrics.overall_pass_rate, 0.0)
        self.assertEqual(report.aggregate_metrics.rule_reference_failed, 3)
        self.assertIn("baseline_runner", report.evaluator_versions)
        self.assertEqual(
            report.case_results[0].evaluation_status["rubric"].state,
            "not_run",
        )

    def test_aggregate_metric_calculation(self) -> None:
        metrics = calculate_aggregate_metrics(
            [
                PerCaseEvaluationResult(
                    eval_case_id="a",
                    case_id="case-a",
                    deterministic_validation_passed=True,
                ),
                PerCaseEvaluationResult(
                    eval_case_id="b",
                    case_id="case-b",
                    deterministic_validation_passed=False,
                    failures=["bad transcript"],
                ),
            ]
        )

        self.assertEqual(metrics.total_cases, 2)
        self.assertEqual(metrics.deterministic_passed, 1)
        self.assertEqual(metrics.deterministic_failed, 1)
        self.assertEqual(metrics.pass_rate, 0.5)
        self.assertEqual(metrics.deterministic_pass_rate, 0.5)
        self.assertEqual(metrics.overall_pass_rate, 0.5)

    def test_timestamped_report_naming_is_unique(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir)
            first = build_report_path(output_dir, dataset_version="domain-eval-v1")
            second = build_report_path(output_dir, dataset_version="domain-eval-v1")

        self.assertNotEqual(first.name, second.name)
        self.assertTrue(first.name.startswith("baseline-domain-eval-v1-"))
        self.assertTrue(first.name.endswith(".json"))

    def test_report_can_be_serialized_to_json(self) -> None:
        report = build_baseline_report(runner=fake_runner)
        payload = json.loads(report.model_dump_json())

        self.assertEqual(payload["aggregate_metrics"]["total_cases"], 3)
        self.assertNotIn("generated_output", payload["case_results"][0])

    def test_report_writer_persists_generated_outputs(self) -> None:
        report = build_baseline_report(runner=rule_passing_runner)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = write_baseline_report(report, Path(tmp_dir))
            payload = json.loads(report_path.read_text())

            artifact_path = (
                Path(tmp_dir) / payload["case_results"][0]["generated_output_path"]
            )
            artifact = json.loads(artifact_path.read_text())

        self.assertTrue(artifact_path.name.startswith("eval-normal-ledger-theft-"))
        self.assertEqual(artifact["run"]["case_id"], "case-ledger-theft")
        self.assertEqual(artifact["full_trial_transcript"][-1]["scene"], "verdict")

    def test_report_writer_persists_deterministic_failure_outputs(self) -> None:
        report = build_baseline_report(runner=deterministic_failing_runner)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_path = write_baseline_report(report, Path(tmp_dir))
            payload = json.loads(report_path.read_text())

            first_result = payload["case_results"][0]
            artifact_path = Path(tmp_dir) / first_result["generated_output_path"]
            artifact = json.loads(artifact_path.read_text())

        self.assertFalse(first_result["deterministic_validation_passed"])
        self.assertTrue(artifact_path.name.startswith("eval-normal-ledger-theft-"))
        self.assertFalse(artifact["run"]["deterministic_validation_passed"])
        self.assertEqual(artifact["run"]["case_id"], "case-ledger-theft")

    def test_rubric_judge_runs_when_configured_and_rule_checks_pass(self) -> None:
        seen_inputs = []

        def tracking_judge(rubric_input):
            seen_inputs.append(rubric_input)
            return passing_rubric_judge(rubric_input)

        report = build_baseline_report(
            runner=rule_passing_runner,
            rubric_judge=tracking_judge,
        )

        self.assertEqual(len(seen_inputs), 3)
        self.assertTrue(
            all(
                result.evaluation_status["rubric"].state == "passed"
                for result in report.case_results
            )
        )
        self.assertTrue(
            all(len(result.rubric_results) == 1 for result in report.case_results)
        )

    def test_rubric_judge_token_usage_is_included_in_cost_estimate(self) -> None:
        report = build_baseline_report(
            runner=rule_passing_runner,
            rubric_judge=passing_rubric_judge,
            rubric_config=RubricEvaluatorConfig(judge_model="gpt-4o"),
        )

        rubric_usage = report.case_results[0].cost_estimate.node_usage[0]

        self.assertEqual(rubric_usage.node_name, "llm_rubric")
        self.assertEqual(rubric_usage.stage, "eval")
        self.assertEqual(rubric_usage.model_name, "gpt-4o")
        self.assertEqual(rubric_usage.call_count, 1)
        self.assertEqual(rubric_usage.token_usage.total_tokens, 120)
        self.assertEqual(str(rubric_usage.cost.total_cost_usd), "0.00045000")
        self.assertEqual(report.aggregate_metrics.llm_call_count, 3)
        self.assertEqual(report.aggregate_metrics.token_usage.total_tokens, 360)
        self.assertEqual(report.aggregate_metrics.estimated_total_cost_usd, 0.00135)

    def test_configured_rubric_skips_when_rule_checks_fail(self) -> None:
        report = build_baseline_report(
            runner=fake_runner,
            rubric_judge=passing_rubric_judge,
        )

        self.assertEqual(
            report.case_results[0].evaluation_status["rubric"].state,
            "skipped",
        )
        self.assertEqual(report.case_results[0].rubric_results, [])


if __name__ == "__main__":
    unittest.main()
