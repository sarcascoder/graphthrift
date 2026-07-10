"""GraphThrift — profile, optimize, and safely shrink the LLM cost & latency of
knowledge-graph ingestion pipelines (Graphiti-first)."""
from __future__ import annotations

from graphthrift.eval.gate import evaluate_gate
from graphthrift.eval.metrics import evaluate_graph, graph_diff
from graphthrift.instrument.tracing import CallRecord, RunTrace
from graphthrift.integrations import wrap
from graphthrift.optimize.config import OptimizerConfig

__version__ = "0.1.0"
__all__ = [
    "wrap",
    "OptimizerConfig",
    "RunTrace",
    "CallRecord",
    "evaluate_graph",
    "graph_diff",
    "evaluate_gate",
    "__version__",
]
