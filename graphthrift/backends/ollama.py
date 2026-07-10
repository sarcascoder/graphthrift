"""Local Ollama backend — the default key-free path for real (non-simulated) runs."""
from __future__ import annotations

import json
from typing import Any

import httpx

from graphthrift.backends.base import BackendResult, LLMBackend, Usage, est_tokens


class OllamaBackend(LLMBackend):
    name = "ollama"

    def __init__(self, base_url: str, medium: str, small: str, embed: str, timeout: float = 120.0):
        self._base = base_url.rstrip("/")
        self._medium = medium
        self._small = small
        self._embed = embed
        self._timeout = timeout

    def model_for(self, model_size: str) -> str:
        return self._small if model_size == "small" else self._medium

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
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if response_schema is not None:
            payload["format"] = response_schema  # Ollama accepts a JSON schema for structured output
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(f"{self._base}/api/chat", json=payload)
            resp.raise_for_status()
            body = resp.json()
        content = body.get("message", {}).get("content", "") or ""
        data = _safe_json(content)
        usage = Usage(
            prompt_tokens=body.get("prompt_eval_count") or est_tokens(str(messages)),
            completion_tokens=body.get("eval_count") or est_tokens(content),
        )
        return BackendResult(data=data, model=model, usage=usage, text=content)

    async def embed(self, texts: list[str], model: str | None = None) -> list[list[float]]:
        model = model or self._embed
        out: list[list[float]] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for t in texts:
                resp = await client.post(f"{self._base}/api/embeddings", json={"model": model, "prompt": t})
                resp.raise_for_status()
                out.append(resp.json().get("embedding", []))
        return out


def _safe_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        start, end = text.find("{"), text.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {"_raw": text}
