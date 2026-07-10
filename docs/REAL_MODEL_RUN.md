# Real-model validation (Ollama)

The bundled demo runs on a deterministic simulator by default (offline, key-free).
This document records an actual run against **real local models** to prove the
pipeline, optimizers, eval, and gate work on live inference — not just the sim.

## Setup

- **Host:** Apple M5 Pro (Metal, 17.8 GiB), Ollama 0.31.1
- **Models:** `qwen2.5:3b` (medium/extraction), `qwen2.5:0.5b` (small/dedup·summaries), `nomic-embed-text` (embeddings)
- **Command:** `GRAPHTHRIFT_BACKEND=ollama graphthrift demo --scenario {safe,aggressive}`
- Date: 2026-07-10

## Results

### Safe config (batch + dedup prefilter + cache + compress)

| Metric | Baseline (3b) | Optimized | Δ |
|---|---|---|---|
| LLM calls | 65 | 36 | **−44.6%** |
| Prompt tokens | 18,013 | 2,415 | **−86.6%** |
| Entity F1 | 0.815 | 0.889 | **+0.074** (held/improved) |
| Triple F1 | 0.235 | 0.242 | +0.007 (held) |
| Wall time | 38.4 s | 36.4 s | — |
| — | eliminated calls: 28 | cache hits: 13 | **Gate: PASS ✅** |

Real optimizations cut real calls and tokens on live inference while extraction
quality held (entity F1 even rose slightly).

### Aggressive config (also routes extraction 3b → 0.5b)

| Metric | Baseline (3b) | Aggressive (0.5b) | Δ |
|---|---|---|---|
| Entity F1 | 0.815 | 0.696 | **−0.119** |
| Triple F1 | 0.235 | 0.063 | **−0.173** |
| — | routed calls: 16 | | **Gate: FAIL ❌ — flagged, not applied** |

Routing extraction to the cheaper model measurably degraded quality, and the gate
caught it — the "proven safe" mechanism working on real inference.

## Honest caveats

1. **Cost is $0 here** — local Ollama models are free to run, so the headline
   *cost*-reduction % is not meaningful on this backend. The **−86.6% prompt-token**
   reduction is the real proxy; genuine dollar figures require the OpenAI-compatible
   backend (`GRAPHTHRIFT_BACKEND=openai`, real pricing).
2. **Absolute triple-F1 is low (~0.24)** because the raw `qwen2.5` model emits
   free-form predicates (`join_organization`, `start_project_leadership`) while the
   bundled gold graph uses a canonical vocabulary (`WORKS_AT`, `LEADS`). That's an
   artifact of the demo's hand-authored gold (written for the simulator's oracle),
   **not** a tool defect — in a real Graphiti deployment the gold is built from the
   same model, so predicates align. What matters here is the **relative** behavior:
   optimizations preserve quality; aggressive routing degrades it; the gate catches it.
3. **What is now proven on real inference:** real model calls fire; real token/latency
   metering; optimizers genuinely reduce calls (−45%) and tokens (−87%); the eval
   computes real F1; the gate correctly passes safe configs and fails unsafe ones.

## Real dollar cost (OpenAI)

Local models are free, so the Ollama run above shows token reduction, not dollars.
This run uses **real OpenAI models** to produce genuine cost figures — deliberately
frugal: `gpt-4o-mini` (extraction) + `gpt-4.1-nano` (dedup/summaries), 5 episodes,
baseline vs safe only. **Total actual spend: $0.0033.**

| Metric | Baseline | Optimized | Δ |
|---|---|---|---|
| LLM calls | 44 | 25 | **−43.2%** |
| Prompt tokens | 12,526 | 2,085 | **−83.4%** |
| Cost (gpt-4o-mini/nano) | $0.00245 | $0.00086 | **−64.9%** |
| Entity F1 | 0.88 | 0.88 | 0.000 (held) |
| Triple F1 | 0.296 | 0.296 | 0.000 (held) |
| — | eliminated: 19 | cache hits: 7 | **Gate: PASS ✅** |

**Real cost cut with identical extraction quality** — the gate passes.

### Projected to frontier pricing (from the *real measured* token counts)

These reprice the actual measured tokens at published frontier rates — honest
extrapolation, not additional spend:

| Model tier | Baseline | Optimized | Reduction | Monthly saving @ 1M episodes |
|---|---|---|---|---|
| gpt-4o + gpt-4o-mini | $0.0197 | $0.0104 | **−47.2%** | **~$1,861/mo** |
| gpt-5.5 + gpt-4.1-nano | $0.0338 | $0.0174 | **−48.6%** | **~$3,282/mo** |

(The gpt-4o-mini *actual* reduction of −64.9% is higher than the frontier projection
because on the cheap tier the small-model calls are proportionally cheaper and prompt
compression dominates. The frontier −47–49% is the conservative, defensible figure.)

## Real Graphiti + Neo4j integration (the `wrap()` drop-in)

The demo pipeline is a *reproduction* of Graphiti's call graph. This is the real
thing: `graphthrift.wrap()` around an actual `graphiti-core` `LLMClient`, driving a
real `Graphiti.add_episode()` against a real **Neo4j** database (LLM/embedder via
Ollama). See `examples/graphiti_quickstart.py`.

**Setup:** `graphiti-core` (pip), Neo4j 5.26 in Docker (via Colima) on
`bolt://localhost:7687`, LLM = `qwen2.5:3b`/`0.5b` + `nomic-embed-text` through
Ollama's OpenAI-compatible endpoint.

**Result — verified working:**

- `graphthrift.wrap(base_llm)` returns an object that **`isinstance` of Graphiti's `LLMClient`** ✓
- `build_indices_and_constraints()` + two `add_episode()` calls ran clean
- Graph **persisted in Neo4j**: 3 Entity nodes (Alice, Acme Corp, Atlas project — deduped from 2 episodes), 2 Episodic nodes, 1 `RELATES_TO` edge
- **The wrapper metered the real pipeline per stage:** 5 LLM calls, 6,977 prompt tokens, 244 completion tokens, 8.4 s — `{ExtractedEntities: 2, ExtractedEdges: 2, SummarizedEntities: 1}`

**Technical note:** Graphiti's base `generate_response` does not pass `prompt_name`
down to `_generate_response` (it uses it only for its own tracing spans), so the
wrapper labels stages by the `response_model` class name — which yields clean,
meaningful stage names (`ExtractedEntities`, `ExtractedEdges`, `SummarizedEntities`).
The override signature `(messages, response_model, max_tokens, model_size)` matched
graphiti-core exactly; no changes to `wrap()` were needed.

## Reproduce

```bash
# 1. local models
ollama serve &
ollama pull qwen2.5:3b && ollama pull qwen2.5:0.5b && ollama pull nomic-embed-text

# 2. the simulator demo
GRAPHTHRIFT_BACKEND=ollama graphthrift demo --scenario safe
GRAPHTHRIFT_BACKEND=ollama graphthrift demo --scenario aggressive

# 3. the real Graphiti + Neo4j integration
docker run -d -p 7687:7687 -e NEO4J_AUTH=neo4j/testpassword123 -e 'NEO4J_PLUGINS=["apoc"]' neo4j:5.26
pip install "graphthrift[graphiti]"
python examples/graphiti_quickstart.py
```
