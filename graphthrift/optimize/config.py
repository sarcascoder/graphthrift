"""Optimizer configuration — toggles for the whole chain."""
from __future__ import annotations

from dataclasses import asdict, dataclass

from graphthrift.config import Settings, get_settings


@dataclass
class OptimizerConfig:
    cache_enabled: bool = False
    embedding_cache_enabled: bool = False
    router_enabled: bool = False
    dedup_prefilter_enabled: bool = False
    edge_batcher_enabled: bool = False
    compressor_enabled: bool = False
    # Stages the router is allowed to DOWNGRADE medium->small. Empty = honor-only
    # (fixes the Anthropic 'ignores model_size' bug without degrading quality).
    router_downgrade_stages: tuple[str, ...] = ()
    # near-duplicate cosine threshold for the dedup prefilter
    dedup_threshold: float = 0.97

    @classmethod
    def baseline(cls) -> OptimizerConfig:
        return cls()  # everything off

    @classmethod
    def safe(cls, settings: Settings | None = None) -> OptimizerConfig:
        """The recommended config: big savings, zero quality change."""
        s = settings or get_settings()
        return cls(
            cache_enabled=s.cache_enabled,
            embedding_cache_enabled=s.embedding_cache_enabled,
            router_enabled=s.router_enabled,          # honor-only (no downgrade stages)
            dedup_prefilter_enabled=s.dedup_prefilter_enabled,
            edge_batcher_enabled=s.edge_batcher_enabled,
            compressor_enabled=s.compressor_enabled,
        )

    @classmethod
    def aggressive(cls) -> OptimizerConfig:
        """Cautionary config: also downgrades extraction to the small model.
        Cuts more cost but hurts quality — the gate should REJECT this."""
        c = cls.safe()
        c.router_enabled = True
        c.router_downgrade_stages = ("extract_nodes", "extract_edges")
        return c

    def as_dict(self) -> dict:
        return asdict(self)
