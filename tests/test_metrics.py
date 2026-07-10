from graphthrift.eval.metrics import evaluate_graph, graph_diff, prf, triple_match


def test_prf_perfect():
    r = prf(tp=5, fp=0, fn=0)
    assert r["precision"] == 1.0 and r["recall"] == 1.0 and r["f1"] == 1.0


def test_prf_partial():
    r = prf(tp=3, fp=1, fn=1)
    assert r["precision"] == 0.75 and r["recall"] == 0.75 and r["f1"] == 0.75


def test_triple_match_fuzzy():
    a = {"subject": "Acme Corp", "predicate": "EMPLOYS", "object": "Alice"}
    b = {"subject": "Acme  Corp", "predicate": "employs", "object": "Alice"}
    assert triple_match(a, b)


def test_evaluate_graph_and_diff():
    gold = {"entities": [{"name": "A", "type": "X"}, {"name": "B", "type": "X"}],
            "triples": [{"subject": "A", "predicate": "R", "object": "B"}]}
    pred = {"entities": [{"name": "A", "type": "X"}],
            "triples": []}
    res = evaluate_graph(pred, gold)
    assert res["entity"]["recall"] == 0.5
    assert res["triple"]["tp"] == 0
    diff = graph_diff(gold, pred)
    assert diff["entities_removed"] == 1 and diff["triples_removed"] == 1 and not diff["identical"]
