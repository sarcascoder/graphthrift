"""Real drop-in wrapper for Graphiti's `LLMClient`.

Adoption is a one-line change:

    from graphiti_core import Graphiti
    from graphiti_core.llm_client.openai_client import OpenAIClient
    import graphthrift

    base = OpenAIClient(config=...)
    graphiti = Graphiti(llm_client=graphthrift.wrap(base, trace=my_trace))

We subclass `LLMClient` and override ONLY `_generate_response` (the teardown's
recommended seam — the base keeps its retry/tracing and passes prompt_name +
model_size down). Around the wrapped client we add: model-size routing (so the
small tier is honored even on providers that ignore it), a response cache, and
per-call cost/latency metering into a shared RunTrace.
"""
from __future__ import annotations

from time import perf_counter
from typing import Any

from graphthrift.backends.base import est_tokens
from graphthrift.instrument.tracing import CallRecord, RunTrace
from graphthrift.optimize.cache import ResponseCache
from graphthrift.optimize.config import OptimizerConfig
from graphthrift.optimize.router import ModelRouter


def _size_to_str(model_size: Any) -> str:
    s = str(getattr(model_size, "value", model_size)).lower()
    return "small" if "small" in s else "medium"


def wrap(client: Any, *, config: OptimizerConfig | None = None, trace: RunTrace | None = None):
    """Return a GraphThrift-instrumented subclass instance wrapping `client`."""
    try:
        from graphiti_core.llm_client.client import LLMClient
        from graphiti_core.llm_client.config import ModelSize
    except ImportError as e:  # pragma: no cover - exercised only without graphiti
        raise ImportError(
            "graphthrift.wrap requires graphiti-core. Install with: pip install 'graphthrift[graphiti]'"
        ) from e

    cfg = config or OptimizerConfig.safe()
    run_trace = trace or RunTrace(label="graphiti")
    response_cache = ResponseCache() if cfg.cache_enabled else None
    router = ModelRouter(cfg)

    def _to_str_size(sz: ModelSize) -> str:
        return _size_to_str(sz)

    def _to_model_size(s: str) -> ModelSize:
        return ModelSize.small if s == "small" else ModelSize.medium

    class InstrumentedGraphitiClient(LLMClient):  # type: ignore[misc, valid-type]
        def __init__(self) -> None:
            # mirror the wrapped client's config so base-class behavior is identical
            super().__init__(config=getattr(client, "config", None), cache=False)
            self._inner = client
            self.trace = run_trace
            self.cfg = cfg
            self.cache = response_cache
            self.router = router

        async def _generate_response(  # type: ignore[override]
            self,
            messages: list,
            response_model: Any = None,
            max_tokens: int | None = None,
            model_size: Any = None,
            **kwargs: Any,
        ) -> dict[str, Any]:
            prompt_name = kwargs.get("prompt_name") or getattr(response_model, "__name__", "llm")
            requested = _to_str_size(model_size) if model_size is not None else "medium"
            effective, downgraded = self.router.route(prompt_name, requested)

            msg_dicts = [
                {"role": getattr(m, "role", "user"), "content": getattr(m, "content", str(m))}
                for m in messages
            ]

            if self.cache is not None:
                hit = self.cache.get(prompt_name, msg_dicts)
                if hit is not None:
                    self.trace.add(CallRecord(
                        stage=prompt_name, prompt_name=prompt_name,
                        model=str(getattr(self._inner, "model", "unknown")), model_size=effective,
                        prompt_tokens=0, completion_tokens=0, latency_ms=1.0, cache_hit=True,
                    ))
                    return hit

            call_kwargs = dict(kwargs)
            if model_size is not None:
                call_kwargs["model_size"] = _to_model_size(effective)
            t0 = perf_counter()
            result = await self._inner._generate_response(
                messages, response_model, max_tokens or 4096, **_filter_kwargs(self._inner, call_kwargs)
            )
            latency = (perf_counter() - t0) * 1000.0

            prompt_tokens = sum(est_tokens(m["content"]) for m in msg_dicts)
            completion_tokens = est_tokens(str(result))
            self.trace.add(CallRecord(
                stage=prompt_name, prompt_name=prompt_name,
                model=str(getattr(self._inner, "model", "unknown")), model_size=effective,
                prompt_tokens=prompt_tokens, completion_tokens=completion_tokens, latency_ms=latency,
                routed_from=("medium" if downgraded else None),
            ))
            if self.cache is not None:
                self.cache.put(prompt_name, msg_dicts, result)
            return result

    return InstrumentedGraphitiClient()


def _filter_kwargs(inner: Any, kwargs: dict) -> dict:
    """Pass only kwargs the inner client accepts (version-robust)."""
    import inspect

    try:
        sig = inspect.signature(inner._generate_response)
    except (TypeError, ValueError):
        return {}
    allowed = set(sig.parameters)
    if any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values()):
        return kwargs
    return {k: v for k, v in kwargs.items() if k in allowed}
