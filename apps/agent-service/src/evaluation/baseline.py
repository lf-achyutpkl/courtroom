from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Callable

from courtroom_domain import NodeTelemetry

from src.evaluation.costs import (
    DEFAULT_MODEL_TOKEN_RATES,
    CostEstimateSummary,
    NodeUsageSummary,
    TokenUsageSummary,
    build_cost_estimate_summary,
    combine_cost_estimate_summaries,
    estimate_cost,
)
from src.evaluation.dataset import EvaluationCase, load_dataset
from src.evaluation.evaluators import evaluate_rule_reference
from src.evaluation.monitoring import (
    alerts_for_deterministic_failure,
    alerts_for_evaluator_results,
    alerts_for_missing_trace_metadata,
    alerts_for_node_telemetry,
    route_monitoring_records,
)
from src.evaluation.reports import (
    AggregateMetrics,
    BaselineReport,
    EvaluationStageStatus,
    PerCaseEvaluationResult,
    write_baseline_report,
)
from src.evaluation.rubric import (
    DEFAULT_JUDGE_MODEL,
    JudgeCallable,
    RubricEvaluationResult,
    RubricEvaluatorConfig,
    build_openai_rubric_judge,
    evaluate_rubric,
)
from src.service import _run_trial_with_state
from src.utils.config import TRIAL_CONFIG
from src.utils.types import RunTrialRequest, RunTrialResponse
from src.utils.validation import DeterministicValidationError

DEFAULT_REPORT_DIR = Path(__file__).resolve().parents[2] / "evals" / "reports"
BASELINE_EVALUATOR_VERSIONS = {
    "baseline_runner": "v1",
    "rule_reference": "v1",
    "monitoring": "v1",
    "cost_estimate": "v1",
}

TrialRunnerResult = RunTrialResponse | tuple[RunTrialResponse, list[NodeTelemetry]]
TrialRunner = Callable[[RunTrialRequest], TrialRunnerResult]
ProgressReporter = Callable[[str], None]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_eval_runner(request: RunTrialRequest) -> TrialRunnerResult:
    response, state = _run_trial_with_state(request)
    return response, state.node_telemetry


def _normalize_runner_result(
    result: TrialRunnerResult,
) -> tuple[RunTrialResponse, list[NodeTelemetry]]:
    if isinstance(result, tuple):
        response, telemetry = result
        return response, telemetry
    return result, []


def _stage_status(
    *,
    ran: bool,
    passed: bool = True,
    result_count: int = 0,
    reason: str | None = None,
) -> EvaluationStageStatus:
    if not ran:
        return EvaluationStageStatus(
            state="not_run",
            reason=reason,
            result_count=result_count,
        )
    return EvaluationStageStatus(
        state="passed" if passed else "failed",
        reason=reason,
        result_count=result_count,
    )


def _build_rubric_cost_estimate(
    rubric_results: list[RubricEvaluationResult],
) -> CostEstimateSummary:
    priced_node_usage = []
    unpriced_models = set()
    total_cost = Decimal("0")

    for result in rubric_results:
        usage = result.token_usage
        usage_summary = TokenUsageSummary(
            prompt_tokens=(usage.prompt_tokens or 0) if usage is not None else 0,
            completion_tokens=(usage.completion_tokens or 0)
            if usage is not None
            else 0,
            total_tokens=(usage.total_tokens or 0) if usage is not None else 0,
            missing_usage_records=1 if usage is None else 0,
        )
        rate = DEFAULT_MODEL_TOKEN_RATES.get(result.evaluator_model)
        cost = estimate_cost(usage_summary, rate) if rate is not None else None
        if cost is not None:
            total_cost += cost.total_cost_usd
        else:
            unpriced_models.add(result.evaluator_model)

        priced_node_usage.append(
            NodeUsageSummary(
                node_name=result.evaluator_name,
                stage="eval",
                model_name=result.evaluator_model,
                call_count=1,
                duration_ms=result.latency_ms,
                token_usage=usage_summary,
                cost=cost,
            )
        )

    return CostEstimateSummary(
        pricing_source="local_static_rates_openai_pricing_snapshot",
        model_rates=DEFAULT_MODEL_TOKEN_RATES,
        token_usage=TokenUsageSummary(
            prompt_tokens=sum(
                node.token_usage.prompt_tokens for node in priced_node_usage
            ),
            completion_tokens=sum(
                node.token_usage.completion_tokens for node in priced_node_usage
            ),
            total_tokens=sum(
                node.token_usage.total_tokens for node in priced_node_usage
            ),
            missing_usage_records=sum(
                node.token_usage.missing_usage_records for node in priced_node_usage
            ),
        ),
        total_cost_usd=total_cost,
        unpriced_models=sorted(unpriced_models),
        node_usage=priced_node_usage,
    )


def _run_case(
    case: EvaluationCase,
    runner: TrialRunner,
    *,
    rubric_judge: JudgeCallable | None = None,
    rubric_config: RubricEvaluatorConfig | None = None,
) -> PerCaseEvaluationResult:
    try:
        response, telemetry = _normalize_runner_result(
            runner(RunTrialRequest(case_file=case.case_file))
        )
    except DeterministicValidationError as exc:
        failures = exc.errors
        generated_output = exc.generated_output
        run = generated_output.run if generated_output is not None else None
        telemetry = exc.node_telemetry
        return PerCaseEvaluationResult(
            eval_case_id=case.eval_case_id,
            case_id=case.case_file.case_id,
            run_id=run.run_id if run is not None else None,
            deterministic_validation_passed=False,
            run=run,
            evaluation_status={
                "deterministic": EvaluationStageStatus(
                    state="failed",
                    reason="deterministic validation failed",
                    result_count=len(failures),
                ),
                "rule_reference": _stage_status(
                    ran=False,
                    reason="skipped because deterministic validation failed",
                ),
                "rubric": (
                    EvaluationStageStatus(
                        state="skipped",
                        reason="skipped because deterministic validation failed",
                    )
                    if rubric_judge is not None
                    else _stage_status(
                        ran=False,
                        reason="no rubric judge configured for baseline CLI",
                    )
                ),
                "monitoring": _stage_status(ran=True, passed=False),
            },
            failures=failures,
            queue_decisions=route_monitoring_records(
                run=run,
                deterministic_failures=failures,
            ),
            alert_summaries=alerts_for_deterministic_failure(
                run=run,
                failures=failures,
            ),
            cost_estimate=build_cost_estimate_summary(telemetry),
            generated_output=generated_output,
        )
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
        return PerCaseEvaluationResult(
            eval_case_id=case.eval_case_id,
            case_id=case.case_file.case_id,
            deterministic_validation_passed=False,
            evaluation_status={
                "deterministic": EvaluationStageStatus(
                    state="failed",
                    reason="trial runner raised an exception",
                    result_count=1,
                ),
                "rule_reference": _stage_status(
                    ran=False,
                    reason="skipped because trial runner failed",
                ),
                "rubric": (
                    EvaluationStageStatus(
                        state="skipped",
                        reason="skipped because trial runner failed",
                    )
                    if rubric_judge is not None
                    else _stage_status(
                        ran=False,
                        reason="no rubric judge configured for baseline CLI",
                    )
                ),
                "monitoring": _stage_status(ran=True, passed=False),
            },
            failures=[failure],
            queue_decisions=route_monitoring_records(
                run=None,
                deterministic_failures=[failure],
            ),
            alert_summaries=alerts_for_deterministic_failure(
                run=None,
                failures=[failure],
            ),
        )

    rule_results = evaluate_rule_reference(response=response, case=case)
    rule_passed = all(result.passed for result in rule_results)
    rubric_results = (
        evaluate_rubric(
            response=response,
            reference=case.reference,
            judge=rubric_judge,
            config=rubric_config,
            prerequisite_results=rule_results,
        )
        if rubric_judge is not None
        else []
    )
    rubric_passed = all(result.passed for result in rubric_results)
    queue_decisions = route_monitoring_records(
        run=response.run,
        rule_results=rule_results,
        rubric_results=rubric_results,
    )
    alert_summaries = [
        *alerts_for_evaluator_results(run=response.run, results=rule_results),
        *alerts_for_missing_trace_metadata(response.run),
        *alerts_for_node_telemetry(run=response.run, telemetry=telemetry),
    ]
    cost_estimate = combine_cost_estimate_summaries(
        [
            build_cost_estimate_summary(telemetry),
            _build_rubric_cost_estimate(rubric_results),
        ]
    )

    return PerCaseEvaluationResult(
        eval_case_id=case.eval_case_id,
        case_id=case.case_file.case_id,
        run_id=response.run.run_id,
        deterministic_validation_passed=response.run.deterministic_validation_passed,
        run=response.run,
        evaluation_status={
            "deterministic": _stage_status(
                ran=True,
                passed=response.run.deterministic_validation_passed,
                result_count=1,
            ),
            "rule_reference": _stage_status(
                ran=True,
                passed=rule_passed,
                result_count=len(rule_results),
            ),
            "rubric": (
                _stage_status(
                    ran=True,
                    passed=rubric_passed,
                    result_count=len(rubric_results),
                )
                if rubric_results
                else (
                    EvaluationStageStatus(
                        state="skipped",
                        reason="skipped because rule/reference checks failed",
                    )
                    if rubric_judge is not None
                    else _stage_status(
                        ran=False,
                        reason="no rubric judge configured for baseline CLI",
                    )
                )
            ),
            "monitoring": _stage_status(
                ran=True,
                passed=not queue_decisions and not alert_summaries,
                result_count=len(queue_decisions) + len(alert_summaries),
            ),
        },
        evaluator_results=rule_results,
        rubric_results=rubric_results,
        queue_decisions=queue_decisions,
        alert_summaries=alert_summaries,
        cost_estimate=cost_estimate,
        generated_output=response,
    )


def calculate_aggregate_metrics(
    case_results: list[PerCaseEvaluationResult],
) -> AggregateMetrics:
    total_cases = len(case_results)
    deterministic_passed = sum(
        1 for result in case_results if result.deterministic_validation_passed
    )
    rule_reference_passed = sum(
        1
        for result in case_results
        if result.evaluation_status.get("rule_reference")
        and result.evaluation_status["rule_reference"].state == "passed"
    )
    rule_reference_failed = sum(
        1
        for result in case_results
        if result.evaluation_status.get("rule_reference")
        and result.evaluation_status["rule_reference"].state == "failed"
    )
    rule_reference_skipped = sum(
        1
        for result in case_results
        if result.evaluation_status.get("rule_reference")
        and result.evaluation_status["rule_reference"].state == "skipped"
    )
    rubric_passed = sum(
        1
        for result in case_results
        if result.evaluation_status.get("rubric")
        and result.evaluation_status["rubric"].state == "passed"
    )
    rubric_failed = sum(
        1
        for result in case_results
        if result.evaluation_status.get("rubric")
        and result.evaluation_status["rubric"].state == "failed"
    )
    rubric_skipped = sum(
        1
        for result in case_results
        if result.evaluation_status.get("rubric")
        and result.evaluation_status["rubric"].state == "skipped"
    )
    rubric_not_run = sum(
        1
        for result in case_results
        if result.evaluation_status.get("rubric")
        and result.evaluation_status["rubric"].state == "not_run"
    )
    queued_cases = sum(1 for result in case_results if result.queue_decisions)
    alert_cases = sum(1 for result in case_results if result.alert_summaries)
    token_usage = sum_cost_estimate_tokens(case_results)
    estimated_total_cost = sum(
        float(result.cost_estimate.total_cost_usd or 0)
        for result in case_results
        if result.cost_estimate is not None
    )
    unpriced_models = sorted(
        {
            model
            for result in case_results
            if result.cost_estimate is not None
            for model in result.cost_estimate.unpriced_models
        }
    )

    overall_passed = sum(
        1
        for result in case_results
        if result.deterministic_validation_passed
        and (
            not result.evaluation_status.get("rule_reference")
            or result.evaluation_status["rule_reference"].state == "passed"
        )
        and (
            not result.evaluation_status.get("rubric")
            or result.evaluation_status["rubric"].state in {"passed", "not_run"}
        )
    )
    deterministic_pass_rate = deterministic_passed / total_cases if total_cases else 0.0
    overall_pass_rate = overall_passed / total_cases if total_cases else 0.0

    return AggregateMetrics(
        total_cases=total_cases,
        overall_passed=overall_passed,
        overall_failed=total_cases - overall_passed,
        deterministic_passed=deterministic_passed,
        deterministic_failed=total_cases - deterministic_passed,
        rule_reference_passed=rule_reference_passed,
        rule_reference_failed=rule_reference_failed,
        rule_reference_skipped=rule_reference_skipped,
        rubric_passed=rubric_passed,
        rubric_failed=rubric_failed,
        rubric_skipped=rubric_skipped,
        rubric_not_run=rubric_not_run,
        queued_cases=queued_cases,
        alert_cases=alert_cases,
        pass_rate=overall_pass_rate,
        deterministic_pass_rate=deterministic_pass_rate,
        overall_pass_rate=overall_pass_rate,
        llm_call_count=sum(
            sum(node.call_count for node in result.cost_estimate.node_usage)
            for result in case_results
            if result.cost_estimate is not None
        ),
        token_usage=token_usage,
        estimated_total_cost_usd=estimated_total_cost,
        unpriced_models=unpriced_models,
    )


def sum_cost_estimate_tokens(
    case_results: list[PerCaseEvaluationResult],
) -> TokenUsageSummary:
    return TokenUsageSummary(
        prompt_tokens=sum(
            result.cost_estimate.token_usage.prompt_tokens
            for result in case_results
            if result.cost_estimate is not None
        ),
        completion_tokens=sum(
            result.cost_estimate.token_usage.completion_tokens
            for result in case_results
            if result.cost_estimate is not None
        ),
        total_tokens=sum(
            result.cost_estimate.token_usage.total_tokens
            for result in case_results
            if result.cost_estimate is not None
        ),
        cached_tokens=sum(
            result.cost_estimate.token_usage.cached_tokens
            for result in case_results
            if result.cost_estimate is not None
        ),
        cache_write_tokens=sum(
            result.cost_estimate.token_usage.cache_write_tokens
            for result in case_results
            if result.cost_estimate is not None
        ),
        missing_usage_records=sum(
            result.cost_estimate.token_usage.missing_usage_records
            for result in case_results
            if result.cost_estimate is not None
        ),
    )


def build_baseline_report(
    *,
    runner: TrialRunner = _default_eval_runner,
    rubric_judge: JudgeCallable | None = None,
    rubric_config: RubricEvaluatorConfig | None = None,
    progress: ProgressReporter | None = None,
) -> BaselineReport:
    dataset = load_dataset()
    active_cases = dataset.active_cases
    if progress is not None:
        progress(f"Running baseline evaluation ({len(active_cases)} cases).")

    case_results = []
    for index, case in enumerate(active_cases, start=1):
        if progress is not None:
            progress(f"[{index}/{len(active_cases)}] Evaluating {case.eval_case_id}...")
        case_results.append(
            _run_case(
                case,
                runner,
                rubric_judge=rubric_judge,
                rubric_config=rubric_config,
            )
        )
    model_names = {
        "runtime": "not_observed",
        "judge": "not_observed",
    }
    for result in case_results:
        if result.run is not None:
            model_names = {
                "runtime": result.run.model_name,
                "judge": result.run.judge_model_name,
            }
            break

    return BaselineReport(
        report_id=f"baseline-{dataset.dataset_version}-{_utc_now_iso()}",
        dataset_version=dataset.dataset_version,
        graph_version=TRIAL_CONFIG.graph_version,
        prompt_version=TRIAL_CONFIG.prompt_version,
        model_names=model_names,
        evaluator_versions=BASELINE_EVALUATOR_VERSIONS,
        case_results=case_results,
        aggregate_metrics=calculate_aggregate_metrics(case_results),
        created_at=_utc_now_iso(),
    )


def run_baseline(
    *,
    output_dir: Path = DEFAULT_REPORT_DIR,
    runner: TrialRunner = _default_eval_runner,
    rubric_judge: JudgeCallable | None = None,
    rubric_config: RubricEvaluatorConfig | None = None,
    progress: ProgressReporter | None = None,
) -> Path:
    report = build_baseline_report(
        runner=runner,
        rubric_judge=rubric_judge,
        rubric_config=rubric_config,
        progress=progress,
    )
    if progress is not None:
        progress("Writing baseline report...")
    return write_baseline_report(report, output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the baseline eval dataset.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help="Directory where timestamped baseline reports are written.",
    )
    parser.add_argument(
        "--enable-rubric",
        action="store_true",
        help="Run the OpenAI LLM-as-judge rubric after rule/reference checks pass.",
    )
    parser.add_argument(
        "--rubric-judge-model",
        default=DEFAULT_JUDGE_MODEL,
        help="OpenAI model to use for rubric judging when --enable-rubric is set.",
    )
    args = parser.parse_args()
    rubric_config = None
    rubric_judge = None
    if args.enable_rubric:
        print(
            f"Preparing rubric judge ({args.rubric_judge_model})...",
            flush=True,
        )
        print(
            "Rubric judge LLM calls: "
            f"model={args.rubric_judge_model}, "
            f"max={len(load_dataset().active_cases)} "
            "(one per case after rule/reference checks pass).",
            flush=True,
        )
        rubric_config = RubricEvaluatorConfig(judge_model=args.rubric_judge_model)
        rubric_judge = build_openai_rubric_judge(model=args.rubric_judge_model)

    report_path = run_baseline(
        output_dir=args.output_dir,
        rubric_judge=rubric_judge,
        rubric_config=rubric_config,
        progress=lambda message: print(message, flush=True),
    )
    print(report_path)


if __name__ == "__main__":
    main()
