"""Extraction-quality metrics — the credible measurement Graphiti's repo lacks.

Graphiti ships only a *relative* pairwise LLM-as-judge; there is no gold-graph
precision/recall/F1 anywhere in the repo or paper. This module adds intrinsic
entity-level and triple-level P/R/F1 (with fuzzy matching) plus a graph diff, so
an optimization can be proven to preserve quality, not merely assumed to.
"""
from __future__ import annotations

from collections.abc import Callable
from difflib import SequenceMatcher
from typing import Any

FUZZY = 0.9


def _norm(s: str) -> str:
    return " ".join(str(s).lower().split())


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def entity_match(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return _norm(a["name"]) == _norm(b["name"]) or _sim(a["name"], b["name"]) >= FUZZY


def triple_match(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        _norm(a["predicate"]) == _norm(b["predicate"])
        and _sim(a["subject"], b["subject"]) >= FUZZY
        and _sim(a["object"], b["object"]) >= FUZZY
    )


def _match_sets(pred: list, gold: list, is_match: Callable) -> tuple[int, int, int]:
    matched: set[int] = set()
    tp = 0
    for p in pred:
        for i, g in enumerate(gold):
            if i in matched:
                continue
            if is_match(p, g):
                matched.add(i)
                tp += 1
                break
    return tp, len(pred) - tp, len(gold) - tp


def prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
            "tp": tp, "fp": fp, "fn": fn}


def evaluate_graph(pred: dict[str, Any], gold: dict[str, Any]) -> dict[str, Any]:
    e = prf(*_match_sets(pred.get("entities", []), gold.get("entities", []), entity_match))
    t = prf(*_match_sets(pred.get("triples", []), gold.get("triples", []), triple_match))
    return {"entity": e, "triple": t}


def graph_diff(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """What changed going from graph `a` (baseline) to `b` (candidate)."""
    a_ents = {_norm(x["name"]) for x in a.get("entities", [])}
    b_ents = {_norm(x["name"]) for x in b.get("entities", [])}
    a_tr = {(_norm(x["subject"]), _norm(x["predicate"]), _norm(x["object"])) for x in a.get("triples", [])}
    b_tr = {(_norm(x["subject"]), _norm(x["predicate"]), _norm(x["object"])) for x in b.get("triples", [])}
    return {
        "entities_added": len(b_ents - a_ents),
        "entities_removed": len(a_ents - b_ents),
        "triples_added": len(b_tr - a_tr),
        "triples_removed": len(a_tr - b_tr),
        "identical": a_ents == b_ents and a_tr == b_tr,
    }
