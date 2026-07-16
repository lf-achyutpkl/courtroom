from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from courtroom_domain import NodeTelemetry
from pydantic import BaseModel, Field


class ModelTokenRate(BaseModel, frozen=True):
    input_per_1m_tokens_usd: Decimal
    output_per_1m_tokens_usd: Decimal
    cached_input_per_1m_tokens_usd: Decimal | None = None


class CostBreakdown(BaseModel, frozen=True):
    input_cost_usd: Decimal
    output_cost_usd: Decimal
    cached_input_cost_usd: Decimal = Decimal("0")
    total_cost_usd: Decimal


class TokenUsageSummary(BaseModel, frozen=True):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cached_tokens: int = 0
    cache_write_tokens: int = 0
    missing_usage_records: int = 0


class NodeUsageSummary(BaseModel, frozen=True):
    node_name: str
    stage: str
    model_name: str | None = None
    call_count: int
    duration_ms: int
    token_usage: TokenUsageSummary
    cost: CostBreakdown | None = None


class CostEstimateSummary(BaseModel, frozen=True):
    currency: str = "USD"
    pricing_source: str
    pricing_units: str = "per_1m_tokens"
    model_rates: dict[str, ModelTokenRate] = Field(default_factory=dict)
    token_usage: TokenUsageSummary
    total_cost_usd: Decimal | None = None
    unpriced_models: list[str] = Field(default_factory=list)
    node_usage: list[NodeUsageSummary] = Field(default_factory=list)


DEFAULT_MODEL_TOKEN_RATES: dict[str, ModelTokenRate] = {
    "gpt-4o-mini": ModelTokenRate(
        input_per_1m_tokens_usd=Decimal("0.15"),
        output_per_1m_tokens_usd=Decimal("0.60"),
        cached_input_per_1m_tokens_usd=Decimal("0.075"),
    ),
    "gpt-4o": ModelTokenRate(
        input_per_1m_tokens_usd=Decimal("2.50"),
        output_per_1m_tokens_usd=Decimal("10.00"),
        cached_input_per_1m_tokens_usd=Decimal("1.25"),
    ),
}

DEFAULT_PRICING_SOURCE = "local_static_rates_openai_pricing_snapshot"
_ONE_MILLION = Decimal("1000000")
_COST_QUANT = Decimal("0.00000001")


def summarize_token_usage(telemetry: list[NodeTelemetry]) -> TokenUsageSummary:
    return TokenUsageSummary(
        prompt_tokens=sum(record.prompt_tokens or 0 for record in telemetry),
        completion_tokens=sum(record.completion_tokens or 0 for record in telemetry),
        total_tokens=sum(record.total_tokens or 0 for record in telemetry),
        cached_tokens=sum(record.cached_tokens or 0 for record in telemetry),
        cache_write_tokens=sum(record.cache_write_tokens or 0 for record in telemetry),
        missing_usage_records=sum(
            1
            for record in telemetry
            if record.prompt_tokens is None
            and record.completion_tokens is None
            and record.total_tokens is None
        ),
    )


def estimate_cost(
    usage: TokenUsageSummary,
    rate: ModelTokenRate,
) -> CostBreakdown:
    cached_tokens = usage.cached_tokens
    billable_prompt_tokens = max(usage.prompt_tokens - cached_tokens, 0)
    cached_rate = rate.cached_input_per_1m_tokens_usd

    input_cost = (
        Decimal(billable_prompt_tokens) * rate.input_per_1m_tokens_usd / _ONE_MILLION
    )
    cached_cost = (
        Decimal(cached_tokens) * cached_rate / _ONE_MILLION
        if cached_rate is not None
        else Decimal("0")
    )
    output_cost = (
        Decimal(usage.completion_tokens) * rate.output_per_1m_tokens_usd / _ONE_MILLION
    )
    total = input_cost + cached_cost + output_cost
    return CostBreakdown(
        input_cost_usd=input_cost.quantize(_COST_QUANT, rounding=ROUND_HALF_UP),
        cached_input_cost_usd=cached_cost.quantize(_COST_QUANT, rounding=ROUND_HALF_UP),
        output_cost_usd=output_cost.quantize(_COST_QUANT, rounding=ROUND_HALF_UP),
        total_cost_usd=total.quantize(_COST_QUANT, rounding=ROUND_HALF_UP),
    )


def build_cost_estimate_summary(
    telemetry: list[NodeTelemetry],
    *,
    model_rates: dict[str, ModelTokenRate] | None = None,
    pricing_source: str = DEFAULT_PRICING_SOURCE,
) -> CostEstimateSummary:
    rates = model_rates or DEFAULT_MODEL_TOKEN_RATES
    total_usage = summarize_token_usage(telemetry)
    grouped: dict[tuple[str, str, str | None], list[NodeTelemetry]] = {}
    for record in telemetry:
        key = (record.node_name, record.stage, record.model_name)
        grouped.setdefault(key, []).append(record)

    node_usage: list[NodeUsageSummary] = []
    total_cost = Decimal("0")
    unpriced_models: set[str] = set()

    for (node_name, stage, model_name), records in sorted(grouped.items()):
        usage = summarize_token_usage(records)
        rate = rates.get(model_name or "")
        cost = estimate_cost(usage, rate) if rate is not None else None
        if cost is not None:
            total_cost += cost.total_cost_usd
        elif model_name:
            unpriced_models.add(model_name)

        node_usage.append(
            NodeUsageSummary(
                node_name=node_name,
                stage=stage,
                model_name=model_name,
                call_count=len(records),
                duration_ms=sum(record.duration_ms for record in records),
                token_usage=usage,
                cost=cost,
            )
        )

    return CostEstimateSummary(
        pricing_source=pricing_source,
        model_rates=rates,
        token_usage=total_usage,
        total_cost_usd=total_cost.quantize(_COST_QUANT, rounding=ROUND_HALF_UP)
        if telemetry
        else Decimal("0"),
        unpriced_models=sorted(unpriced_models),
        node_usage=node_usage,
    )


def combine_cost_estimate_summaries(
    summaries: list[CostEstimateSummary],
    *,
    pricing_source: str = DEFAULT_PRICING_SOURCE,
    model_rates: dict[str, ModelTokenRate] | None = None,
) -> CostEstimateSummary:
    summaries = [summary for summary in summaries if summary is not None]
    rates = model_rates or DEFAULT_MODEL_TOKEN_RATES
    total_cost = sum(
        ((summary.total_cost_usd or Decimal("0")) for summary in summaries),
        Decimal("0"),
    )
    node_usage = [
        node_usage for summary in summaries for node_usage in summary.node_usage
    ]

    return CostEstimateSummary(
        pricing_source=pricing_source,
        model_rates=rates,
        token_usage=TokenUsageSummary(
            prompt_tokens=sum(
                summary.token_usage.prompt_tokens for summary in summaries
            ),
            completion_tokens=sum(
                summary.token_usage.completion_tokens for summary in summaries
            ),
            total_tokens=sum(summary.token_usage.total_tokens for summary in summaries),
            cached_tokens=sum(
                summary.token_usage.cached_tokens for summary in summaries
            ),
            cache_write_tokens=sum(
                summary.token_usage.cache_write_tokens for summary in summaries
            ),
            missing_usage_records=sum(
                summary.token_usage.missing_usage_records for summary in summaries
            ),
        ),
        total_cost_usd=total_cost.quantize(_COST_QUANT, rounding=ROUND_HALF_UP),
        unpriced_models=sorted(
            {model for summary in summaries for model in summary.unpriced_models}
        ),
        node_usage=node_usage,
    )
