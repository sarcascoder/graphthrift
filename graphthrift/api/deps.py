"""Shared API dependencies (auth)."""
from __future__ import annotations

from fastapi import Header, HTTPException, status

from graphthrift.config import get_settings


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Enforce X-API-Key on mutating routes when auth is enabled."""
    s = get_settings()
    if not s.auth_enabled:
        return
    if not s.api_key or x_api_key != s.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or missing X-API-Key")
