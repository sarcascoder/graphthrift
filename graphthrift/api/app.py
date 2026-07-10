"""FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from graphthrift import __version__
from graphthrift.api import metrics
from graphthrift.api.routers import meta, runs
from graphthrift.config import get_settings
from graphthrift.logging import configure_logging, get_logger
from graphthrift.store import init_db

log = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    s = get_settings()
    configure_logging(s.log_level, s.log_json)
    init_db()
    log.info("graphthrift.startup", version=__version__, backend=s.backend)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="GraphThrift API",
        version=__version__,
        description="Profile, optimize, and safely shrink the LLM cost & latency of "
                    "knowledge-graph ingestion pipelines (Graphiti-first).",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(runs.router)
    app.include_router(meta.router)

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/readyz", tags=["meta"])
    async def readyz() -> dict:
        # touch the DB to confirm readiness
        from graphthrift.store import list_runs

        list_runs(limit=1)
        return {"status": "ready"}

    @app.get("/metrics", response_class=PlainTextResponse, tags=["meta"])
    async def prometheus() -> str:
        return metrics.render()

    @app.get("/", tags=["meta"])
    async def root() -> dict:
        return {"name": "graphthrift", "version": __version__, "docs": "/docs"}

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception) -> JSONResponse:
        log.error("unhandled_error", path=str(request.url), error=str(exc))
        metrics.inc("errors_total")
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    return app


app = create_app()
