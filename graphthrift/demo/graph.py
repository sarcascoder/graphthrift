"""In-memory knowledge graph accumulated across episodes (Neo4j stand-in)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def norm(s: str) -> str:
    return " ".join(str(s).lower().split())


def triple_key(e: dict[str, Any]) -> tuple[str, str, str]:
    return (norm(e.get("subject", "")), norm(e.get("predicate", "")), norm(e.get("object", "")))


@dataclass
class GraphState:
    nodes: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: dict[tuple[str, str, str], dict[str, Any]] = field(default_factory=dict)

    def add_node(self, node: dict[str, Any]) -> bool:
        k = norm(node["name"])
        is_new = k not in self.nodes
        if is_new:
            self.nodes[k] = {"name": node["name"], "type": node.get("type", "Entity")}
        return is_new

    def has_edge(self, edge: dict[str, Any]) -> bool:
        return triple_key(edge) in self.edges

    def add_edge(self, edge: dict[str, Any]) -> bool:
        k = triple_key(edge)
        is_new = k not in self.edges
        if is_new:
            self.edges[k] = {
                "subject": edge["subject"], "predicate": edge["predicate"],
                "object": edge["object"], "valid_at": edge.get("valid_at"),
            }
        return is_new

    def existing_edge_list(self) -> list[dict[str, Any]]:
        return list(self.edges.values())

    def as_graph(self) -> dict[str, Any]:
        return {
            "entities": [{"name": n["name"], "type": n["type"]} for n in self.nodes.values()],
            "triples": [{"subject": e["subject"], "predicate": e["predicate"], "object": e["object"]}
                        for e in self.edges.values()],
        }
