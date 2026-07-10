"""Deterministic simulation backend — the engine behind the key-free demo.

It does NOT call any model. Instead it simulates a realistic *imperfect*
entity/edge extractor driven by the demo dataset's oracle annotations (passed via
`context`). Crucially it degrades on the 'small' model tier: it misses
low-salience entities and hard edges. That makes optimizations that route work to
the small model carry a *real, measurable* quality cost, so the eval gate is not a
rubber stamp. Real backends (Ollama/OpenAI) ignore `context` and extract for real.
"""
from __future__ import annotations

import hashlib
from typing import Any

from graphthrift.backends.base import BackendResult, LLMBackend, Usage, est_tokens


def _seed(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest()[:8], 16)


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


class FakeBackend(LLMBackend):
    name = "fake"

    def __init__(self, medium: str = "fake-medium", small: str = "fake-small", embed: str = "fake-embed"):
        self._medium = medium
        self._small = small
        self._embed = embed

    def model_for(self, model_size: str) -> str:
        return self._small if model_size == "small" else self._medium

    def _latency(self, model_size: str, out_tokens: int, seed_key: str) -> float:
        base = 120.0 if model_size == "small" else 450.0
        jitter = (_seed(seed_key) % 120) - 40  # deterministic +/- spread
        return max(20.0, base + out_tokens * 0.6 + jitter)

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
        ctx = context or {}
        op = ctx.get("op", "noop")
        degraded = model_size == "small"
        data: dict[str, Any]

        if op == "extract_nodes":
            ents = ctx.get("episode", {}).get("entities", [])
            # 'elusive' items are in the gold graph but even the medium model misses
            # them; the small model additionally misses low-salience entities.
            kept = [e for e in ents
                    if not e.get("elusive")
                    and not (degraded and e.get("salience", 1.0) < 0.5)]
            data = {"entities": [{"name": e["name"], "type": e.get("type", "Entity")} for e in kept]}

        elif op == "extract_edges":
            triples = ctx.get("episode", {}).get("triples", [])
            kept = [t for t in triples
                    if not t.get("elusive")
                    and not (degraded and t.get("hard"))]
            data = {"edges": [
                {"subject": t["subject"], "predicate": t["predicate"], "object": t["object"]}
                for t in kept
            ]}

        elif op == "resolve_edge":
            edge = ctx.get("edge", {})
            existing = {(_norm(e["subject"]), _norm(e["predicate"]), _norm(e["object"]))
                        for e in ctx.get("existing_edges", [])}
            key = (_norm(edge.get("subject", "")), _norm(edge.get("predicate", "")), _norm(edge.get("object", "")))
            data = {"duplicate": key in existing}

        elif op == "resolve_edges_batch":
            existing = {(_norm(e["subject"]), _norm(e["predicate"]), _norm(e["object"]))
                        for e in ctx.get("existing_edges", [])}
            results = []
            for edge in ctx.get("edges", []):
                key = (_norm(edge.get("subject", "")), _norm(edge.get("predicate", "")), _norm(edge.get("object", "")))
                results.append({"duplicate": key in existing, "valid_at": edge.get("valid_at")})
            data = {"results": results}

        elif op == "extract_timestamps":
            edge = ctx.get("edge", {})
            data = {"valid_at": edge.get("valid_at"), "invalid_at": edge.get("invalid_at")}

        elif op == "extract_attributes":
            # matches Graphiti: plain Entity nodes get {} (and the pipeline skips the call)
            data = {"attributes": ctx.get("node", {}).get("attributes", {})}

        elif op == "summarize":
            name = ctx.get("node", {}).get("name", "entity")
            data = {"summary": f"{name}: mentioned in episode {ctx.get('episode_id', '?')}."}

        else:
            data = {}

        prompt_text = " ".join(m.get("content", "") for m in messages) + str(context or "")
        out_text = str(data)
        usage = Usage(prompt_tokens=est_tokens(prompt_text), completion_tokens=est_tokens(out_text))
        result = BackendResult(data=data, model=model, usage=usage, text=out_text)
        # attach deterministic latency for the caller to record
        result_latency = self._latency(model_size, usage.completion_tokens, prompt_text[:64] + op)
        result._latency_ms = result_latency
        return result

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        # deterministic tiny embedding: 16-dim from a hash, L2-ish normalized
        out: list[list[float]] = []
        for t in texts:
            h = hashlib.md5(_norm(t).encode()).digest()
            vec = [((b / 255.0) * 2 - 1) for b in h[:16]]
            out.append(vec)
        return out
