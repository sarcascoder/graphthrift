# Architecture

GraphThrift is a Python package (`graphthrift/`) plus a React dashboard (`apps/web/`).
The core is **Graphiti-agnostic**: the same engine powers the offline demo and the
real Graphiti drop-in wrapper.

## Data flow

```
                        ┌──────────────────────── graphthrift (Python) ─────────────────────────┐
 episode ──► pipeline ──►  InstrumentedLLM.call()                                              │
 (demo)      (demo/       ├─ ModelRouter        (honor small tier / optional downgrade)        │
              pipeline)   ├─ ResponseCache       (skip repeat extraction calls)                │
                          ├─ PromptCompressor    (prune few-shot block, cut input tokens)      │
                          ├─ backend.generate()  (fake │ ollama │ openai)                       │
                          └─ RunTrace.add(CallRecord: tokens, cost, latency, stage)             │
                                                                                                │
 DedupPrefilter / EdgeBatcher run inside the pipeline to eliminate the per-edge fan-out         │
                          │                                                                     │
                          ▼                                                                     │
              GraphState (built graph) ──► eval.metrics (entity/triple P·R·F1 vs gold)          │
                          │                                │                                    │
                          ▼                                ▼                                    │
                     graph_diff                     eval.gate (PASS / FAIL within ε)            │
                          └──────────────► runner.run_comparison ──► report dict ──────────────┘
                                                                          │
                          store (SQLAlchemy)  ◄───────────  api.service   │  cli
                                                                          ▼
                                                             FastAPI  ──►  React dashboard
```

## Modules

| Package | Responsibility |
|---|---|
| `graphthrift/backends` | LLM transport: `fake` (deterministic sim), `ollama` (local), `openai_compat`. Uniform `LLMBackend` protocol. |
| `graphthrift/instrument` | `InstrumentedLLM` engine + `RunTrace`/`CallRecord` + pricing. Every call is routed, cached, metered here. |
| `graphthrift/optimize` | The optimizer chain: `router`, `cache` (response+embedding), `dedup_prefilter`, `edge_batcher`, `compressor`, and `OptimizerConfig`. |
| `graphthrift/eval` | `metrics` (entity/triple P·R·F1 vs gold, graph diff) + `gate` (safety threshold). |
| `graphthrift/demo` | Faithful Graphiti `add_episode` call-graph reproduction, the demo corpus + gold graph, and the large system prompts. |
| `graphthrift/integrations` | `graphiti.wrap()` — the one-line production drop-in. |
| `graphthrift/store` | SQLAlchemy models + repo for persisting runs. |
| `graphthrift/api` | FastAPI app, routers, schemas, auth, metrics. |
| `graphthrift/runner.py` | Orchestrates baseline vs candidate → eval → gate → savings → report. |
| `graphthrift/cli.py` | Typer CLI (`demo`, `serve`, `version`). |

## Why the demo is faithful, not fake

The demo pipeline fires the exact stages and call-count formula the Graphiti source
teardown found (`3 + E + Eₙₑ𝓌 + ⌈N/30⌉` per episode; see `docs/PRD.md` §7). The
`fake` backend simulates an imperfect extractor that *degrades on the small model
tier*, so routing carries a real quality cost and the gate is meaningful. Swap in
the `ollama` or `openai` backend and the same pipeline runs against real models.

## Extension points

- **New backend**: implement `LLMBackend` (`generate` + `embed` + `model_for`).
- **New optimizer**: add to `graphthrift/optimize`, wire a toggle in `OptimizerConfig`,
  and invoke it from `InstrumentedLLM` or the pipeline; account eliminated calls via
  `record_eliminated` so the dashboard reflects savings.
- **New integration** (LlamaIndex KG, LangChain graph transformers): mirror
  `integrations/graphiti.py` — wrap the framework's LLM seam.
