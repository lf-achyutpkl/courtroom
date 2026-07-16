import logging
from datetime import datetime, timezone
from typing import Any, Callable, Literal, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from .env import load_service_env
from .types import NodeTelemetry

load_service_env()

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)

fast_llm = ChatOpenAI(model="gpt-5-mini", temperature=0.9, max_retries=0)
judge_llm = ChatOpenAI(model="gpt-5-nano", temperature=0.2, max_retries=0)

NODE_MAX_COMPLETION_TOKENS = {
    "plan_prosecution_strategy": 180,
    "plan_defense_strategy": 180,
    "opening_prosecution": 140,
    "opening_defense": 140,
    "ask_question": 90,
    "objection_check": 50,
    "witness_answer": 110,
    "judge_ruling": 120,
    "summarize_trial_transcript": 260,
    "closing_prosecution": 170,
    "closing_defense": 170,
    "verdict": 240,
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _extract_usage_stats(response: dict[str, Any]) -> dict[str, int]:
    raw_message = response.get("raw")
    response_metadata = getattr(raw_message, "response_metadata", {}) or {}
    usage_metadata = getattr(raw_message, "usage_metadata", {}) or {}

    token_usage = response_metadata.get("token_usage", {})
    prompt_details = token_usage.get("prompt_tokens_details", {})
    input_details = usage_metadata.get("input_token_details", {})

    def _pick_int(*values: object) -> int | None:
        for value in values:
            if isinstance(value, int):
                return value
        return None

    stats = {
        "prompt_tokens": _pick_int(
            token_usage.get("prompt_tokens"),
            usage_metadata.get("input_tokens"),
        ),
        "completion_tokens": _pick_int(
            token_usage.get("completion_tokens"),
            usage_metadata.get("output_tokens"),
        ),
        "total_tokens": _pick_int(
            token_usage.get("total_tokens"),
            usage_metadata.get("total_tokens"),
        ),
        "cached_tokens": _pick_int(
            prompt_details.get("cached_tokens"),
            input_details.get("cached_tokens"),
        ),
        "cache_write_tokens": _pick_int(
            prompt_details.get("cache_write_tokens"),
            input_details.get("cache_write_tokens"),
        ),
    }

    return {key: value for key, value in stats.items() if value is not None}


def invoke_structured(
    system_prompt: str,
    user_prompt: str,
    schema: type[SchemaT],
    llm: ChatOpenAI = fast_llm,
    *,
    node_name: str = "unknown",
    telemetry_sink: Callable[[NodeTelemetry], None] | None = None,
    stage: Literal["trial", "witness"] = "trial",
    phase: str | None = None,
    witness_id: str | None = None,
) -> SchemaT:
    started_at = _utc_now()
    telemetry_emitted = False

    try:
        max_completion_tokens = NODE_MAX_COMPLETION_TOKENS.get(node_name, 160)
        structured_llm = llm.bind(
            max_completion_tokens=max_completion_tokens
        ).with_structured_output(schema, include_raw=True)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]
        response = structured_llm.invoke(messages)
        completed_at = _utc_now()
        usage_stats = _extract_usage_stats(response)

        parsing_error = response.get("parsing_error")
        if parsing_error:
            if telemetry_sink is not None:
                telemetry_sink(
                    NodeTelemetry(
                        node_name=node_name,
                        stage=stage,
                        phase=phase,
                        witness_id=witness_id,
                        model_name=getattr(llm, "model_name", None),
                        started_at=started_at.isoformat(),
                        completed_at=completed_at.isoformat(),
                        duration_ms=int(
                            (completed_at - started_at).total_seconds() * 1000
                        ),
                        prompt_tokens=usage_stats.get("prompt_tokens"),
                        completion_tokens=usage_stats.get("completion_tokens"),
                        total_tokens=usage_stats.get("total_tokens"),
                        cached_tokens=usage_stats.get("cached_tokens"),
                        cache_write_tokens=usage_stats.get("cache_write_tokens"),
                        parse_success=False,
                        error_type=type(parsing_error).__name__,
                    )
                )
                telemetry_emitted = True
            raise parsing_error

        if telemetry_sink is not None:
            telemetry_sink(
                NodeTelemetry(
                    node_name=node_name,
                    stage=stage,
                    phase=phase,
                    witness_id=witness_id,
                    model_name=getattr(llm, "model_name", None),
                    started_at=started_at.isoformat(),
                    completed_at=completed_at.isoformat(),
                    duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                    prompt_tokens=usage_stats.get("prompt_tokens"),
                    completion_tokens=usage_stats.get("completion_tokens"),
                    total_tokens=usage_stats.get("total_tokens"),
                    cached_tokens=usage_stats.get("cached_tokens"),
                    cache_write_tokens=usage_stats.get("cache_write_tokens"),
                    parse_success=True,
                )
            )
            telemetry_emitted = True

        return response["parsed"]

    except Exception as exc:
        completed_at = _utc_now()
        if telemetry_sink is not None and not telemetry_emitted:
            telemetry_sink(
                NodeTelemetry(
                    node_name=node_name,
                    stage=stage,
                    phase=phase,
                    witness_id=witness_id,
                    model_name=getattr(llm, "model_name", None),
                    started_at=started_at.isoformat(),
                    completed_at=completed_at.isoformat(),
                    duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                    parse_success=False,
                    error_type=type(exc).__name__,
                )
            )
        logger.exception(
            "Failed to invoke structured output for node '%s'",
            node_name,
        )
        raise
