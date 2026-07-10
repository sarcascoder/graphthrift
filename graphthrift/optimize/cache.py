"""Response + embedding caches.

Graphiti ships an LLMCache that is *off by default* and has *no embedding cache*.
GraphThrift enables a response cache keyed on (prompt_name + normalized messages +
salient context) and adds an embedding cache keyed on normalized text.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


def _key(prompt_name: str, messages: list[dict[str, str]], salient: Any = None) -> str:
    blob = json.dumps(
        {"p": prompt_name, "m": [(m.get("role"), m.get("content")) for m in messages], "s": salient},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(blob.encode()).hexdigest()


class ResponseCache:
    def __init__(self) -> None:
        self._store: dict[str, dict] = {}
        self.hits = 0
        self.misses = 0

    def get(self, prompt_name: str, messages: list[dict[str, str]], salient: Any = None) -> dict | None:
        k = _key(prompt_name, messages, salient)
        v = self._store.get(k)
        if v is None:
            self.misses += 1
            return None
        self.hits += 1
        return v

    def put(self, prompt_name: str, messages: list[dict[str, str]], value: dict, salient: Any = None) -> None:
        self._store[_key(prompt_name, messages, salient)] = value


class EmbeddingCache:
    def __init__(self) -> None:
        self._store: dict[str, list[float]] = {}
        self.hits = 0
        self.misses = 0

    @staticmethod
    def _norm(t: str) -> str:
        return " ".join(t.lower().split())

    def get_many(self, texts: list[str]) -> tuple[list[list[float] | None], list[int]]:
        """Return (results-with-None-for-misses, indices-needing-compute)."""
        results: list[list[float] | None] = []
        missing: list[int] = []
        for i, t in enumerate(texts):
            v = self._store.get(self._norm(t))
            if v is None:
                self.misses += 1
                missing.append(i)
                results.append(None)
            else:
                self.hits += 1
                results.append(v)
        return results, missing

    def put(self, text: str, vec: list[float]) -> None:
        self._store[self._norm(text)] = vec
