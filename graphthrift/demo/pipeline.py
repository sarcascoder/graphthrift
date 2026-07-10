"""Faithful offline reproduction of Graphiti's add_episode call graph.

Per episode it fires the same ordered stages the teardown found (§7 of the PRD):
  extract_nodes -> (embed) -> dedupe_nodes(0/1) -> extract_edges -> (embed)
  -> [dedup prefilter] -> resolve_edge (E, or 1 batched) -> extract_timestamps
  (Enew, or folded) -> extract_attributes(Nc) -> summaries(ceil(Ns/30)).

Optimizer toggles change *which* calls fire; eliminated calls are accounted so
the dashboard can show calls saved. The resulting graph is identical between
baseline and the SAFE optimized config, and smaller under aggressive routing.
"""
from __future__ import annotations

from typing import Any

from graphthrift.demo.graph import GraphState, norm
from graphthrift.demo.prompts import system_prompt
from graphthrift.instrument.engine import InstrumentedLLM
from graphthrift.optimize.config import OptimizerConfig
from graphthrift.optimize.dedup_prefilter import DedupPrefilter
from graphthrift.optimize.edge_batcher import EdgeBatcher

# Detailed schemas so REAL backends (Ollama/OpenAI) return the exact shape the
# pipeline consumes. The simulator ignores schemas, so this is a no-op for it.
NODE_SCHEMA = {
    "type": "object",
    "properties": {
        "entities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "type": {"type": "string"}},
                "required": ["name"],
            },
        }
    },
    "required": ["entities"],
}
EDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "subject": {"type": "string"},
                    "predicate": {"type": "string"},
                    "object": {"type": "string"},
                },
                "required": ["subject", "predicate", "object"],
            },
        }
    },
    "required": ["edges"],
}
SUMMARY_BATCH = 30  # Graphiti's MAX_NODES


def _msgs(prompt_name: str, user_content: str) -> list[dict[str, str]]:
    """Build [system, user] messages with the realistic large fixed system prefix."""
    return [
        {"role": "system", "content": system_prompt(prompt_name)},
        {"role": "user", "content": user_content},
    ]


async def ingest_episode(
    instr: InstrumentedLLM, episode: dict[str, Any], graph: GraphState, cfg: OptimizerConfig
) -> None:
    ep_id = episode["id"]
    text = episode["text"]

    # 1. extract_nodes (medium)
    node_res = await instr.call(
        stage="extract_nodes", prompt_name="extract_nodes.extract_message",
        messages=_msgs("extract_nodes.extract_message", f"Extract entities from episode: {text}"),
        model_size="medium", response_schema=NODE_SCHEMA,
        context={"op": "extract_nodes", "episode": episode},
        cacheable=True, cache_salient=f"nodes::{norm(text)}",
    )
    entities = node_res.get("entities", [])

    # 2. embed node names for dedup candidate search
    if entities:
        await instr.embed([e["name"] for e in entities], stage="embed_nodes", prompt_name="embed.node_names")

    # 3. node dedup escalation: 0 or 1 batched call (only if >=2 genuinely-new nodes)
    new_nodes = [e for e in entities if norm(e["name"]) not in graph.nodes]
    if len(new_nodes) >= 2:
        await instr.call(
            stage="dedupe_nodes", prompt_name="dedupe_nodes.nodes",
            messages=_msgs("dedupe_nodes.nodes", f"Resolve duplicate nodes among {len(new_nodes)}"),
            model_size="medium", context={"op": "noop"}, cacheable=False,
        )
    for e in entities:
        graph.add_node(e)

    # 4. extract_edges (medium)
    edge_res = await instr.call(
        stage="extract_edges", prompt_name="extract_edges.edge",
        messages=_msgs("extract_edges.edge", f"Extract relationships from episode: {text}"),
        model_size="medium", response_schema=EDGE_SCHEMA,
        context={"op": "extract_edges", "episode": episode},
        cacheable=True, cache_salient=f"edges::{norm(text)}",
    )
    edges = edge_res.get("edges", [])

    # 5. embed edge facts
    edge_vecs: list[list[float]] = []
    if edges:
        edge_vecs = await instr.embed(
            [f'{e["subject"]} {e["predicate"]} {e["object"]}' for e in edges],
            stage="embed_edges", prompt_name="embed.edge_facts",
        )

    existing = graph.existing_edge_list()

    # 6. dedup prefilter (classical NLP, zero LLM) — drops restated facts pre-LLM
    if cfg.dedup_prefilter_enabled and edges:
        pref = DedupPrefilter(cfg.dedup_threshold)
        unique, dups = pref.partition(edges, existing=existing, embeddings=edge_vecs)
        if dups:
            instr.record_eliminated("resolve_edge", "dedupe_edges.resolve_edge", n=len(dups))
    else:
        unique = edges

    # 7. resolve edges (+ timestamps for new edges)
    if cfg.edge_batcher_enabled and unique:
        batch_ctx = EdgeBatcher.build_context(unique, existing)
        res = await instr.call(
            stage="resolve_edge", prompt_name="dedupe_edges.resolve_edge",
            messages=_msgs("dedupe_edges.resolve_edge", f"Resolve and timestamp {len(unique)} edges"),
            model_size="small", context=batch_ctx, cacheable=False,
        )
        resolved = EdgeBatcher.split(res, unique)
        # E-1 per-edge resolve calls + all timestamp calls folded into the one batch call
        instr.record_eliminated("resolve_edge", "dedupe_edges.resolve_edge", n=max(0, len(unique) - 1))
        new_after = [r for r in resolved if not r.get("duplicate") and not graph.has_edge(r)]
        instr.record_eliminated("extract_timestamps", "extract_edges.extract_timestamps", n=len(new_after))
    else:
        resolved = []
        for edge in unique:
            r = await instr.call(
                stage="resolve_edge", prompt_name="dedupe_edges.resolve_edge",
                messages=_msgs("dedupe_edges.resolve_edge", f"Is this edge a duplicate? {edge}"),
                model_size="small",
                context={"op": "resolve_edge", "edge": edge, "existing_edges": existing},
                cacheable=False,
            )
            e2 = {**edge, "duplicate": r.get("duplicate", False)}
            resolved.append(e2)
            if not e2["duplicate"] and not graph.has_edge(e2):
                await instr.call(
                    stage="extract_timestamps", prompt_name="extract_edges.extract_timestamps",
                    messages=_msgs("extract_edges.extract_timestamps", f"Extract validity dates for edge {edge}"),
                    model_size="small", context={"op": "extract_timestamps", "edge": edge}, cacheable=False,
                )

    # 8. commit new (non-duplicate) edges
    for r in resolved:
        if not r.get("duplicate"):
            graph.add_edge(r)

    # 9. node summaries: batched, ceil(Ns / 30)
    if new_nodes:
        for start in range(0, len(new_nodes), SUMMARY_BATCH):
            chunk = new_nodes[start : start + SUMMARY_BATCH]
            names = ",".join(n["name"] for n in chunk)
            await instr.call(
                stage="summarize", prompt_name="extract_nodes.extract_summaries_batch",
                messages=_msgs("extract_nodes.extract_summaries_batch", f"Summarize nodes: {names}"),
                model_size="small", context={"op": "summarize", "episode_id": ep_id, "node": chunk[0]},
                cacheable=True, cache_salient=f"summary::{norm(names)}",
            )


async def ingest_corpus(
    backend, episodes: list[dict[str, Any]], cfg: OptimizerConfig, label: str
) -> tuple[GraphState, Any]:
    """Run the whole corpus through one config; return (built graph, trace)."""
    from graphthrift.instrument.tracing import RunTrace

    trace = RunTrace(label=label)
    graph = GraphState()
    instr = InstrumentedLLM(backend, cfg, trace)
    for ep in episodes:
        await ingest_episode(instr, ep, graph, cfg)
    trace.close()
    return graph, trace
