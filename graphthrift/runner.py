"""Orchestrator: run baseline vs a candidate config, eval both, gate, and price."""
from __future__ import annotations

from typing import Any

from graphthrift.backends import build_backend
from graphthrift.backends.base import LLMBackend
from graphthrift.config import get_settings
from graphthrift.demo.data.dataset import EPISODES, gold_graph
from graphthrift.demo.pipeline import ingest_corpus
from graphthrift.eval.gate import evaluate_gate
from graphthrift.eval.metrics import evaluate_graph, graph_diff
from graphthrift.optimize.config import OptimizerConfig


def _pct(base: float, cand: float) -> float:
    return round((1 - cand / base) * 100, 1) if base else 0.0


def _projected_savings(base_cost: float, cand_cost: float, n_episodes: int, monthly_volume: int) -> dict[str, float]:
    per_ep_saved = (base_cost - cand_cost) / n_episodes if n_episodes else 0.0
    return {
        "per_episode_saved_usd": round(per_ep_saved, 6),
        "monthly_volume_episodes": monthly_volume,
        "projected_monthly_saved_usd": round(per_ep_saved * monthly_volume, 2),
    }


async def run_comparison(
    backend: LLMBackend,
    episodes: list[dict[str, Any]],
    gold: dict[str, Any],
    candidate_cfg: OptimizerConfig,
    *,
    epsilon: float = 0.02,
    candidate_label: str = "optimized",
    monthly_volume: int = 1_000_000,
) -> dict[str, Any]:
    base_graph, base_trace = await ingest_corpus(backend, episodes, OptimizerConfig.baseline(), "baseline")
    cand_graph, cand_trace = await ingest_corpus(backend, episodes, candidate_cfg, candidate_label)

    gold = gold or gold_graph()
    base_eval = evaluate_graph(base_graph.as_graph(), gold)
    cand_eval = evaluate_graph(cand_graph.as_graph(), gold)
    gate = evaluate_gate(base_eval, cand_eval, epsilon)
    diff = graph_diff(base_graph.as_graph(), cand_graph.as_graph())

    bs, cs = base_trace.summary(), cand_trace.summary()
    savings = {
        "cost_reduction_pct": _pct(bs["total_cost_usd"], cs["total_cost_usd"]),
        "llm_calls_reduction_pct": _pct(bs["total_llm_calls"], cs["total_llm_calls"]),
        "latency_reduction_pct": _pct(bs["total_latency_ms"], cs["total_latency_ms"]),
        "calls_eliminated": cs["calls_eliminated"],
        "cache_hits": cs["cache_hits"],
        "routed_calls": cs["routed_calls"],
        **_projected_savings(bs["total_cost_usd"], cs["total_cost_usd"], len(episodes), monthly_volume),
    }
    return {
        "candidate_label": candidate_label,
        "config": candidate_cfg.as_dict(),
        "n_episodes": len(episodes),
        "baseline": {"trace": bs, "eval": base_eval},
        "candidate": {"trace": cs, "eval": cand_eval},
        "savings": savings,
        "gate": gate.as_dict(),
        "graph_diff": diff,
        "verdict": "SAFE — apply" if gate.passed else "UNSAFE — flagged, do not apply",
    }


async def run_demo(scenario: str = "safe", monthly_volume: int = 1_000_000) -> dict[str, Any]:
    """Convenience entry point used by the CLI and the API's /demo route."""
    s = get_settings()
    backend = build_backend(s)
    cfg = OptimizerConfig.aggressive() if scenario == "aggressive" else OptimizerConfig.safe(s)
    return await run_comparison(
        backend, EPISODES, gold_graph(), cfg,
        epsilon=s.quality_epsilon, candidate_label=scenario, monthly_volume=monthly_volume,
    )
