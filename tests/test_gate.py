from graphthrift.eval.gate import evaluate_gate


def _mk(entity_f1, triple_f1):
    return {"entity": {"f1": entity_f1}, "triple": {"f1": triple_f1}}


def test_gate_passes_when_within_epsilon():
    g = evaluate_gate(_mk(0.9, 0.9), _mk(0.9, 0.89), epsilon=0.02)
    assert g.passed is True


def test_gate_fails_on_triple_drop():
    g = evaluate_gate(_mk(0.9, 0.9), _mk(0.9, 0.7), epsilon=0.02)
    assert g.passed is False
    assert any("triple" in r for r in g.reasons)


def test_gate_allows_improvement():
    g = evaluate_gate(_mk(0.8, 0.8), _mk(0.9, 0.95), epsilon=0.02)
    assert g.passed is True
    assert g.triple_f1_delta > 0
