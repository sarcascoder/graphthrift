"""ORM models. One row per comparison run, storing the full report JSON."""
from __future__ import annotations

import json
from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from graphthrift.store.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Run(Base):
    __tablename__ = "runs"

    run_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    label: Mapped[str] = mapped_column(String(64), default="optimized")
    scenario: Mapped[str] = mapped_column(String(32), default="safe")
    backend: Mapped[str] = mapped_column(String(16), default="fake")
    gate_passed: Mapped[bool] = mapped_column(default=False)
    cost_reduction_pct: Mapped[float] = mapped_column(Float, default=0.0)
    latency_reduction_pct: Mapped[float] = mapped_column(Float, default=0.0)
    calls_reduction_pct: Mapped[float] = mapped_column(Float, default=0.0)
    n_episodes: Mapped[int] = mapped_column(Integer, default=0)
    report_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    @property
    def report(self) -> dict:
        return json.loads(self.report_json)

    def summary_row(self) -> dict:
        return {
            "run_id": self.run_id,
            "label": self.label,
            "scenario": self.scenario,
            "backend": self.backend,
            "gate_passed": self.gate_passed,
            "cost_reduction_pct": self.cost_reduction_pct,
            "latency_reduction_pct": self.latency_reduction_pct,
            "calls_reduction_pct": self.calls_reduction_pct,
            "n_episodes": self.n_episodes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
