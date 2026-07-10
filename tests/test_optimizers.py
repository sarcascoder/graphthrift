from graphthrift.optimize.cache import EmbeddingCache, ResponseCache
from graphthrift.optimize.compressor import PromptCompressor
from graphthrift.optimize.config import OptimizerConfig
from graphthrift.optimize.dedup_prefilter import DedupPrefilter
from graphthrift.optimize.router import ModelRouter


def test_dedup_prefilter_exact_and_existing():
    existing = [{"subject": "Alice", "predicate": "WORKS_AT", "object": "Acme"}]
    edges = [
        {"subject": "Alice", "predicate": "WORKS_AT", "object": "Acme"},   # dup of existing
        {"subject": "Bob", "predicate": "WORKS_AT", "object": "Acme"},     # new
        {"subject": "Bob", "predicate": "WORKS_AT", "object": "Acme"},     # dup within batch
    ]
    uniq, dups = DedupPrefilter().partition(edges, existing=existing)
    assert len(uniq) == 1 and len(dups) == 2


def test_router_honor_only_no_downgrade():
    r = ModelRouter(OptimizerConfig.safe())
    size, downgraded = r.route("extract_edges.edge", "medium")
    assert size == "medium" and downgraded is False


def test_router_aggressive_downgrades_extraction():
    r = ModelRouter(OptimizerConfig.aggressive())
    size, downgraded = r.route("extract_nodes", "medium")
    assert size == "small" and downgraded is True


def test_compressor_prunes_examples_and_shrinks():
    msgs = [{"role": "system", "content": "Do the task.\n<<<EXAMPLES\n" + "x " * 500 + "\n>>>\nEnd."}]
    out = PromptCompressor().compress(msgs)
    assert "EXAMPLES" not in out[0]["content"]
    assert len(out[0]["content"]) < len(msgs[0]["content"])


def test_response_cache_hit_miss():
    c = ResponseCache()
    m = [{"role": "user", "content": "hi"}]
    assert c.get("p", m) is None
    c.put("p", m, {"ok": True})
    assert c.get("p", m) == {"ok": True}
    assert c.hits == 1 and c.misses == 1


def test_embedding_cache_partial():
    c = EmbeddingCache()
    res, missing = c.get_many(["a", "b"])
    assert missing == [0, 1]
    c.put("a", [0.1])
    res, missing = c.get_many(["a", "b"])
    assert res[0] == [0.1] and missing == [1]
