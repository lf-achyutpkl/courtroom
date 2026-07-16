from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Protocol

from courtroom_domain import NodeTelemetry
from pydantic import BaseModel, Field

from src.evaluation.evaluators import EvaluatorResult, Severity
from src.evaluation.rubric import RubricEvaluationResult
from src.utils.types import RunMetadata

QueueReason = Literal[
    "sampled",
    "deterministic_failure",
    "rule_reference_failure",
    "rubric_threshold_failure",
    "alert_worthy",
]
QueueStatus = Literal["open", "synced", "closed"]
SyncStatus = Literal["not_synced", "created", "updated", "failed"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class GitHubIssueTracking(BaseModel):
    provider: Literal["github"] | None = None
    issue_number: int | None = None
    issue_url: str | None = None
    sync_status: SyncStatus = "not_synced"
    last_sync_at: str | None = None


class QueueRecord(BaseModel):
    queue_id: str
    run_id: str | None = None
    case_id: str | None = None
    route_reason: QueueReason
    severity: Severity
    source_evaluator: str
    evidence_summary: str
    created_at: str = Field(default_factory=utc_now_iso)
    status: QueueStatus = "open"
    github: GitHubIssueTracking = Field(default_factory=GitHubIssueTracking)


class SamplingPolicy(BaseModel):
    sample_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    tag_matches: list[str] = Field(default_factory=list)


class AlertRecord(BaseModel):
    alert_id: str
    run_id: str | None = None
    severity: Severity
    trigger_name: str
    source: str
    summary: str
    created_at: str = Field(default_factory=utc_now_iso)
    routing_target: str


class GitHubIssueResult(BaseModel):
    issue_number: int
    issue_url: str
    sync_status: Literal["created", "updated"]


class GitHubIssueClient(Protocol):
    def create_or_update_issue(self, record: QueueRecord) -> GitHubIssueResult: ...


def should_sample(
    *,
    policy: SamplingPolicy,
    tags: list[str],
    stable_bucket: float = 0.0,
) -> bool:
    if set(policy.tag_matches).intersection(tags):
        return True
    return stable_bucket < policy.sample_rate


def queue_for_sampled_run(
    *,
    run: RunMetadata,
    tags: list[str],
    policy: SamplingPolicy,
    stable_bucket: float = 0.0,
) -> list[QueueRecord]:
    if not should_sample(policy=policy, tags=tags, stable_bucket=stable_bucket):
        return []
    return [
        QueueRecord(
            queue_id=f"queue-{run.run_id}-sampled",
            run_id=run.run_id,
            case_id=run.case_id,
            route_reason="sampled",
            severity="low",
            source_evaluator="sampling_policy",
            evidence_summary="Run selected for annotation review by sampling policy.",
        )
    ]


def route_monitoring_records(
    *,
    run: RunMetadata | None,
    deterministic_failures: list[str] | None = None,
    rule_results: list[EvaluatorResult] | None = None,
    rubric_results: list[RubricEvaluationResult] | None = None,
    sampled: bool = False,
) -> list[QueueRecord]:
    records: list[QueueRecord] = []
    run_id = run.run_id if run else None
    case_id = run.case_id if run else None

    if deterministic_failures:
        records.append(
            QueueRecord(
                queue_id=f"queue-{run_id or 'unknown'}-deterministic",
                run_id=run_id,
                case_id=case_id,
                route_reason="deterministic_failure",
                severity="high",
                source_evaluator="deterministic_validation",
                evidence_summary="; ".join(deterministic_failures),
            )
        )

    for result in rule_results or []:
        if not result.passed and result.severity in {"high", "critical"}:
            records.append(
                QueueRecord(
                    queue_id=f"queue-{run_id or 'unknown'}-{result.evaluator_name}",
                    run_id=run_id,
                    case_id=case_id,
                    route_reason="rule_reference_failure",
                    severity=result.severity,
                    source_evaluator=result.evaluator_name,
                    evidence_summary=result.summary,
                )
            )

    for result in rubric_results or []:
        if not result.passed:
            records.append(
                QueueRecord(
                    queue_id=f"queue-{run_id or 'unknown'}-rubric",
                    run_id=run_id,
                    case_id=case_id,
                    route_reason="rubric_threshold_failure",
                    severity="medium",
                    source_evaluator=result.evaluator_name,
                    evidence_summary=result.rationale,
                )
            )

    if sampled:
        records.append(
            QueueRecord(
                queue_id=f"queue-{run_id or 'unknown'}-sampled",
                run_id=run_id,
                case_id=case_id,
                route_reason="sampled",
                severity="low",
                source_evaluator="sampling_policy",
                evidence_summary="Run selected for sampled annotation review.",
            )
        )

    return records


def sync_queue_record_to_github(
    record: QueueRecord,
    client: GitHubIssueClient,
) -> QueueRecord:
    result = client.create_or_update_issue(record)
    return record.model_copy(
        update={
            "status": "synced",
            "github": GitHubIssueTracking(
                provider="github",
                issue_number=result.issue_number,
                issue_url=result.issue_url,
                sync_status=result.sync_status,
                last_sync_at=utc_now_iso(),
            ),
        }
    )


def alerts_for_deterministic_failure(
    *,
    run: RunMetadata | None,
    failures: list[str],
) -> list[AlertRecord]:
    if not failures:
        return []
    run_id = run.run_id if run else None
    return [
        AlertRecord(
            alert_id=f"alert-{run_id or 'unknown'}-deterministic",
            run_id=run_id,
            severity="high",
            trigger_name="deterministic_validation_failed",
            source="deterministic_validation",
            summary="; ".join(failures),
            routing_target="evaluation-escalations",
        )
    ]


def alerts_for_evaluator_results(
    *,
    run: RunMetadata | None,
    results: list[EvaluatorResult],
) -> list[AlertRecord]:
    alerts: list[AlertRecord] = []
    run_id = run.run_id if run else None
    for result in results:
        if result.passed or result.severity not in {"high", "critical"}:
            continue
        alerts.append(
            AlertRecord(
                alert_id=f"alert-{run_id or 'unknown'}-{result.evaluator_name}",
                run_id=run_id,
                severity=result.severity,
                trigger_name="severe_evaluator_failure",
                source=result.evaluator_name,
                summary=result.summary,
                routing_target="evaluation-escalations",
            )
        )
    return alerts


def alerts_for_missing_trace_metadata(run: RunMetadata) -> list[AlertRecord]:
    if run.langsmith_trace_id:
        return []
    return [
        AlertRecord(
            alert_id=f"alert-{run.run_id}-missing-trace",
            run_id=run.run_id,
            severity="medium",
            trigger_name="missing_trace_metadata",
            source="monitoring_validation",
            summary="Run is missing langsmith_trace_id.",
            routing_target="observability-review",
        )
    ]


def alerts_for_node_telemetry(
    *,
    run: RunMetadata,
    telemetry: list[NodeTelemetry],
) -> list[AlertRecord]:
    missing = [
        record.node_name
        for record in telemetry
        if record.duration_ms is None
        or (
            record.prompt_tokens is None
            and record.completion_tokens is None
            and record.total_tokens is None
        )
    ]
    if not missing:
        return []
    return [
        AlertRecord(
            alert_id=f"alert-{run.run_id}-node-telemetry",
            run_id=run.run_id,
            severity="medium",
            trigger_name="missing_node_token_or_latency_telemetry",
            source="node_telemetry",
            summary="Missing token or latency telemetry for: " + ", ".join(missing),
            routing_target="observability-review",
        )
    ]
