# GraphThrift — What it is, how it was built, and the honest trade-offs

A plain-language, end-to-end explanation of the project: the problem, the design,
how each piece was built, what's proven vs. simulated, and where it helps or hurts.

---

## 1. The one-sentence version

**GraphThrift makes knowledge-graph ingestion (turning conversations/documents into
a graph of entities and relationships) cheaper and faster to run on LLMs — and
*proves* the cost cut didn't quietly wreck extraction quality.**

It targets [Graphiti](https://github.com/getzep/graphiti) (the open-source
agent-memory library by Zep, YC W24) first, but the core is framework-agnostic.

---

## 2. The problem it solves (and why it's real)

Agent-memory systems like Graphiti take each "episode" (a chat message, a document)
and fire a **cascade of LLM calls** to build a graph: extract entities → extract
relationships → deduplicate against the existing graph → summarize → assign
time-validity. For one episode that's typically **`3 + E + Eₙₑ𝓌 + ⌈N/30⌉` LLM calls**
(E = edges, N = nodes) — the cost is dominated by a **per-edge fan-out** where every
edge triggers its own resolve + timestamp call.

This isn't hypothetical. Zep's own engineering post-mortem
([*"How We Scaled Zep 30x"*](https://blog.getzep.com/scaling-agent-memory-zep-30x/))
says: **"LLM costs exploded to 3–5× our provisioned capacity."** And Graphiti
[issue #1193](https://github.com/getzep/graphiti/issues/1193) documents the same
per-episode call volume being *"prohibitively expensive."*

The **deeper** problem: you can't safely cut that cost. Swap to a cheaper model,
cache aggressively, or skip calls, and you might silently degrade extraction quality
— and nobody has an eval harness pointed at *their own* graph to prove they didn't.
Graphiti ships a *relative* pairwise LLM-judge but **no gold-graph precision/recall
metric anywhere** in the repo or its paper. That gap is GraphThrift's wedge.

---

## 3. What GraphThrift actually does

Four things, in a loop:

1. **Instrument** — meter every LLM/embedding call: tokens, cost, latency, per stage.
2. **Optimize** — a chain of techniques (below) that cut calls, tokens, and latency.
3. **Prove it's safe** — an evaluation harness measures entity- and triple-level
   **precision/recall/F1 against a gold graph**, and a **gate blocks any optimization
   that drops quality beyond a tolerance ε**.
4. **Show it** — a dashboard + CLI report before/after cost, latency, quality, and
   projected $ savings.

Adoption is **one line**: `graphthrift.wrap(your_graphiti_llm_client)`.

### The optimizers

| Optimizer | What it does | Why it's safe (or not) |
|---|---|---|
| **EdgeBatcher** | Collapses the per-edge resolve/timestamp fan-out (E calls → 1) | Same decisions, fewer calls — safe |
| **DedupPrefilter** | Drops restated/duplicate facts with classical NLP (exact + cosine) before the LLM sees them | Only removes true duplicates — safe |
| **ResponseCache / EmbeddingCache** | Reuses results for repeated extractions/embeddings | Deterministic — safe |
| **PromptCompressor** | Strips the prunable few-shot block from prompts | Instruction + input preserved — safe |
| **ModelRouter** | Honors the small/large tier; *optionally* downgrades stages to a cheaper model | Honor-only = safe; **downgrading extraction = risky → the gate catches it** |

The "aggressive" config deliberately downgrades extraction to a tiny model to show
the gate rejecting an unsafe cut. That contrast *is* the product thesis.

---

## 4. How it was built (chronological, honest)

### Phase A — Evidence, not assumptions
Before writing code, I did a **source-level teardown of Graphiti** to map the exact
LLM-call graph (`graphiti_core/edge_operations.py:623/813`, etc.), confirm the
per-edge fan-out is the dominant cost, and find the safe integration seam:
subclass `LLMClient` and override only `_generate_response`. This is captured in
`docs/PRD.md` §7. Every design choice traces to something in Graphiti's source or
Zep's own writing.

### Phase B — A backend-agnostic core
I built the core so the same engine runs three ways:
- **`fake`** — a deterministic *simulator* (no model) for offline, key-free demos
- **`ollama`** — real local models
- **`openai`** — any OpenAI-compatible endpoint (real cost numbers)

The simulator is the clever bit: it mimics an *imperfect* extractor driven by the
demo dataset's ground-truth annotations, and **degrades on the small-model tier** —
so routing to a cheap model carries a *real, measurable* quality cost and the gate
isn't a rubber stamp.

### Phase C — The pieces (Python)
- `instrument/` — the `InstrumentedLLM` engine (routing + caching + metering), a
  `RunTrace`/`CallRecord` model, and a token-pricing table.
- `optimize/` — the five optimizers + an `OptimizerConfig` (baseline / safe / aggressive).
- `eval/` — `metrics.py` (entity/triple P·R·F1 vs a gold graph, fuzzy matching,
  graph-diff) and `gate.py` (the ε safety gate).
- `demo/` — a **faithful offline reproduction** of Graphiti's `add_episode` call
  graph, plus an 8-episode agent-memory dataset with a hand-authored gold graph.
- `integrations/graphiti.py` — the real `wrap()` drop-in.
- `store/` (SQLAlchemy), `api/` (FastAPI, 9 routes), `runner.py`, `cli.py` (Typer).

### Phase D — The surfaces
- **FastAPI** service with OpenAPI docs, health/readiness, Prometheus metrics.
- **React + TypeScript + Vite + Tailwind** dashboard (dark mode): gate banner,
  metric cards, before/after charts, per-stage table, run history.
- **Docker + docker-compose** (`make up`), **GitHub Actions CI**, Apache-2.0.

### Phase E — Ship
- Renamed to a name free on PyPI/npm/GitHub, pushed to
  **github.com/sarcascoder/graphthrift**, deployed to **graphthrift.vercel.app**
  (React static + FastAPI as a Python serverless function).

### Phase F — Validation on real systems (the part that matters most)
- **Real local models (Ollama, `qwen2.5:3b`/`0.5b` + `nomic-embed`)** — safe config
  cut −44.6% calls / −86.6% prompt tokens with entity-F1 held (gate PASS); aggressive
  routing dropped F1 and the gate FAILED it.
- **Real `graphiti-core` + real Neo4j** — an actual `add_episode()` ran through
  `graphthrift.wrap()`, built and persisted a graph in Neo4j (3 entities, 2 episodics,
  1 edge), and the wrapper metered every call per stage. The override signature
  matched graphiti-core exactly; no changes to `wrap()` were needed.

See `docs/REAL_MODEL_RUN.md` for the full numbers and caveats.

---

## 5. What is proven vs. simulated (full honesty)

| Aspect | Status |
|---|---|
| Optimizer logic, eval math, gate | ✅ Real code, unit-tested (23 tests), run on real models |
| FastAPI / CLI / dashboard | ✅ Real, build-verified, live on Vercel |
| Reduces real calls & tokens on live inference | ✅ Proven (Ollama) |
| Gate catches real quality regressions | ✅ Proven (Ollama aggressive run) |
| `wrap()` works with real Graphiti + Neo4j | ✅ Proven (end-to-end run) |
| **Real dollar-cost figures** | ⬜ **Not yet** — needs the OpenAI backend + a key. Local models are free, so cost-% on Ollama is $0; token reduction is the proxy. |
| Absolute triple-F1 on the demo (~0.24 on Ollama) | ⚠️ Low because the demo's gold uses canonical predicates (`WORKS_AT`) while raw qwen emits free-form ones — an artifact of the hand-authored demo gold, not a tool defect. *Relative* behavior (safe holds, aggressive degrades) is what's validated. |

---

## 6. Advantages

- **Solves a documented, expensive, real problem** (Zep's own 3–5× cost blow-up).
- **Safety-first**: the eval gate is the differentiator — "cut cost, *proven* safe."
  Nobody else wires a gold-graph F1 gate into KG-ingestion cost optimization.
- **One-line adoption**: wraps Graphiti's existing `LLMClient` seam — no fork, no
  monkey-patching; verified against real graphiti-core.
- **Runs anywhere**: offline simulator (no keys) → local models → any OpenAI-compatible
  endpoint. Great for demos *and* production.
- **Fills a real gap**: adds the intrinsic extraction-quality metric Graphiti lacks.
- **Production-shaped**: tests, CI, Docker, OpenAPI, metrics, structured logging,
  a real dashboard — not a notebook.
- **Framework-agnostic core**: the optimizer + eval pattern generalizes to any LLM
  extraction pipeline (LlamaIndex KG, LangChain graph transformers, custom).

## 7. Disadvantages & limitations (stated plainly)

- **No real $ numbers yet** — validated on free local models and a real graph DB, but
  the headline dollar savings need an OpenAI (or paid-endpoint) run.
- **The demo's gold graph is hand-authored** for the simulator, so absolute F1 against
  a raw local model is low; it demonstrates *relative* behavior, not absolute accuracy.
- **Batched edge-resolution is an approximation** of Graphiti's per-edge logic. It
  mirrors the decisions in tests, but a production PR would need Graphiti's maintainers
  to validate parity on adversarial cases.
- **Serverless demo history is best-effort** — the live Vercel site stores runs in
  `/tmp` (stateless), so run history may not persist across cold starts. `make up`
  with Postgres gives durable history.
- **Not yet load-tested at scale** — correctness is shown on small corpora; behavior
  under high concurrency / large graphs / rate limits isn't benchmarked.
- **Gate quality depends on the gold set** — a weak or unrepresentative gold graph
  weakens the safety guarantee. Real value needs a real gold set per deployment.
- **Young project** — v0.1.0, single author, no external users yet.

## 8. When to use it / when not to

**Use it if** you run Graphiti (or a similar LLM extraction pipeline) at non-trivial
volume and want to cut ingestion cost without gambling on quality — especially if you
already have (or can build) a small gold graph to gate against.

**Don't reach for it if** your ingestion volume is tiny (the LLM bill isn't your
problem), or you need a turnkey guaranteed-accurate solution today — this is an
early, evidence-backed tool that still needs a real gold set and a production
validation pass to earn full trust.

---

## 9. Tech stack

**Backend:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, structlog, httpx, Typer.
**Frontend:** React + TypeScript, Vite, Tailwind, Recharts.
**Data:** SQLite (local) / PostgreSQL (prod).
**Infra:** Docker + docker-compose, GitHub Actions CI, Vercel (live demo).
**Models (validation):** Ollama (`qwen2.5`, `nomic-embed`); OpenAI-compatible supported.
**Integration:** graphiti-core + Neo4j (verified).

## 10. Links

- Repo: https://github.com/sarcascoder/graphthrift
- Live demo: https://graphthrift.vercel.app
- Design + Graphiti teardown: `docs/PRD.md`
- Architecture: `docs/ARCHITECTURE.md`
- Real-model + Neo4j validation: `docs/REAL_MODEL_RUN.md`
- Runnable integration: `examples/graphiti_quickstart.py`
