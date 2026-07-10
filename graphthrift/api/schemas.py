"""API request/response schemas."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ConfigOverrides(BaseModel):
    cache_enabled: bool | None = None
    embedding_cache_enabled: bool | None = None
    router_enabled: bool | None = None
    dedup_prefilter_enabled: bool | None = None
    edge_batcher_enabled: bool | None = None
    compressor_enabled: bool | None = None
    router_downgrade_stages: list[str] | None = None


class RunRequest(BaseModel):
    scenario: Literal["safe", "aggressive", "custom"] = "safe"
    monthly_volume: int = Field(1_000_000, ge=0, description="episodes/month for savings projection")
    epsilon: float | None = Field(None, ge=0, le=1, description="allowed F1 drop before flagged unsafe")
    overrides: ConfigOverrides | None = None


class RunSummary(BaseModel):
    run_id: str
    label: str
    scenario: str
    backend: str
    gate_passed: bool
    cost_reduction_pct: float
    latency_reduction_pct: float
    calls_reduction_pct: float
    n_episodes: int
    created_at: str | None


class ConfigResponse(BaseModel):
    backend: str
    quality_epsilon: float
    defaults: dict[str, Any]
