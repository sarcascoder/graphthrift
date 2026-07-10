"""Per-call trace records and run-level aggregation.

A `CallRecord` is emitted for every LLM/embedding call. A `RunTrace` collects
them for one ingestion run and computes the cost/latency/coverage summary the
dashboard renders.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from graphthrift.instrument.pricing import cost_usd


@dataclass
class CallRecord:
    stage: str              # e.g. "extract_edges", "resolve_edge"
    prompt_name: str        # Graphiti prompt name
    model: str
    model_size: str         # "small" | "medium"
    prompt_tokens: int
    completion_tokens: int
    latency_ms: float
    cache_hit: bool = False
    routed_from: str | None = None   # original model if ModelRouter downgraded it
    eliminated: bool = False         # counted-but-skipped (dedup prefilter / batching)
    call_type: str = "llm"           # "llm" | "embed"
    ts: float = field(default_factory=time.time)

    @property
    def cost(self) -> float:
        if self.cache_hit or self.eliminated:
            return 0.0
        return cost_usd(self.model, self.prompt_tokens, self.completion_tokens)


@dataclass
class RunTrace:
    label: str = "baseline"
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    records: list[CallRecord] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    finished: float | None = None

    def add(self, rec: CallRecord) -> None:
        self.records.append(rec)

    def close(self) -> None:
        self.finished = time.time()

    # --- aggregates ---
    @property
    def wall_ms(self) -> float:
        return ((self.finished or time.time()) - self.started) * 1000.0

    @property
    def total_cost(self) -> float:
        return sum(r.cost for r in self.records)

    @property
    def total_llm_calls(self) -> int:
        return sum(1 for r in self.records if r.call_type == "llm" and not r.eliminated)

    @property
    def calls_eliminated(self) -> int:
        return sum(1 for r in self.records if r.eliminated)

    @property
    def cache_hits(self) -> int:
        return sum(1 for r in self.records if r.cache_hit)

    @property
    def routed_calls(self) -> int:
        return sum(1 for r in self.records if r.routed_from)

    @property
    def prompt_tokens(self) -> int:
        return sum(r.prompt_tokens for r in self.records if not (r.cache_hit or r.eliminated))

    @property
    def completion_tokens(self) -> int:
        return sum(r.completion_tokens for r in self.records if not (r.cache_hit or r.eliminated))

    @property
    def total_latency_ms(self) -> float:
        """Summed call latency — models Graphiti's sequential-stage ingestion time
        (the 'episode processing 60s->4s' metric), which batching/dedup cut."""
        return sum(r.latency_ms for r in self.records if not r.eliminated)

    def latency_p(self, q: float) -> float:
        lats = sorted(r.latency_ms for r in self.records if not r.eliminated)
        if not lats:
            return 0.0
        idx = min(len(lats) - 1, int(round(q * (len(lats) - 1))))
        return lats[idx]

    def by_stage(self) -> dict[str, dict[str, float]]:
        out: dict[str, dict[str, float]] = {}
        for r in self.records:
            s = out.setdefault(r.stage, {"calls": 0, "cost": 0.0, "latency_ms": 0.0, "eliminated": 0})
            if r.eliminated:
                s["eliminated"] += 1
                continue
            s["calls"] += 1
            s["cost"] += r.cost
            s["latency_ms"] += r.latency_ms
        return out

    def summary(self) -> dict:
        return {
            "run_id": self.run_id,
            "label": self.label,
            "total_cost_usd": round(self.total_cost, 6),
            "total_llm_calls": self.total_llm_calls,
            "calls_eliminated": self.calls_eliminated,
            "cache_hits": self.cache_hits,
            "routed_calls": self.routed_calls,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "wall_ms": round(self.wall_ms, 1),
            "total_latency_ms": round(self.total_latency_ms, 1),
            "latency_p50_ms": round(self.latency_p(0.50), 1),
            "latency_p95_ms": round(self.latency_p(0.95), 1),
            "by_stage": {k: {kk: round(vv, 6) for kk, vv in v.items()} for k, v in self.by_stage().items()},
        }
