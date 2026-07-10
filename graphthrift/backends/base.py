"""LLM backend protocol + shared value types.

A backend is the raw model transport. Instrumentation, caching, routing and
batching all live *above* this layer so they work identically across backends.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


def est_tokens(text: str) -> int:
    """Cheap, deterministic token estimate (~4 chars/token)."""
    return max(1, len(text) // 4)


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class BackendResult:
    data: dict[str, Any]           # parsed structured output
    model: str
    usage: Usage = field(default_factory=Usage)
    text: str = ""


@runtime_checkable
class LLMBackend(Protocol):
    name: str

    def model_for(self, model_size: str) -> str:
        """Resolve a ModelSize ('small'|'medium') to a concrete model id."""

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        model_size: str = "medium",
        response_schema: dict[str, Any] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> BackendResult:
        ...

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        ...
