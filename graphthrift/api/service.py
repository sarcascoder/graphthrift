"""API-facing service layer: turn a request into a persisted comparison run."""
from __future__ import annotations

from typing import Any

from graphthrift.api.schemas import RunRequest
from graphthrift.backends import build_backend
from graphthrift.config import get_settings
from graphthrift.demo.data.dataset import EPISODES, gold_graph
from graphthrift.optimize.config import OptimizerConfig
from graphthrift.runner import run_comparison
from graphthrift.store import save_run


def _config_for(req: RunRequest) -> OptimizerConfig:
    if req.scenario == "aggressive":
        cfg = OptimizerConfig.aggressive()
    else:
        cfg = OptimizerConfig.safe()
    if req.overrides is not None:
        for field, value in req.overrides.model_dump(exclude_none=True).items():
            setattr(cfg, field, tuple(value) if field == "router_downgrade_stages" else value)
    return cfg


async def run_and_persist(req: RunRequest) -> dict[str, Any]:
    s = get_settings()
    backend = build_backend(s)
    cfg = _config_for(req)
    epsilon = req.epsilon if req.epsilon is not None else s.quality_epsilon
    report = await run_comparison(
        backend, EPISODES, gold_graph(), cfg,
        epsilon=epsilon, candidate_label=req.scenario, monthly_volume=req.monthly_volume,
    )
    run_id = save_run(report, scenario=req.scenario, backend=s.backend)
    report["run_id"] = run_id
    return report
