"""Edge batcher — collapse the per-edge resolve/timestamp fan-out into one call.

This targets the dominant cost term identified in the Graphiti teardown:
`resolve_extracted_edge` fires once PER EDGE (E calls) and `extract_timestamps`
once per NEW edge (Enew calls), both per-item. Batching them into a single call
(the node-dedup path already proves batched resolution works) turns E + Enew
calls into 1, with identical resolution decisions.
"""
from __future__ import annotations

from typing import Any


class EdgeBatcher:
    @staticmethod
    def build_context(edges: list[dict[str, Any]], existing_edges: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "op": "resolve_edges_batch",
            "edges": edges,
            "existing_edges": existing_edges,
        }

    @staticmethod
    def split(result: dict[str, Any], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Map the batched result back to per-edge decisions (aligned by index)."""
        decisions = result.get("results", [])
        out = []
        for i, edge in enumerate(edges):
            d = decisions[i] if i < len(decisions) else {}
            out.append({**edge, "duplicate": d.get("duplicate", False),
                        "valid_at": d.get("valid_at", edge.get("valid_at"))})
        return out
