"""Backend factory."""
from __future__ import annotations

from graphthrift.backends.base import BackendResult, LLMBackend, Usage, est_tokens
from graphthrift.backends.fake import FakeBackend
from graphthrift.config import Settings, get_settings

__all__ = ["LLMBackend", "BackendResult", "Usage", "est_tokens", "FakeBackend", "build_backend"]


def build_backend(settings: Settings | None = None) -> LLMBackend:
    s = settings or get_settings()
    if s.backend == "fake":
        return FakeBackend()
    if s.backend == "ollama":
        from graphthrift.backends.ollama import OllamaBackend

        return OllamaBackend(
            base_url=s.ollama_base_url,
            medium=s.ollama_model,
            small=s.ollama_small_model,
            embed=s.ollama_embed_model,
        )
    if s.backend == "openai":
        from graphthrift.backends.openai_compat import OpenAICompatBackend

        return OpenAICompatBackend(
            base_url=s.openai_base_url,
            api_key=s.openai_api_key,
            medium=s.openai_model,
            small=s.openai_small_model,
            embed=s.openai_embed_model,
        )
    raise ValueError(f"unknown backend: {s.backend}")
