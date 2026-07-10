"""OpenAI-compatible backend — the 'real cost numbers' path (OpenAI, vLLM, etc.)."""
from __future__ import annotations

import json
from typing import Any

import httpx

from graphthrift.backends.base import BackendResult, LLMBackend, Usage, est_tokens


class OpenAICompatBackend(LLMBackend):
    name = "openai"

    def __init__(self, base_url: str, api_key: str | None, medium: str, small: str, embed: str, timeout: float = 120.0):
        self._base = base_url.rstrip("/")
        self._key = api_key
        self._medium = medium
        self._small = small
        self._embed = embed
        self._timeout = timeout

    def model_for(self, model_size: str) -> str:
        return self._small if model_size == "small" else self._medium

    @property
    def _headers(self) -> dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self._key:
            h["Authorization"] = f"Bearer {self._key}"
        return h

    async def generate(
        self,
        *,
        messages: list[dict[str, str]],
        model: str,
        model_size: str = "medium",
        response_schema: dict[str, Any] | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.0,
        context: dict[str, Any] | None = None,
    ) -> BackendResult:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "extraction", "schema": response_schema, "strict": False},
            }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base}/chat/completions", json=payload, headers=self._headers)
            resp.raise_for_status()
            body = resp.json()
        content = body["choices"][0]["message"]["content"] or ""
        data = _safe_json(content)
        u = body.get("usage", {})
        usage = Usage(
            prompt_tokens=u.get("prompt_tokens") or est_tokens(str(messages)),
            completion_tokens=u.get("completion_tokens") or est_tokens(content),
        )
        return BackendResult(data=data, model=model, usage=usage, text=content)

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        model = model or self._embed
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                f"{self._base}/embeddings", json={"model": model, "input": texts}, headers=self._headers
            )
            resp.raise_for_status()
            body = resp.json()
        return [d["embedding"] for d in body["data"]]


def _safe_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"_raw": text}
