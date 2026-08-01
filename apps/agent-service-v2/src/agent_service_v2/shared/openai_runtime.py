from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, Mapping, Protocol, Sequence, TypeVar

from pydantic import BaseModel

from agent_service_v2.prompts import (
    DEFAULT_OPENAI_MODEL_BY_TIER,
    ModelTier,
    PromptBundle,
    PromptId,
    build_prompt_bundle,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)
VALIDATION_RETRY_COUNT = 0


class ResponsesClient(Protocol):
    responses: Any


class InvocationOutcome(str, Enum):
    SUCCESS = "success"
    INSUFFICIENT_CONTEXT = "insufficient_context"
    REFUSAL_OR_UNUSABLE = "refusal_or_unusable"


@dataclass(frozen=True, slots=True)
class PromptUsage:
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None
    cached_tokens: int | None = None
    cache_write_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class SemanticValidationResult:
    accepted: bool
    outcome: InvocationOutcome
    validation_feedback: tuple[str, ...] = ()
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class PromptInvocationResult(Generic[SchemaT]):
    output: SchemaT | None
    outcome: InvocationOutcome
    usage: PromptUsage
    attempts: int
    response_id: str | None = None
    refusal_reason: str | None = None
    error_message: str | None = None


class PromptInvocationError(RuntimeError):
    """Raised when the provider returns a refusal or unusable structured output."""

    def __init__(
        self,
        message: str,
        *,
        result: PromptInvocationResult[Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.result = result


def accept_output(_: BaseModel) -> SemanticValidationResult:
    return SemanticValidationResult(
        accepted=True,
        outcome=InvocationOutcome.SUCCESS,
    )


def is_gpt_56_family(model: str) -> bool:
    return model.startswith("gpt-5.6")


def build_openai_response_request(
    bundle: PromptBundle,
    *,
    schema: type[SchemaT],
    model: str | None = None,
    tools: Sequence[Mapping[str, Any]] = (),
    metadata: Mapping[str, str] | None = None,
    max_output_tokens: int | None = None,
) -> dict[str, Any]:
    resolved_model = model or DEFAULT_OPENAI_MODEL_BY_TIER[bundle.model_tier]
    request: dict[str, Any] = {
        "model": resolved_model,
        "input": [
            {
                "role": "developer",
                "content": [
                    {
                        "type": "input_text",
                        "text": bundle.instructions,
                    }
                ],
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": bundle.input_text,
                    }
                ],
            },
        ],
        "reasoning": {"effort": bundle.reasoning_effort.value},
        "text": {"verbosity": bundle.text_verbosity.value},
        "text_format": schema,
    }
    if tools:
        request["tools"] = list(tools)
    if metadata:
        request["metadata"] = dict(metadata)
    if max_output_tokens is not None:
        request["max_output_tokens"] = max_output_tokens
    if is_gpt_56_family(resolved_model):
        request["prompt_cache_key"] = bundle.cache_key
        request["prompt_cache_options"] = {"mode": "explicit", "ttl": "30m"}
        request["input"][0]["content"][0]["prompt_cache_breakpoint"] = {
            "mode": "explicit"
        }
    return request


def invoke_structured_prompt(
    client: ResponsesClient,
    *,
    prompt_id: PromptId | str,
    context: Any,
    schema: type[SchemaT],
    semantic_validator: Callable[[SchemaT], SemanticValidationResult] = accept_output,
    model: str | None = None,
    model_by_tier: Mapping[ModelTier, str] = DEFAULT_OPENAI_MODEL_BY_TIER,
    tools: Sequence[Mapping[str, Any]] = (),
    metadata: Mapping[str, str] | None = None,
    max_output_tokens: int | None = None,
    cache_scope: str | None = None,
) -> PromptInvocationResult[SchemaT]:
    validation_feedback: tuple[str, ...] = ()
    attempts = 0
    last_result: PromptInvocationResult[SchemaT] | None = None

    while attempts < VALIDATION_RETRY_COUNT + 1:
        attempts += 1
        bundle = build_prompt_bundle(
            prompt_id,
            context,
            validation_feedback=validation_feedback,
            cache_scope=cache_scope,
        )
        resolved_model = model or model_by_tier[bundle.model_tier]
        request = build_openai_response_request(
            bundle,
            schema=schema,
            model=resolved_model,
            tools=tools,
            metadata=metadata,
            max_output_tokens=max_output_tokens,
        )
        response = client.responses.parse(**request)
        parsed = _get_response_value(response, "output_parsed")
        usage = _extract_usage(response)
        refusal_reason = _extract_refusal_reason(response)

        if parsed is None:
            error_message = "Provider did not return a parsed structured output."
            result = PromptInvocationResult[SchemaT](
                output=None,
                outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
                usage=usage,
                attempts=attempts,
                response_id=_get_response_value(response, "id"),
                refusal_reason=refusal_reason,
                error_message=error_message,
            )
            raise PromptInvocationError(error_message, result=result)

        validation = semantic_validator(parsed)
        if validation.accepted:
            return PromptInvocationResult(
                output=parsed,
                outcome=validation.outcome,
                usage=usage,
                attempts=attempts,
                response_id=_get_response_value(response, "id"),
                refusal_reason=refusal_reason,
                error_message=validation.error_message,
            )

        result = PromptInvocationResult(
            output=parsed,
            outcome=validation.outcome,
            usage=usage,
            attempts=attempts,
            response_id=_get_response_value(response, "id"),
            refusal_reason=refusal_reason,
            error_message=validation.error_message,
        )
        last_result = result
        if attempts <= VALIDATION_RETRY_COUNT and validation.validation_feedback:
            validation_feedback = validation.validation_feedback
            continue
        break

    if last_result is None:
        raise PromptInvocationError(
            "Prompt invocation failed before producing a result."
        )
    raise PromptInvocationError(
        last_result.error_message or "Structured output was semantically unusable.",
        result=last_result,
    )


def _extract_usage(response: Any) -> PromptUsage:
    usage = _get_response_value(response, "usage", {}) or {}
    input_tokens_details = _get_response_value(usage, "input_tokens_details", {}) or {}
    output_tokens_details = (
        _get_response_value(usage, "output_tokens_details", {}) or {}
    )
    return PromptUsage(
        prompt_tokens=_get_response_value(usage, "input_tokens"),
        completion_tokens=_get_response_value(usage, "output_tokens"),
        total_tokens=_get_response_value(usage, "total_tokens"),
        cached_tokens=_get_response_value(input_tokens_details, "cached_tokens"),
        cache_write_tokens=_get_response_value(
            input_tokens_details, "cache_write_tokens"
        )
        or _get_response_value(output_tokens_details, "cache_write_tokens"),
    )


def _extract_refusal_reason(response: Any) -> str | None:
    output = _get_response_value(response, "output", []) or []
    for item in output:
        content = _get_response_value(item, "content", []) or []
        for block in content:
            if _get_response_value(block, "type") == "refusal":
                return _get_response_value(block, "refusal")
    return None


def _get_response_value(response: Any, field: str, default: Any = None) -> Any:
    if isinstance(response, Mapping):
        return response.get(field, default)
    return getattr(response, field, default)
