from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol, Sequence, TypeVar

from pydantic import BaseModel

from agent_service_v2.prompts import PromptId
from agent_service_v2.shared.openai_runtime import (
    InvocationOutcome,
    PromptInvocationResult,
    SemanticValidationResult,
    accept_output,
    invoke_structured_prompt,
)

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class PromptRunRecord(BaseModel):
    node_name: str
    prompt_id: str
    outcome: str
    attempts: int
    response_id: str | None = None
    cached_tokens: int | None = None
    cache_write_tokens: int | None = None


class NodeFailureRecord(BaseModel):
    node_name: str
    prompt_id: str
    outcome: str
    message: str
    response_id: str | None = None


class StructuredPromptExecutor(Protocol):
    def invoke(
        self,
        *,
        prompt_id: PromptId | str,
        context: Any,
        schema: type[SchemaT],
        semantic_validator: Any = accept_output,
        metadata: Mapping[str, str] | None = None,
        cache_scope: str | None = None,
        max_output_tokens: int | None = None,
    ) -> PromptInvocationResult[SchemaT]: ...


@dataclass(frozen=True, slots=True)
class OpenAIResponsesPromptExecutor:
    client: Any
    model: str | None = None

    def invoke(
        self,
        *,
        prompt_id: PromptId | str,
        context: Any,
        schema: type[SchemaT],
        semantic_validator: Any = accept_output,
        metadata: Mapping[str, str] | None = None,
        cache_scope: str | None = None,
        max_output_tokens: int | None = None,
    ) -> PromptInvocationResult[SchemaT]:
        return invoke_structured_prompt(
            self.client,
            prompt_id=prompt_id,
            context=context,
            schema=schema,
            semantic_validator=semantic_validator,
            model=self.model,
            metadata=metadata,
            cache_scope=cache_scope,
            max_output_tokens=max_output_tokens,
        )


def one_retry_feedback(message: str) -> SemanticValidationResult:
    return SemanticValidationResult(
        accepted=False,
        outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
        validation_feedback=(message,),
        error_message=message,
    )


__all__ = [
    "NodeFailureRecord",
    "OpenAIResponsesPromptExecutor",
    "PromptRunRecord",
    "StructuredPromptExecutor",
]
