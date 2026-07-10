import pytest

from graphthrift.backends import build_backend
from graphthrift.demo.data.dataset import EPISODES, gold_graph
from graphthrift.demo.pipeline import ingest_corpus
from graphthrift.eval.metrics import graph_diff
from graphthrift.optimize.config import OptimizerConfig
from graphthrift.runner import run_comparison, run_demo

pytestmark = pytest.mark.asyncio


async def test_safe_config_produces_identical_graph():
    backend = build_backend()
    base_g, _ = await ingest_corpus(backend, EPISODES, OptimizerConfig.baseline(), "baseline")
    safe_g, _ = await ingest_corpus(backend, EPISODES, OptimizerConfig.safe(), "safe")
    assert graph_diff(base_g.as_graph(), safe_g.as_graph())["identical"] is True


async def test_safe_reduces_calls_and_passes_gate():
    r = await run_demo("safe")
    assert r["savings"]["llm_calls_reduction_pct"] > 0
    assert r["savings"]["cost_reduction_pct"] > 0
    assert r["gate"]["passed"] is True
    assert r["graph_diff"]["identical"] is True


async def test_aggressive_fails_gate():
    r = await run_demo("aggressive")
    assert r["gate"]["passed"] is False
    assert r["candidate"]["eval"]["triple"]["f1"] < r["baseline"]["eval"]["triple"]["f1"]


async def test_run_comparison_shapes():
    backend = build_backend()
    r = await run_comparison(backend, EPISODES, gold_graph(), OptimizerConfig.safe(), candidate_label="safe")
    for key in ("baseline", "candidate", "savings", "gate", "graph_diff", "verdict"):
        assert key in r
    assert r["candidate"]["trace"]["calls_eliminated"] > 0
