"""Model router — honor `model_size` and optionally downgrade easy stages.

Two jobs:
  1. HONOR small/medium tiers. Graphiti's Anthropic client accepts `model_size`
     but ignores it, so those high-volume small calls silently run on the full
     model. Routing here guarantees the small tier is used.
  2. Optionally DOWNGRADE configured medium stages to small. This cuts cost but
     can hurt quality, which is exactly why the eval gate exists.
"""
from __future__ import annotations

from graphthrift.optimize.config import OptimizerConfig


class ModelRouter:
    def __init__(self, config: OptimizerConfig) -> None:
        self.cfg = config

    def route(self, stage: str, requested_size: str) -> tuple[str, bool]:
        """Return (effective_size, downgraded)."""
        if not self.cfg.router_enabled:
            return requested_size, False
        if requested_size == "medium" and stage in self.cfg.router_downgrade_stages:
            return "small", True
        return requested_size, False
