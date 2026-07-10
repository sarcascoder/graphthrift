"""Token pricing table + cost computation.

Prices are USD per 1M tokens (input, output). Values are approximate and easily
overridden via `register_price`. The point is a *consistent* cost model so
baseline-vs-optimized deltas are meaningful, not a billing-accurate ledger.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Price:
    input_per_m: float
    output_per_m: float


# USD per 1,000,000 tokens. Extend freely.
_PRICES: dict[str, Price] = {
    # OpenAI (frontier + nano, matching Graphiti's medium/small defaults)
    "gpt-5.5": Price(5.00, 15.00),
    "gpt-4.1-nano": Price(0.10, 0.40),
    "gpt-4o": Price(2.50, 10.00),
    "gpt-4o-mini": Price(0.15, 0.60),
    "gpt-4.1-mini": Price(0.40, 1.60),
    # Anthropic
    "claude-haiku-4-5": Price(1.00, 5.00),
    "claude-opus-4-8": Price(15.00, 75.00),
    # Gemini
    "gemini-3-flash-preview": Price(0.30, 1.20),
    "gemini-2.5-flash-lite": Price(0.05, 0.20),
    # Embeddings (output tokens are 0)
    "text-embedding-3-small": Price(0.02, 0.0),
    "nomic-embed-text": Price(0.0, 0.0),
    # Local models are free to run; we still meter tokens so an "equivalent cloud
    # cost" can be shown by re-pricing against a cloud model in the dashboard.
    "qwen2.5:3b": Price(0.0, 0.0),
    "qwen2.5:0.5b": Price(0.0, 0.0),
    "fake-medium": Price(5.00, 15.00),
    "fake-small": Price(0.10, 0.40),
    "fake-embed": Price(0.02, 0.0),
}

_DEFAULT = Price(1.00, 3.00)


def register_price(model: str, input_per_m: float, output_per_m: float) -> None:
    _PRICES[model] = Price(input_per_m, output_per_m)


def price_for(model: str) -> Price:
    return _PRICES.get(model, _DEFAULT)


def cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    p = price_for(model)
    return (prompt_tokens / 1_000_000) * p.input_per_m + (completion_tokens / 1_000_000) * p.output_per_m
