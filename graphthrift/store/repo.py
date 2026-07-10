"""Repository helpers for persisting and querying runs."""
from __future__ import annotations

import json
import uuid
from typing import Any

from graphthrift.store.db import session_scope
from graphthrift.store.models import Run


def save_run(report: dict[str, Any], *, scenario: str, backend: str) -> str:
    run_id = uuid.uuid4().hex[:12]
    s = report.get("savings", {})
    with session_scope() as db:
        db.add(Run(
            run_id=run_id,
            label=report.get("candidate_label", scenario),
            scenario=scenario,
            backend=backend,
            gate_passed=bool(report.get("gate", {}).get("passed", False)),
            cost_reduction_pct=float(s.get("cost_reduction_pct", 0.0)),
            latency_reduction_pct=float(s.get("latency_reduction_pct", 0.0)),
            calls_reduction_pct=float(s.get("llm_calls_reduction_pct", 0.0)),
            n_episodes=int(report.get("n_episodes", 0)),
            report_json=json.dumps(report),
        ))
    return run_id


def list_runs(limit: int = 50) -> list[dict]:
    with session_scope() as db:
        rows = db.query(Run).order_by(Run.created_at.desc()).limit(limit).all()
        return [r.summary_row() for r in rows]


def get_run(run_id: str) -> dict | None:
    with session_scope() as db:
        r = db.get(Run, run_id)
        if r is None:
            return None
        return {**r.summary_row(), "report": r.report}
