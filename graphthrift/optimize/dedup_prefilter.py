"""Near-duplicate edge prefilter — classical NLP, zero LLM cost.

Mirrors Zep's own '30x' approach: replace LLM calls with cheap deterministic
signals (here: exact-triple match + cosine on edge-fact embeddings) to drop
verbatim/near-duplicate edges *before* the expensive per-edge `resolve_edge` LLM
call. Because it only removes true duplicates, final graph quality is unchanged.
"""
from __future__ import annotations

import math
from typing import Any


def _norm(s: str) -> str:
    return " ".join(str(s).lower().split())


def triple_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (_norm(edge.get("subject", "")), _norm(edge.get("predicate", "")), _norm(edge.get("object", "")))


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


class DedupPrefilter:
    def __init__(self, threshold: float = 0.97) -> None:
        self.threshold = threshold

    def partition(
        self,
        edges: list[dict[str, Any]],
        existing: list[dict[str, Any]] | None = None,
        embeddings: list[list[float]] | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Split incoming edges into (unique, duplicates).

        Duplicates = exact triple match against existing/among-batch, or cosine
        similarity >= threshold to an already-kept edge (if embeddings supplied).
        """
        existing_keys = {triple_key(e) for e in (existing or [])}
        unique: list[dict[str, Any]] = []
        dups: list[dict[str, Any]] = []
        kept_vecs: list[list[float]] = []
        for i, edge in enumerate(edges):
            k = triple_key(edge)
            if k in existing_keys:
                dups.append(edge)
                continue
            vec = embeddings[i] if embeddings and i < len(embeddings) else None
            if vec is not None and any(cosine(vec, kv) >= self.threshold for kv in kept_vecs):
                dups.append(edge)
                continue
            unique.append(edge)
            existing_keys.add(k)
            if vec is not None:
                kept_vecs.append(vec)
        return unique, dups
