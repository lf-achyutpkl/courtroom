import logging
from typing import Any, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)

fast_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.9, max_retries=0)
judge_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, max_retries=0)

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
    "verdict": 180,
}


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
) -> SchemaT:
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
        usage_stats = _extract_usage_stats(response)
        if usage_stats:
            logger.info("LLM usage for node '%s': %s", node_name, usage_stats)

        parsing_error = response.get("parsing_error")
        if parsing_error:
            raise parsing_error

        return response["parsed"]

    except Exception as e:
        logger.exception(
            "Failed to invoke structured output for node '%s'",
            node_name,
        )
        raise
