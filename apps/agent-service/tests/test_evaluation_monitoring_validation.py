import unittest

from src.evaluation.evaluators import EvaluatorResult
from src.evaluation.monitoring import (
    alerts_for_deterministic_failure,
    alerts_for_evaluator_results,
    route_monitoring_records,
)
from src.evaluation.reports import AggregateMetrics, BaselineReport, PerCaseEvaluationResult
from src.evaluation.traceability import (
    EvaluationContext,
    export_node_spans,
    export_run_record,
)
from src.utils.types import NodeTelemetry, RunMetadata


def run_metadata(deterministic_valid=True):
    return RunMetadata(
        run_id="run-1",
        case_id="case-1",
        graph_version="v1",
        prompt_version="v1",
        model_name="gpt-4o-mini",
        judge_model_name="gpt-4o",
        environment="test",
        deterministic_validation_passed=deterministic_valid,
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
    )


class MonitoringValidationTest(unittest.TestCase):
    def test_exported_run_record_includes_required_metadata(self) -> None:
        record = export_run_record(
            run_metadata(),
            evaluation_context=EvaluationContext(
                dataset_version="domain-eval-v1",
                eval_case_id="eval-1",
                evaluator_versions={"baseline": "v1"},
            ),
        )

        self.assertEqual(record.run_id, "run-1")
        self.assertEqual(record.case_id, "case-1")
        self.assertEqual(record.graph_version, "v1")
        self.assertEqual(record.prompt_version, "v1")
        self.assertEqual(record.model_names["runtime"], "gpt-4o-mini")
        self.assertEqual(record.model_names["judge"], "gpt-4o")
        self.assertEqual(record.environment, "test")
        self.assertTrue(record.started_at)
        self.assertTrue(record.completed_at)
        self.assertTrue(record.deterministic_validation_passed)
        self.assertEqual(record.evaluation_context.dataset_version, "domain-eval-v1")

    def test_node_spans_include_latency_tokens_parse_and_error_fields(self) -> None:
        spans = export_node_spans(
            [
                NodeTelemetry(
                    node_name="verdict",
                    stage="trial",
                    started_at="2026-01-01T00:00:00+00:00",
                    completed_at="2026-01-01T00:00:01+00:00",
                    duration_ms=1000,
                    prompt_tokens=20,
                    completion_tokens=10,
                    total_tokens=30,
                    parse_success=True,
                    error_type=None,
                )
            ]
        )

        self.assertEqual(spans[0].node_name, "verdict")
        self.assertEqual(spans[0].stage, "trial")
        self.assertEqual(spans[0].duration_ms, 1000)
        self.assertEqual(spans[0].latency_ms, 1000)
        self.assertEqual(spans[0].total_tokens, 30)
        self.assertTrue(spans[0].parse_success)
        self.assertIsNone(spans[0].error_type)

    def test_failed_runs_and_threshold_failures_create_queue_and_alerts(self) -> None:
        failed_run = run_metadata(deterministic_valid=False)
        deterministic_records = route_monitoring_records(
            run=failed_run, deterministic_failures=["bad run"]
        )
        deterministic_alerts = alerts_for_deterministic_failure(
            run=failed_run, failures=["bad run"]
        )
        threshold_result = EvaluatorResult(
            evaluator_name="verdict_support",
            passed=False,
            severity="high",
            summary="Verdict lacked support.",
        )
        threshold_records = route_monitoring_records(
            run=run_metadata(), rule_results=[threshold_result]
        )
        threshold_alerts = alerts_for_evaluator_results(
            run=run_metadata(), results=[threshold_result]
        )

        self.assertEqual(deterministic_records[0].route_reason, "deterministic_failure")
        self.assertEqual(deterministic_alerts[0].trigger_name, "deterministic_validation_failed")
        self.assertEqual(threshold_records[0].route_reason, "rule_reference_failure")
        self.assertEqual(threshold_alerts[0].trigger_name, "severe_evaluator_failure")

    def test_baseline_report_includes_queue_decisions_and_alert_summaries(self) -> None:
        queue_records = route_monitoring_records(
            run=run_metadata(), deterministic_failures=["bad run"]
        )
        alerts = alerts_for_deterministic_failure(
            run=run_metadata(), failures=["bad run"]
        )
        report = BaselineReport(
            report_id="baseline-test",
            dataset_version="domain-eval-v1",
            graph_version="v1",
            prompt_version="v1",
            model_names={"runtime": "gpt-4o-mini", "judge": "gpt-4o"},
            evaluator_versions={"baseline": "v1"},
            case_results=[
                PerCaseEvaluationResult(
                    eval_case_id="eval-1",
                    case_id="case-1",
                    run_id="run-1",
                    deterministic_validation_passed=False,
                    failures=["bad run"],
                    queue_decisions=queue_records,
                    alert_summaries=alerts,
                )
            ],
            aggregate_metrics=AggregateMetrics(
                total_cases=1,
                deterministic_passed=0,
                deterministic_failed=1,
                queued_cases=1,
                alert_cases=1,
                pass_rate=0.0,
            ),
            created_at="2026-01-01T00:00:00+00:00",
        )

        self.assertEqual(report.case_results[0].queue_decisions[0].route_reason, "deterministic_failure")
        self.assertEqual(report.case_results[0].alert_summaries[0].routing_target, "evaluation-escalations")


if __name__ == "__main__":
    unittest.main()
