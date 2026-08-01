from __future__ import annotations

# pyright: reportMissingImports=false
from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from agent_service_v2.prompts import (
    PROMPTS,
    PromptId,
    PromptSerializationError,
    build_prompt_bundle,
    render_runtime_input,
)
from agent_service_v2.shared import (
    InvocationOutcome,
    PromptInvocationError,
    SemanticValidationResult,
    build_openai_response_request,
    invoke_structured_prompt,
)


class DummySchema(BaseModel):
    answer: str


class FakeResponsesAPI:
    def __init__(self, responses: list[object]) -> None:
        self._responses = responses
        self.requests: list[dict[str, object]] = []

    def parse(self, **request: object) -> object:
        self.requests.append(request)
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses: list[object]) -> None:
        self.responses = FakeResponsesAPI(responses)


def _response(
    parsed: BaseModel | None,
    *,
    usage: dict[str, object] | None = None,
    refusal: str | None = None,
) -> SimpleNamespace:
    output: list[object] = []
    if refusal is not None:
        output.append(
            SimpleNamespace(
                content=[
                    SimpleNamespace(
                        type="refusal",
                        refusal=refusal,
                    )
                ]
            )
        )
    return SimpleNamespace(
        id="resp_test",
        output_parsed=parsed,
        output=output,
        usage=usage
        or {
            "input_tokens": 1200,
            "output_tokens": 60,
            "total_tokens": 1260,
            "input_tokens_details": {
                "cached_tokens": 900,
                "cache_write_tokens": 250,
            },
        },
    )


def test_prompt_registry_moved_to_v2_and_complete() -> None:
    assert len(PROMPTS) == 66


def test_build_prompt_bundle_includes_cache_metadata_and_verbosity() -> None:
    bundle = build_prompt_bundle(
        PromptId.PLAN_EXAMINATION_ACTION,
        {"fact_ids": ["fact_1"]},
        cache_scope="Tenant Alpha / Batch 1",
    )

    assert bundle.cache_key == (
        "courtroom:2.0.0:plan_examination_action:1.0.0:default:tenant-alpha-batch-1"
    )
    assert bundle.model_tier.value == "default"
    assert bundle.reasoning_effort.value == "medium"
    assert bundle.text_verbosity.value == "low"


def test_render_runtime_input_rejects_unsupported_values() -> None:
    with pytest.raises(PromptSerializationError) as exc_info:
        render_runtime_input({"bad": object()})

    assert "runtime_context.bad" in str(exc_info.value)


def test_gpt_56_request_uses_explicit_cache_breakpoint_and_verbosity() -> None:
    bundle = build_prompt_bundle(PromptId.DRAFT_QUESTION, {"topic": "timeline"})

    request = build_openai_response_request(
        bundle,
        schema=DummySchema,
        model="gpt-5.6-terra",
    )

    assert request["prompt_cache_key"] == bundle.cache_key
    assert request["prompt_cache_options"] == {"mode": "explicit", "ttl": "30m"}
    assert request["text"] == {"verbosity": bundle.text_verbosity.value}
    assert request["input"][0]["content"][0]["prompt_cache_breakpoint"] == {
        "mode": "explicit"
    }
    assert "prompt_cache_breakpoint" not in request["input"][1]["content"][0]


def test_pre_gpt_56_request_omits_breakpoint_fields() -> None:
    bundle = build_prompt_bundle(PromptId.DRAFT_QUESTION, {"topic": "timeline"})

    request = build_openai_response_request(
        bundle,
        schema=DummySchema,
        model="gpt-5-mini",
    )

    assert "prompt_cache_key" not in request
    assert "prompt_cache_options" not in request
    assert "prompt_cache_breakpoint" not in request["input"][0]["content"][0]


def test_invoke_structured_prompt_does_not_retry_validation_failures() -> None:
    client = FakeClient(
        [
            _response(DummySchema(answer="unsupported")),
            _response(DummySchema(answer="grounded")),
        ]
    )

    def validator(result: DummySchema) -> SemanticValidationResult:
        if result.answer == "unsupported":
            return SemanticValidationResult(
                accepted=False,
                outcome=InvocationOutcome.REFUSAL_OR_UNUSABLE,
                validation_feedback=("missing cited object ids",),
                error_message="Missing citations.",
            )
        return SemanticValidationResult(
            accepted=True,
            outcome=InvocationOutcome.SUCCESS,
        )

    with pytest.raises(PromptInvocationError) as exc_info:
        invoke_structured_prompt(
            client,
            prompt_id=PromptId.DRAFT_QUESTION,
            context={"topic": "timeline"},
            schema=DummySchema,
            semantic_validator=validator,
            model="gpt-5.6-terra",
        )

    assert exc_info.value.result is not None
    assert exc_info.value.result.attempts == 1
    assert len(client.responses.requests) == 1


def test_invoke_structured_prompt_accepts_typed_response_usage() -> None:
    usage = SimpleNamespace(
        input_tokens=1200,
        output_tokens=60,
        total_tokens=1260,
        input_tokens_details=SimpleNamespace(cached_tokens=900),
        output_tokens_details=SimpleNamespace(),
    )
    client = FakeClient([_response(DummySchema(answer="grounded"), usage=usage)])

    result = invoke_structured_prompt(
        client,
        prompt_id=PromptId.DRAFT_QUESTION,
        context={"topic": "timeline"},
        schema=DummySchema,
        model="gpt-5.6-terra",
    )

    assert result.usage.prompt_tokens == 1200
    assert result.usage.completion_tokens == 60
    assert result.usage.total_tokens == 1260
    assert result.usage.cached_tokens == 900


def test_invoke_structured_prompt_raises_for_refusal_or_missing_parsed_output() -> None:
    client = FakeClient([_response(None, refusal="safety refusal")])

    with pytest.raises(PromptInvocationError) as exc_info:
        invoke_structured_prompt(
            client,
            prompt_id=PromptId.DRAFT_QUESTION,
            context={"topic": "timeline"},
            schema=DummySchema,
            model="gpt-5.6-terra",
        )

    result = exc_info.value.result
    assert result is not None
    assert result.outcome is InvocationOutcome.REFUSAL_OR_UNUSABLE
    assert result.refusal_reason == "safety refusal"
