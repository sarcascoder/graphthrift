"""Run + trace + eval routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from graphthrift.api import metrics
from graphthrift.api.deps import require_api_key
from graphthrift.api.schemas import RunRequest, RunSummary
from graphthrift.api.service import run_and_persist
from graphthrift.logging import get_logger
from graphthrift.store import get_run, list_runs

router = APIRouter(prefix="/v1", tags=["runs"])
log = get_logger()


@router.post("/runs", summary="Run a baseline-vs-optimized comparison and persist it")
async def create_run(req: RunRequest, _: None = Depends(require_api_key)) -> dict:
    report = await run_and_persist(req)
    metrics.inc("runs_total", scenario=req.scenario)
    metrics.inc("runs_gate_passed_total" if report["gate"]["passed"] else "runs_gate_failed_total")
    metrics.observe("last_cost_reduction_pct", report["savings"]["cost_reduction_pct"])
    log.info("run.created", run_id=report["run_id"], scenario=req.scenario,
             gate_passed=report["gate"]["passed"], cost_reduction=report["savings"]["cost_reduction_pct"])
    return report


@router.get("/runs", response_model=list[RunSummary], summary="List recent runs")
async def get_runs(limit: int = Query(50, ge=1, le=200)) -> list[dict]:
    return list_runs(limit=limit)


@router.get("/runs/{run_id}", summary="Full report for a run")
async def get_run_detail(run_id: str) -> dict:
    row = get_run(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    return row


@router.get("/runs/{run_id}/traces", summary="Per-stage trace breakdown for a run")
async def get_run_traces(run_id: str) -> dict:
    row = get_run(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="run not found")
    report = row["report"]
    return {
        "run_id": run_id,
        "baseline_by_stage": report["baseline"]["trace"]["by_stage"],
        "candidate_by_stage": report["candidate"]["trace"]["by_stage"],
    }
