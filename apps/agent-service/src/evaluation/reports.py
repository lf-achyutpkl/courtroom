from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.evaluation.costs import CostEstimateSummary, TokenUsageSummary
from src.utils.types import RunMetadata, RunTrialResponse

EvaluationStageState = Literal["passed", "failed", "skipped", "not_run"]


class EvaluationStageStatus(BaseModel):
    state: EvaluationStageState
    reason: str | None = None
    result_count: int = 0


class PerCaseEvaluationResult(BaseModel):
    eval_case_id: str
    case_id: str
    run_id: str | None = None
    deterministic_validation_passed: bool
    run: RunMetadata | None = None
    evaluation_status: dict[str, EvaluationStageStatus] = Field(default_factory=dict)
    evaluator_results: list[Any] = Field(default_factory=list)
    rubric_results: list[Any] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    queue_decisions: list[Any] = Field(default_factory=list)
    alert_summaries: list[Any] = Field(default_factory=list)
    cost_estimate: CostEstimateSummary | None = None
    generated_output_path: str | None = None
    generated_output: RunTrialResponse | None = Field(default=None, exclude=True)


class AggregateMetrics(BaseModel):
    total_cases: int
    overall_passed: int = 0
    overall_failed: int = 0
    deterministic_passed: int
    deterministic_failed: int
    rule_reference_passed: int = 0
    rule_reference_failed: int = 0
    rule_reference_skipped: int = 0
    rubric_passed: int = 0
    rubric_failed: int = 0
    rubric_skipped: int = 0
    rubric_not_run: int = 0
    queued_cases: int = 0
    alert_cases: int = 0
    pass_rate: float
    deterministic_pass_rate: float = 0.0
    overall_pass_rate: float = 0.0
    llm_call_count: int = 0
    token_usage: TokenUsageSummary = Field(default_factory=TokenUsageSummary)
    estimated_total_cost_usd: float | None = None
    unpriced_models: list[str] = Field(default_factory=list)


class BaselineReport(BaseModel, frozen=True):
    report_id: str
    dataset_version: str
    graph_version: str
    prompt_version: str
    model_names: dict[str, str]
    evaluator_versions: dict[str, str]
    case_results: list[PerCaseEvaluationResult]
    aggregate_metrics: AggregateMetrics
    created_at: str


def utc_timestamp_for_filename(now: datetime | None = None) -> str:
    value = now or datetime.now(timezone.utc)
    return value.strftime("%Y%m%dT%H%M%S%fZ")


def build_report_path(
    output_dir: Path,
    *,
    dataset_version: str,
    now: datetime | None = None,
) -> Path:
    timestamp = utc_timestamp_for_filename(now)
    return output_dir / f"baseline-{dataset_version}-{timestamp}.json"


def write_baseline_report(report: BaselineReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = build_report_path(output_dir, dataset_version=report.dataset_version)
    artifact_dir = output_dir / path.stem / "outputs"
    case_results = []
    for result in report.case_results:
        output = result.generated_output
        if output is None:
            case_results.append(result)
            continue

        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / f"{result.eval_case_id}-{output.run.run_id}.json"
        artifact_path.write_text(output.model_dump_json(indent=2) + "\n")
        case_results.append(
            result.model_copy(
                update={
                    "generated_output_path": str(artifact_path.relative_to(output_dir)),
                }
            )
        )

    report_with_artifacts = report.model_copy(update={"case_results": case_results})
    path.write_text(report_with_artifacts.model_dump_json(indent=2) + "\n")
    return path
