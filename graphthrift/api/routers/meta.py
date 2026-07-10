"""Config + health + dataset metadata routes."""
from __future__ import annotations

from fastapi import APIRouter

from graphthrift.api.schemas import ConfigResponse
from graphthrift.config import get_settings
from graphthrift.demo.data.dataset import EPISODES, gold_graph
from graphthrift.optimize.config import OptimizerConfig

router = APIRouter(tags=["meta"])


@router.get("/v1/config", response_model=ConfigResponse, summary="Active backend + optimizer defaults")
async def get_config() -> ConfigResponse:
    s = get_settings()
    return ConfigResponse(
        backend=s.backend,
        quality_epsilon=s.quality_epsilon,
        defaults=OptimizerConfig.safe(s).as_dict(),
    )


@router.get("/v1/dataset", summary="Demo dataset stats")
async def get_dataset() -> dict:
    gold = gold_graph()
    return {
        "episodes": len(EPISODES),
        "gold_entities": len(gold["entities"]),
        "gold_triples": len(gold["triples"]),
        "description": "Agent-memory conversation stream (Graphiti's core use case).",
    }
