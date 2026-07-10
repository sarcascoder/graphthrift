<div align="center">

# 🪶 GraphThrift

**Profile, optimize, and _safely_ shrink the LLM cost & latency of knowledge-graph ingestion pipelines.**

*Cut cost — proven safe. Built Graphiti-first.*

[![CI](https://github.com/sarcascoder/graphthrift/actions/workflows/ci.yml/badge.svg)](https://github.com/sarcascoder/graphthrift/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Tests](https://img.shields.io/badge/tests-23%20passing-brightgreen)

### ▶︎ [**Try the live demo →  graphthrift.vercel.app**](https://graphthrift.vercel.app)

*Run a real baseline-vs-optimized comparison in your browser — no signup, no keys.*

</div>

---

## The problem

Knowledge-graph memory systems like [Graphiti](https://github.com/getzep/graphiti) (Zep) turn every conversational episode into graph structure by firing a **cascade of LLM calls** — extract entities → extract edges → resolve/dedupe → summarize → timestamp. Per episode that's **`3 + E + Eₙₑ𝓌 + ⌈N/30⌉` LLM calls**, dominated by a **per-edge fan-out** that is chatty and slow.

Zep's own engineering post-mortem put it bluntly:

> *"LLM costs exploded to 3–5× our provisioned capacity."* — [How We Scaled Zep 30x](https://blog.getzep.com/scaling-agent-memory-zep-30x/)

And there's a deeper problem: **there's no safe way to cut that cost.** Swap in a cheaper model, cache aggressively, or skip calls, and you might silently degrade extraction quality — with no way to prove you didn't. Graphiti ships a *relative* pairwise judge but **no gold-graph precision/recall anywhere in the repo or paper.**

## What GraphThrift does

GraphThrift closes the whole loop:

1. **Instrument** — meter every LLM/embedding call: tokens, cost, latency, per stage.
2. **Optimize** — a chain of cost/latency optimizations (edge-batching, classical-NLP dedup prefilter, response + embedding caching, model routing, prompt compression).
3. **Prove it's safe** — an **evaluation gate** measures entity- and triple-level **precision/recall/F1 against a gold graph** and *blocks any optimization that drops quality beyond ε*.
4. **See it** — a React dashboard shows before/after cost, latency, quality, and projected $ savings.
5. **Ship it** — a **one-line drop-in wrapper** for Graphiti's `LLMClient`. No fork, no monkey-patching.

> The differentiator isn't the optimizer — anyone can swap a cheaper model. It's the **gate that proves quality survived.** That's what turns *"we cut cost"* into *"we cut cost, proven safe."*

## Results on the bundled demo (offline, deterministic)

Two configs against a baseline, on an 8-episode agent-memory corpus:

| Config | Cost | LLM calls | Latency | Triple F1 | **Gate** |
|---|---|---|---|---|---|
| **Safe** (batch + dedup + cache + compress) | **−47%** | **−40%** | **−24%** | unchanged | ✅ **PASS → apply** |
| **Aggressive** (also routes extraction → small model) | −97% | −45% | −64% | **0.93 → 0.75** | ❌ **FAIL → flagged, not applied** |

The tempting 97% cut fails the gate. The safe 47% cut ships. *That's the point.*

| Safe config → gate **passes** | Aggressive config → gate **fails** |
|---|---|
| ![Safe: −47% cost, F1 held, gate pass](docs/screenshots/safe_gate_pass.png) | ![Aggressive: −97% cost but F1 drops, gate fail](docs/screenshots/aggressive_gate_fail.png) |
| −47% cost, quality unchanged | −97% cost, but F1 bars drop below the ε band → refused |

```bash
graphthrift demo --scenario safe        # ✅ gate pass
graphthrift demo --scenario aggressive  # ❌ gate fail — flagged unsafe
```

> These numbers are from the **deterministic simulator** (so the demo runs offline, key-free). The mechanism was also **validated on real local models** (`qwen2.5:3b`/`0.5b` + `nomic-embed` via Ollama): safe config cut **−44.6% calls / −86.6% prompt tokens** with entity-F1 held (0.81→0.89, gate PASS); aggressive routing dropped F1 (entity −0.12, triple −0.17) and the gate **failed it**.
>
> And on **real OpenAI models** (`gpt-4o-mini` + `gpt-4.1-nano`, total spend $0.0033): safe config cut **−64.9% cost / −83.4% prompt tokens** with F1 unchanged (gate PASS) — projecting to **~47–49% ($1.9k–3.3k/mo at 1M episodes)** at frontier `gpt-4o`/`gpt-5.5` pricing.
>
> And the **`wrap()` drop-in was verified against real `graphiti-core` + Neo4j** — an actual `add_episode()` built and persisted a graph in Neo4j while GraphThrift metered every LLM call per stage (`ExtractedEntities`/`ExtractedEdges`/`SummarizedEntities`). Full runs + honest caveats: [`docs/REAL_MODEL_RUN.md`](docs/REAL_MODEL_RUN.md).

## Quickstart

### One command (Docker)

```bash
make up          # API :8000 + dashboard :5173 + Postgres, all wired
open http://localhost:5173
```

### Local (no keys, no GPU, offline)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
graphthrift demo                 # runs the offline simulation backend
graphthrift serve                # API at http://localhost:8000/docs
```

The default backend is a **deterministic simulator** — the demo runs with zero API keys. Point it at a real model any time:

```bash
export GRAPHTHRIFT_BACKEND=ollama     # local, key-free   (qwen2.5 + nomic-embed)
export GRAPHTHRIFT_BACKEND=openai     # real cost numbers (set GRAPHTHRIFT_OPENAI_API_KEY)
```

## Dashboard

**Live:** [graphthrift.vercel.app](https://graphthrift.vercel.app) — or `make up` (or `cd apps/web && npm run dev`) to serve the React + TypeScript dashboard (dark mode by default) at `http://localhost:5173`:

- **Gate banner** — big green *SAFE — apply* or red *UNSAFE — flagged*, with the reasons and F1 deltas.
- **Metric cards** — cost −%, calls −%, latency −%, and projected **$/month saved** at your volume.
- **Before/after charts** — baseline vs optimized for cost/calls/latency, and an entity/triple-F1 chart with the ε tolerance band drawn in.
- **Per-stage table** — cost/calls per pipeline stage, with the `resolve_edge` / `extract_timestamps` fan-out (the money stages) highlighted.
- **Run history** — every comparison persisted and reloadable.
- **Control panel** — pick Safe / Aggressive / Custom (toggle each optimizer), set monthly volume and ε, hit *Run comparison*.

## Drop-in for Graphiti (production)

```python
from graphiti_core import Graphiti
from graphiti_core.llm_client.openai_client import OpenAIClient
import graphthrift

base = OpenAIClient(config=...)
trace = graphthrift.RunTrace(label="prod")

graphiti = Graphiti(llm_client=graphthrift.wrap(base, trace=trace))
# ...ingest as usual...
print(trace.summary())   # cost/latency/calls, per stage
```

`graphthrift.wrap` subclasses Graphiti's `LLMClient` and overrides only `_generate_response` (the stable seam) to add routing, caching, and metering around your real client — **one line changed.**

## How it works

```
InstrumentedLLM  ──► routing · cache · compression · metering ──► backend (fake│ollama│openai)
      │                                                                 │
      └── RunTrace (per-call cost/latency/tokens) ◄─────────────────────┘
                          │
   DedupPrefilter ──┐     ▼
   EdgeBatcher ─────┼──► pipeline (faithful Graphiti add_episode call graph)
   ModelRouter ─────┘     │
                          ▼
        Eval harness: entity/triple P·R·F1 vs gold graph ──► Quality Gate ──► PASS │ FAIL
```

See [`docs/PRD.md`](docs/PRD.md) for the full design and the verified Graphiti call-map teardown, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for module layout.

## API

Interactive docs at `/docs` (Swagger) and `/redoc`.

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/v1/runs` | Run a baseline-vs-optimized comparison, persist it |
| `GET`  | `/v1/runs` | List recent runs |
| `GET`  | `/v1/runs/{id}` | Full report for a run |
| `GET`  | `/v1/runs/{id}/traces` | Per-stage trace breakdown |
| `GET`  | `/v1/config` · `/v1/dataset` | Active config / demo dataset stats |
| `GET`  | `/healthz` · `/readyz` · `/metrics` | Ops |

## Configuration

All via `GRAPHTHRIFT_*` env vars (see [`.env.example`](.env.example)) — backend, models, `DATABASE_URL`, API key auth, optimizer toggles, and the quality `EPSILON`.

## Development

```bash
pip install -e ".[dev]"
pytest            # 23 tests
ruff check .
```

## License

Apache-2.0. See [`LICENSE`](LICENSE).

*GraphThrift is an independent open-source tool and is not affiliated with Zep. Graphiti is a trademark of its respective owner.*
