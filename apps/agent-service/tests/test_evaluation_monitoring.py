import unittest

from src.evaluation.evaluators import EvaluatorResult
from src.evaluation.monitoring import (
    GitHubIssueResult,
    SamplingPolicy,
    alerts_for_deterministic_failure,
    alerts_for_evaluator_results,
    queue_for_sampled_run,
    route_monitoring_records,
    should_sample,
    sync_queue_record_to_github,
)
from src.evaluation.rubric import RubricEvaluationResult, RubricScore
from src.utils.types import RunMetadata


def run_metadata():
    return RunMetadata(
        run_id="run-1",
        case_id="case-1",
        graph_version="v1",
        prompt_version="v1",
        model_name="gpt-4o-mini",
        judge_model_name="gpt-4o-mini",
        environment="test",
        deterministic_validation_passed=True,
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:01+00:00",
        duration_ms=1000,
    )


class FakeGitHubClient:
    def create_or_update_issue(self, record):
        return GitHubIssueResult(
            issue_number=42,
            issue_url=f"https://github.example/issues/{record.queue_id}",
            sync_status="created",
        )


class MonitoringTest(unittest.TestCase):
    def test_sampling_policy_percentage_and_tags(self) -> None:
        self.assertTrue(
            should_sample(
                policy=SamplingPolicy(sample_rate=0.25),
                tags=[],
                stable_bucket=0.1,
            )
        )
        self.assertFalse(
            should_sample(
                policy=SamplingPolicy(sample_rate=0.25),
                tags=[],
                stable_bucket=0.9,
            )
        )
        self.assertTrue(
            should_sample(
                policy=SamplingPolicy(sample_rate=0.0, tag_matches=["safety"]),
                tags=["safety"],
                stable_bucket=0.9,
            )
        )

    def test_sampled_run_routes_to_queue(self) -> None:
        records = queue_for_sampled_run(
            run=run_metadata(),
            tags=["baseline"],
            policy=SamplingPolicy(sample_rate=1.0),
        )

        self.assertEqual(records[0].route_reason, "sampled")
        self.assertEqual(records[0].status, "open")

    def test_failed_run_escalates_and_alerts(self) -> None:
        records = route_monitoring_records(
            run=run_metadata(), deterministic_failures=["missing verdict"]
        )
        alerts = alerts_for_deterministic_failure(
            run=run_metadata(), failures=["missing verdict"]
        )

        self.assertEqual(records[0].route_reason, "deterministic_failure")
        self.assertEqual(records[0].severity, "high")
        self.assertEqual(alerts[0].trigger_name, "deterministic_validation_failed")
        self.assertEqual(alerts[0].run_id, "run-1")

    def test_high_severity_rule_failure_routes_and_alerts(self) -> None:
        result = EvaluatorResult(
            evaluator_name="evidence_reference",
            passed=False,
            severity="high",
            summary="Unsupported evidence reference.",
        )

        records = route_monitoring_records(run=run_metadata(), rule_results=[result])
        alerts = alerts_for_evaluator_results(run=run_metadata(), results=[result])

        self.assertEqual(records[0].route_reason, "rule_reference_failure")
        self.assertEqual(alerts[0].trigger_name, "severe_evaluator_failure")

    def test_low_severity_alert_suppression(self) -> None:
        result = EvaluatorResult(
            evaluator_name="phase_coverage",
            passed=False,
            severity="low",
            summary="Minor issue.",
        )

        self.assertEqual(alerts_for_evaluator_results(run=run_metadata(), results=[result]), [])

    def test_rubric_threshold_failure_routes_to_queue(self) -> None:
        rubric_result = RubricEvaluationResult(
            evaluator_model="gpt-4o",
            evaluator_prompt_version="v1",
            passed=False,
            scores=[
                RubricScore(
                    dimension="legal_grounding",
                    score=0.1,
                    threshold=0.75,
                    passed=False,
                    rationale="Weak support.",
                )
            ],
            latency_ms=5,
            rationale="Weak support.",
        )

        records = route_monitoring_records(
            run=run_metadata(), rubric_results=[rubric_result]
        )

        self.assertEqual(records[0].route_reason, "rubric_threshold_failure")

    def test_github_issue_sync_metadata(self) -> None:
        record = route_monitoring_records(
            run=run_metadata(), deterministic_failures=["missing verdict"]
        )[0]

        synced = sync_queue_record_to_github(record, FakeGitHubClient())

        self.assertEqual(synced.status, "synced")
        self.assertEqual(synced.github.provider, "github")
        self.assertEqual(synced.github.issue_number, 42)
        self.assertEqual(synced.github.sync_status, "created")
        self.assertTrue(synced.github.last_sync_at)


if __name__ == "__main__":
    unittest.main()
