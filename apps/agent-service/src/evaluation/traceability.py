from __future__ import annotations

from pydantic import BaseModel, Field

from courtroom_domain import NodeTelemetry
from src.utils.types import RunMetadata


class EvaluationContext(BaseModel):
    dataset_version: str | None = None
    eval_case_id: str | None = None
    evaluator_versions: dict[str, str] = Field(default_factory=dict)


class ExportedRunRecord(BaseModel):
    run_id: str
    case_id: str
    graph_version: str
    prompt_version: str
    model_names: dict[str, str]
    environment: str
    started_at: str
    completed_at: str
    deterministic_validation_passed: bool
    evaluation_context: EvaluationContext | None = None


class ExportedNodeSpan(BaseModel):
    node_name: str
    stage: str
    duration_ms: int
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    parse_success: bool | None = None
    error_type: str | None = None


def export_run_record(
    run: RunMetadata,
    *,
    evaluation_context: EvaluationContext | None = None,
) -> ExportedRunRecord:
    return ExportedRunRecord(
        run_id=run.run_id,
        case_id=run.case_id,
        graph_version=run.graph_version,
        prompt_version=run.prompt_version,
        model_names={
            "runtime": run.model_name,
            "judge": run.judge_model_name,
        },
        environment=run.environment,
        started_at=run.started_at,
        completed_at=run.completed_at,
        deterministic_validation_passed=run.deterministic_validation_passed,
        evaluation_context=evaluation_context,
    )


def export_node_spans(telemetry: list[NodeTelemetry]) -> list[ExportedNodeSpan]:
    return [
        ExportedNodeSpan(
            node_name=record.node_name,
            stage=record.stage,
            duration_ms=record.duration_ms,
            latency_ms=record.duration_ms,
            prompt_tokens=record.prompt_tokens,
            completion_tokens=record.completion_tokens,
            total_tokens=record.total_tokens,
            parse_success=record.parse_success,
            error_type=record.error_type,
        )
        for record in telemetry
    ]
