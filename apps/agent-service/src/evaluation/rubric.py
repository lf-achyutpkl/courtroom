from __future__ import annotations

import json
import time
from typing import Callable, Literal, Protocol

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.evaluation.dataset import EvaluationReference
from src.evaluation.evaluators import EvaluatorResult
from src.utils.llm import _extract_usage_stats
from src.utils.types import RunTrialResponse

RUBRIC_PROMPT_VERSION = "courtroom-rubric-v1"
DEFAULT_JUDGE_MODEL = "gpt-4o"

RubricDimension = Literal[
    "legal_grounding",
    "procedural_realism",
    "role_adherence",
    "contradiction_handling",
    "verdict_support",
    "unsafe_content_handling",
]

DEFAULT_THRESHOLDS: dict[RubricDimension, float] = {
    "legal_grounding": 0.75,
    "procedural_realism": 0.7,
    "role_adherence": 0.8,
    "contradiction_handling": 0.75,
    "verdict_support": 0.8,
    "unsafe_content_handling": 0.9,
}

RUBRIC_PROMPT_TEMPLATE = """Score the courtroom transcript against the supplied case reference.
Return typed scores for each rubric dimension with rationale and cited turn ids.
Dimensions: legal_grounding, procedural_realism, role_adherence,
contradiction_handling, verdict_support, unsafe_content_handling."""

RUBRIC_JUDGE_SYSTEM_PROMPT = """You are an evaluation judge for synthetic courtroom transcripts.
Score only the transcript against the supplied reference. Do not reward facts that are
unsupported by the transcript. Use cited_turn_ids to point to transcript turn indexes.
Return one score for every rubric dimension."""


class RubricEvaluatorConfig(BaseModel):
    judge_model: str = DEFAULT_JUDGE_MODEL
    prompt_version: str = RUBRIC_PROMPT_VERSION
    thresholds: dict[RubricDimension, float] = Field(
        default_factory=lambda: dict(DEFAULT_THRESHOLDS)
    )


class RubricInput(BaseModel):
    transcript: list[dict]
    reference: EvaluationReference
    prompt_template: str = RUBRIC_PROMPT_TEMPLATE
    prompt_version: str = RUBRIC_PROMPT_VERSION
    judge_model: str = DEFAULT_JUDGE_MODEL


class RubricScore(BaseModel):
    dimension: RubricDimension
    score: float = Field(ge=0.0, le=1.0)
    threshold: float
    passed: bool
    rationale: str
    cited_turn_ids: list[int] = Field(default_factory=list)


class TokenUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class RubricEvaluationResult(BaseModel):
    evaluator_name: str = "llm_rubric"
    evaluator_model: str
    evaluator_prompt_version: str
    passed: bool
    scores: list[RubricScore]
    latency_ms: int
    token_usage: TokenUsage | None = None
    rationale: str
    cited_turn_ids: list[int] = Field(default_factory=list)


class JudgeResponse(BaseModel):
    scores: list[RubricScore]
    rationale: str
    token_usage: TokenUsage | None = None


class RubricJudge(Protocol):
    def __call__(self, rubric_input: RubricInput) -> JudgeResponse | dict:
        ...


JudgeCallable = Callable[[RubricInput], JudgeResponse | dict]


def _build_rubric_input(
    response: RunTrialResponse,
    reference: EvaluationReference,
    config: RubricEvaluatorConfig,
) -> RubricInput:
    return RubricInput(
        transcript=[turn.model_dump() for turn in response.full_trial_transcript],
        reference=reference,
        prompt_version=config.prompt_version,
        judge_model=config.judge_model,
    )


def _build_openai_judge_prompt(rubric_input: RubricInput) -> str:
    payload = rubric_input.model_dump(mode="json")
    payload["thresholds"] = DEFAULT_THRESHOLDS
    return json.dumps(payload, indent=2)


def build_openai_rubric_judge(
    *,
    model: str = DEFAULT_JUDGE_MODEL,
    temperature: float = 0.0,
) -> JudgeCallable:
    llm = ChatOpenAI(model=model, temperature=temperature, max_retries=0)

    def judge(rubric_input: RubricInput) -> JudgeResponse:
        structured_llm = llm.bind(
            max_completion_tokens=1400
        ).with_structured_output(JudgeResponse, include_raw=True)
        response = structured_llm.invoke(
            [
                SystemMessage(content=RUBRIC_JUDGE_SYSTEM_PROMPT),
                HumanMessage(content=_build_openai_judge_prompt(rubric_input)),
            ]
        )
        parsing_error = response.get("parsing_error")
        if parsing_error:
            raise parsing_error

        judge_response = JudgeResponse.model_validate(response["parsed"])
        usage_stats = _extract_usage_stats(response)
        if usage_stats:
            judge_response = judge_response.model_copy(
                update={
                    "token_usage": TokenUsage(
                        prompt_tokens=usage_stats.get("prompt_tokens"),
                        completion_tokens=usage_stats.get("completion_tokens"),
                        total_tokens=usage_stats.get("total_tokens"),
                    )
                }
            )
        return judge_response

    return judge


def evaluate_rubric(
    *,
    response: RunTrialResponse,
    reference: EvaluationReference,
    judge: RubricJudge | JudgeCallable,
    config: RubricEvaluatorConfig | None = None,
    prerequisite_results: list[EvaluatorResult] | None = None,
) -> list[RubricEvaluationResult]:
    config = config or RubricEvaluatorConfig()
    if not response.run.deterministic_validation_passed:
        return []
    if prerequisite_results and any(
        not result.passed for result in prerequisite_results
    ):
        return []

    rubric_input = _build_rubric_input(response, reference, config)
    started = time.perf_counter()
    raw_judge_response = judge(rubric_input)
    latency_ms = int((time.perf_counter() - started) * 1000)
    judge_response = JudgeResponse.model_validate(raw_judge_response)

    normalized_scores = [
        score.model_copy(
            update={
                "threshold": config.thresholds[score.dimension],
                "passed": score.score >= config.thresholds[score.dimension],
            }
        )
        for score in judge_response.scores
    ]
    cited_turn_ids = sorted(
        {turn_id for score in normalized_scores for turn_id in score.cited_turn_ids}
    )
    return [
        RubricEvaluationResult(
            evaluator_model=config.judge_model,
            evaluator_prompt_version=config.prompt_version,
            passed=all(score.passed for score in normalized_scores),
            scores=normalized_scores,
            latency_ms=latency_ms,
            token_usage=judge_response.token_usage,
            rationale=judge_response.rationale,
            cited_turn_ids=cited_turn_ids,
        )
    ]
