"""Minimal Prometheus-style metrics without a hard prometheus_client dep."""
from __future__ import annotations

from collections import defaultdict

_counters: dict[str, float] = defaultdict(float)


def inc(name: str, value: float = 1.0, **labels: str) -> None:
    _counters[_key(name, labels)] += value


def observe(name: str, value: float, **labels: str) -> None:
    _counters[_key(name, labels)] = value


def _key(name: str, labels: dict[str, str]) -> str:
    if not labels:
        return name
    lbl = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f"{name}{{{lbl}}}"


def render() -> str:
    lines = ["# GraphThrift metrics"]
    for k, v in sorted(_counters.items()):
        lines.append(f"graphthrift_{k} {v}")
    return "\n".join(lines) + "\n"
