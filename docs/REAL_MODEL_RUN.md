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

## Reproduce

```bash
ollama serve &
ollama pull qwen2.5:3b && ollama pull qwen2.5:0.5b && ollama pull nomic-embed-text
GRAPHTHRIFT_BACKEND=ollama graphthrift demo --scenario safe
GRAPHTHRIFT_BACKEND=ollama graphthrift demo --scenario aggressive
```
