"""Central configuration, loaded from environment / .env (12-factor)."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GRAPHTHRIFT_", env_file=".env", extra="ignore")

    # --- Backend selection ---
    backend: Literal["fake", "ollama", "openai"] = "fake"

    # Ollama (local, key-free default path)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_small_model: str = "qwen2.5:0.5b"
    ollama_embed_model: str = "nomic-embed-text"

    # OpenAI-compatible (real-numbers path)
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.5"
    openai_small_model: str = "gpt-4.1-nano"
    openai_embed_model: str = "text-embedding-3-small"

    # --- Storage ---
    database_url: str = "sqlite:///./graphthrift_data/graphthrift.sqlite3"

    # --- API auth ---
    api_key: str | None = None  # if set, X-API-Key required on mutating routes
    auth_enabled: bool = False

    # --- Optimizer defaults ---
    cache_enabled: bool = True
    embedding_cache_enabled: bool = True
    router_enabled: bool = True
    dedup_prefilter_enabled: bool = True
    edge_batcher_enabled: bool = True
    compressor_enabled: bool = True

    # --- Eval gate ---
    quality_epsilon: float = 0.02  # allowed F1 drop before an optimization is flagged unsafe

    # --- Concurrency (mirrors Graphiti SEMAPHORE_LIMIT default of 20) ---
    max_concurrency: int = 20

    # --- Logging ---
    log_level: str = "INFO"
    log_json: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
