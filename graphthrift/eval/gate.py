"""Quality gate — decides whether an optimization is SAFE to apply.

An optimization passes only if candidate quality holds within epsilon of the
frozen baseline on BOTH entity-F1 and triple-F1. This is what turns 'we cut cost'
into 'we cut cost, proven safe'.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GateResult:
    passed: bool
    epsilon: float
    entity_f1_delta: float
    triple_f1_delta: float
    reasons: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "epsilon": self.epsilon,
            "entity_f1_delta": round(self.entity_f1_delta, 4),
            "triple_f1_delta": round(self.triple_f1_delta, 4),
            "reasons": self.reasons,
        }


def evaluate_gate(baseline_eval: dict, candidate_eval: dict, epsilon: float = 0.02) -> GateResult:
    e_delta = candidate_eval["entity"]["f1"] - baseline_eval["entity"]["f1"]
    t_delta = candidate_eval["triple"]["f1"] - baseline_eval["triple"]["f1"]
    reasons: list[str] = []
    passed = True
    if e_delta < -epsilon:
        passed = False
        reasons.append(f"entity F1 dropped {e_delta:+.3f} (> epsilon {epsilon})")
    if t_delta < -epsilon:
        passed = False
        reasons.append(f"triple F1 dropped {t_delta:+.3f} (> epsilon {epsilon})")
    if passed:
        reasons.append(f"quality preserved within epsilon {epsilon} (entity {e_delta:+.3f}, triple {t_delta:+.3f})")
    return GateResult(passed=passed, epsilon=epsilon, entity_f1_delta=e_delta, triple_f1_delta=t_delta, reasons=reasons)
