"""InstrumentedLLM — the shared engine: routing + caching + metering + tracing.

Every LLM/embedding call in GraphThrift flows through here, so cost/latency
accounting and the optimizer chain behave identically whether the caller is the
offline demo pipeline or the real Graphiti `LLMClient` wrapper.
"""
from __future__ import annotations

from time import perf_counter
from typing import Any

from graphthrift.backends.base import LLMBackend, est_tokens
from graphthrift.instrument.tracing import CallRecord, RunTrace
from graphthrift.optimize.cache import EmbeddingCache, ResponseCache
from graphthrift.optimize.compressor import PromptCompressor
from graphthrift.optimize.config import OptimizerConfig
from graphthrift.optimize.router import ModelRouter


class InstrumentedLLM:
    def __init__(self, backend: LLMBackend, config: OptimizerConfig, trace: RunTrace) -> None:
        self.backend = backend
        self.cfg = config
        self.trace = trace
        self.router = ModelRouter(config)
        self.cache = ResponseCache() if config.cache_enabled else None
        self.embed_cache = EmbeddingCache() if config.embedding_cache_enabled else None
        self.compressor = PromptCompressor() if config.compressor_enabled else None

    async def call(
        self,
        *,
        stage: str,
        prompt_name: str,
        messages: list[dict[str, str]],
        model_size: str = "medium",
        response_schema: dict[str, Any] | None = None,
        max_tokens: int = 4096,
        context: dict[str, Any] | None = None,
        cacheable: bool = True,
        cache_salient: Any = None,
    ) -> dict[str, Any]:
        effective_size, downgraded = self.router.route(stage, model_size)
        model = self.backend.model_for(effective_size)

        if self.cache is not None and cacheable:
            hit = self.cache.get(prompt_name, messages, cache_salient)
            if hit is not None:
                self.trace.add(CallRecord(
                    stage=stage, prompt_name=prompt_name, model=model, model_size=effective_size,
                    prompt_tokens=0, completion_tokens=0, latency_ms=1.0, cache_hit=True,
                ))
                return hit

        msgs = self.compressor.compress(messages) if self.compressor else messages
        t0 = perf_counter()
        res = await self.backend.generate(
            messages=msgs, model=model, model_size=effective_size,
            response_schema=response_schema, max_tokens=max_tokens, context=context,
        )
        latency = getattr(res, "_latency_ms", (perf_counter() - t0) * 1000.0)
        self.trace.add(CallRecord(
            stage=stage, prompt_name=prompt_name, model=model, model_size=effective_size,
            prompt_tokens=res.usage.prompt_tokens, completion_tokens=res.usage.completion_tokens,
            latency_ms=latency,
            routed_from=(self.backend.model_for(model_size) if downgraded else None),
        ))
        if self.cache is not None and cacheable:
            self.cache.put(prompt_name, messages, res.data, cache_salient)
        return res.data

    def record_eliminated(self, stage: str, prompt_name: str, n: int = 1) -> None:
        """Account for calls an optimizer removed (dedup prefilter / batching)."""
        for _ in range(n):
            self.trace.add(CallRecord(
                stage=stage, prompt_name=prompt_name, model="none", model_size="small",
                prompt_tokens=0, completion_tokens=0, latency_ms=0.0, eliminated=True,
            ))

    async def embed(self, texts: list[str], stage: str = "embed", prompt_name: str = "embed") -> list[list[float]]:
        if not texts:
            return []
        if self.embed_cache is not None:
            results, missing = self.embed_cache.get_many(texts)
            if missing:
                to_embed = [texts[i] for i in missing]
                t0 = perf_counter()
                vecs = await self.backend.embed(to_embed)
                latency = (perf_counter() - t0) * 1000.0
                for j, i in enumerate(missing):
                    results[i] = vecs[j]
                    self.embed_cache.put(texts[i], vecs[j])
                self.trace.add(CallRecord(
                    stage=stage, prompt_name=prompt_name, model="embed", model_size="small",
                    prompt_tokens=sum(est_tokens(t) for t in to_embed), completion_tokens=0,
                    latency_ms=latency, call_type="embed",
                ))
            for _ in range(len(texts) - len(missing)):
                self.trace.add(CallRecord(
                    stage=stage, prompt_name=prompt_name, model="embed", model_size="small",
                    prompt_tokens=0, completion_tokens=0, latency_ms=0.5, cache_hit=True, call_type="embed",
                ))
            return [r or [] for r in results]

        t0 = perf_counter()
        vecs = await self.backend.embed(texts)
        latency = (perf_counter() - t0) * 1000.0
        self.trace.add(CallRecord(
            stage=stage, prompt_name=prompt_name, model="embed", model_size="small",
            prompt_tokens=sum(est_tokens(t) for t in texts), completion_tokens=0,
            latency_ms=latency, call_type="embed",
        ))
        return vecs
