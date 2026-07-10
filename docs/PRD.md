# GraphThrift — Product Requirements Document

> **Working name:** GraphThrift (`graphthrift`) — *frugality/economy*. Renameable in Phase 6.
> **One line:** Profile, optimize, and *safely* shrink the LLM cost & latency of knowledge-graph ingestion pipelines — starting with [Graphiti](https://github.com/getzep/graphiti) (Zep, YC W24).
> **Status:** Phase 4 (this doc). Architecture "Pipeline call map" finalized by the Graphiti teardown in progress.
> **Author:** Anupam · **Date:** 2026-07-10

---

## 0. Why this exists (campaign context, kept honest)

This is a portfolio-grade OSS tool built to solve a *documented, unsolved* pain for a specific YC startup (Zep), so their founder thinks "I want this engineer." It must stand on its own as a genuinely useful tool — not a demo. Every design choice below is evidence-driven, citing Zep's own words.

**The evidence:**
- Zep's engineering post-mortem *["How We Scaled Zep 30x"](https://blog.getzep.com/scaling-agent-memory-zep-30x/)*: **"LLM costs exploded to 3–5× our provisioned capacity."**
- Graphiti [GitHub issue #1193](https://github.com/getzep/graphiti/issues/1193): ingestion fires **"multiple LLM calls and embedding calls… becomes prohibitively expensive."**
- Practitioner corroboration (Reddit r/LLMDevs, r/LocalLLaMA): eval/observability + grounding pain and inference-latency/serving pain are the two loudest clusters in the space.
- Graphiti is Python, ~28.6K★, pluggable LLM/embedder clients — the exact stack GraphThrift targets.

---

## 1. Problem

Knowledge-graph memory systems (Graphiti, and agent-memory layers generally) turn each conversational "episode" into graph structure by firing a **cascade of LLM calls**: extract entities → extract relationships/edges → resolve/dedupe nodes against existing graph → dedupe edges → summarize → temporally invalidate stale edges. For a single episode this can be **5–15+ LLM calls plus embedding calls**, scaling with the number of entities and edges.

Consequences, in the maintainers' own words: cost balloons 3–5×, p95 latency is multi-second, and teams throttle ingestion or drop context to cope. Worse: **there is no safe, principled way to cut that cost**, because any optimization (cheaper model, caching, skipping calls) risks silently degrading extraction quality — and nobody has an eval harness pointed at *their own* graph to prove it didn't.

**GraphThrift solves the whole loop:** measure the LLM-call cost/latency of ingestion → apply optimizations → **prove extraction quality is preserved** with an eval harness → show it in a dashboard → ship as a drop-in wrapper.

## 2. Current workflow (what a Graphiti user does today)

1. `pip install graphiti-core`, configure an LLM client (OpenAI/Anthropic/Gemini/Groq) + embedder + Neo4j/FalkorDB.
2. Call `graphiti.add_episode(...)` per message/document.
3. Under the hood, a fixed pipeline fires many LLM calls (see §7 Pipeline call map).
4. The user watches their OpenAI bill and p95 latency climb, with **no per-stage visibility** into which calls cost what.
5. To cut cost they either (a) guess (swap to a cheaper model globally and hope quality holds), (b) reduce `SEMAPHORE_LIMIT` concurrency (helps rate limits, not cost), or (c) give up and over-provision.

## 3. Pain points (ranked)

| # | Pain | Evidence |
|---|---|---|
| P1 | **Ingestion cost is 3–5× and opaque** — no per-stage cost attribution | Zep blog; issue #1193 |
| P2 | **No safe way to optimize** — cheaper model/caching risks silent quality loss, unmeasurable | inferred from lack of any eval-in-loop tooling |
| P3 | **Redundant/near-duplicate LLM calls** — dedup + extraction re-ask the model overlapping questions per episode | pipeline structure (§7) |
| P4 | **Latency is multi-second p95**, blocking real-time agent memory | Zep blog ("2s → 200ms" was *retrieval*; ingestion still heavy) |
| P5 | **One-size model** — trivial extractions use the same expensive model as hard ones | client abstraction has no routing |

## 4. Target users

- **Primary:** engineers running Graphiti / agent-memory ingestion at scale (Zep's own team; Zep customers; the 28.6K★ OSS community).
- **Secondary:** any team with an **LLM extraction pipeline** (entity/relationship extraction, structured output over documents, RAG indexing) — the optimizer + eval pattern generalizes. This keeps GraphThrift a real tool, not Zep fan-fiction.
- **Buyer/champion persona:** the founding/infra engineer who owns the LLM bill and gets paged on latency.

## 5. Competitors / prior art (and why GraphThrift is different)

| Tool | What it does | Gap GraphThrift fills |
|---|---|---|
| Helicone / Langfuse / Laminar | LLM observability (cost/latency tracing) | They *observe*; they don't *optimize* the pipeline or prove quality is preserved after optimization |
| DeepEval / Confident AI / Ragas | LLM/RAG eval | General eval; not wired into a KG-ingestion pipeline as a **safety gate for cost optimization** |
| GPTCache / semantic caches | Response caching | Generic; not aware of extraction-call semantics or graph dedup; no quality gate |
| LLMLingua (prompt compression) | Compress prompts | A single technique; GraphThrift orchestrates several + measures net quality impact |
| Graphiti's own `SEMAPHORE_LIMIT` | Concurrency control | Rate-limit control only — no cost attribution, routing, caching, or eval |

**GraphThrift's wedge = the combination:** per-stage profiler **+** a portfolio of optimizers **+** an extraction-quality eval harness that gates every optimization. "Cut cost, *proven* safe" is the thing nobody ships.

## 6. Architecture (overview)

```
┌────────────────────────────────────────────────────────────────┐
│  graphthrift (Python package)                                      │
│                                                                  │
│   InstrumentedLLMClient ──wraps──► any Graphiti LLMClient        │
│        │  (records tokens, cost, latency, prompt hash per call)  │
│        ▼                                                          │
│   Optimizer chain (priority order, from teardown):              │
│     1 EdgeBatcher   collapse per-edge resolve/timestamp fan-out  │
│     2 DedupPrefilter classical NLP (LSH/TF-IDF) drops calls @ 0  │
│                      quality cost — mirrors Zep's own 30x method │
│     3 CacheLayer    enable LLMCache + add embedding cache        │
│     4 ConcurrencyTuner  per-provider max_coroutines             │
│     5 ModelRouter   honor model_size (fixes Anthropic path)      │
│       (+ PromptCompressor: token compression before calls)      │
│        │                                                          │
│        ▼                                                          │
│   Trace store (SQLite/Postgres) ── run + per-call records        │
│        │                                                          │
│   Eval harness: replays a gold dataset through baseline vs       │
│   optimized, computes entity/edge F1 + graph-diff, GATES         │
│   optimizations that drop quality below threshold                │
└───────────────┬────────────────────────────────────────────────┘
                │ FastAPI (OpenAPI) — /runs, /traces, /evals, /compare
                ▼
        React + Vite dashboard (dark mode): cost/latency/quality
        before-after, per-stage flamebars, eval report, savings $
```

**Key principle — zero-fork integration (exact hook points, verified):**
- **LLM wrapper:** subclass `graphiti_core.llm_client.client.LLMClient` and override the single abstract method `_generate_response(self, messages, response_model, max_tokens, model_size)`. **Do NOT override public `generate_response`** — the base wraps retry/cache/tracing and passes `prompt_name` + `model_size` down to `_generate_response`, so the wrapper sees *exactly which prompt fired and which model tier was requested*. That is the hook for per-prompt routing, caching, and cost/latency metering.
- **Embedder wrapper:** subclass `graphiti_core.embedder.client.EmbedderClient`, implement `create` + `create_batch` (base raises `NotImplementedError`; node-dedup candidate search at `node_operations.py:428` uses `create_batch`).
- **Inject:** `Graphiti(llm_client=GraphThrift.wrap(OpenAIClient(...)), embedder=GraphThrift.wrap_embedder(...), max_coroutines=N)`. One-line change for the user. No fork, no monkey-patching.
- **Provider gotcha:** the OpenAI/Gemini clients honor `ModelSize.small` (small=`gpt-4.1-nano`/`gemini-2.5-flash-lite`, medium=`gpt-5.5`/`gemini-3-flash-preview`); **the Anthropic client accepts `ModelSize` but ignores it** — always uses one model. Model-routing on the Anthropic path is a GraphThrift-added win.
- **Existing knobs GraphThrift builds on:** `LLMCache` (SQLite, `llm_client/cache.py`) exists but is **off by default** and has **no embedding cache**; `SEMAPHORE_LIMIT`/`max_coroutines` default **20**.

## 7. Pipeline call map *(finalized from Graphiti source teardown — `main`, verified file:line)*

Driver: `Graphiti.add_episode` (`graphiti_core/graphiti.py:980`); core body lines 1122–1191. **Stages run sequentially; parallelism exists only *within* a stage via `semaphore_gather` (bounded `asyncio.gather`).** Notation: **N**=resolved nodes, **E**=extracted edges, **Enew**=new (non-dedup'd) edges, **Nc/Ec**=custom-typed nodes/edges with attribute schemas, **Ns**=nodes needing (re)summary.

| # | Function (file:line) | Prompt | Purpose | Calls | Batched? |
|---|---|---|---|---|---|
| 1 | `extract_nodes`→`_call_extraction_llm` (`node_operations.py:70,255`) | `extract_nodes.*` | Entity extraction + type classification | **1** | batched |
| — | `_semantic_candidate_search` (`node_operations.py:428`) | *(embed)* | Embed N node names for dedup candidates | **1 embed batch** | batched |
| 2 | `resolve_extracted_nodes`→`_resolve_with_llm` (`node_operations.py:467`) | `dedupe_nodes.nodes` | Node dedup vs graph. **Deterministic embedding-similarity pass first**; only leftovers hit LLM | **0 or 1** | batched |
| 3 | `extract_edges` (`edge_operations.py:117`) | `extract_edges.edge` | Relationship/fact extraction | **1** | batched |
| — | `create_entity_edge_embeddings` (`edge_operations.py:363`) | *(embed)* | Embed edge facts | **1 embed batch** | batched |
| **4** | **`resolve_extracted_edge` per edge** (`edge_operations.py:623`) | `dedupe_edges.resolve_edge` (small) | **Per-edge dedup + contradiction/invalidation folded in.** Verbatim-match shortcut (line 686) can skip | **E (concurrent)** | ⚠️ **per-item** |
| 4a | ↑ (`edge_operations.py:788`) | `extract_edges.extract_attributes` (small) | Structured attrs for custom edges | **Ec** | per-item |
| **4b** | ↑ (`edge_operations.py:813`) | `extract_edges.extract_timestamps` (small) | `valid_at`/`invalid_at` for new edges | **Enew** | ⚠️ **per-item** |
| 5 | `_extract_entity_attributes` (`node_operations.py:783`) | `extract_nodes.extract_attributes` (small) | Per-node attrs. **No call for plain `Entity` nodes** (line 790) | **Nc** | per-item |
| — | `create_entity_node_embeddings` (`node_operations.py:778`) | *(embed)* | Embed resolved node name/summary | **1 embed batch** | batched |
| 6 | `_extract_entity_summaries_batch` (`node_operations.py:913`) | `extract_nodes.extract_summaries_batch` (small) | Node summaries in flights of `MAX_NODES=30` | **⌈Ns/30⌉** | batched |
| 7 | `update_community` (`graphiti.py:1184`) — **OFF by default** | `summarize_nodes.*` | Community merge/rename | **~2·N** if enabled, else **0** | per-item |

**Per-episode LLM total (default, `update_communities=False`):**
`1 + [0..1] + 1 + E + Ec + Enew + Nc + ⌈Ns/30⌉`
→ plain episode, no custom types: **≈ 3 + E + Enew + ⌈N/30⌉ LLM calls** + ~4–5 embedding batch ops.
**Dominant cost term = the per-edge fan-out (stage 4/4b): E resolve + Enew timestamp calls, both per-item, small-model but chatty.** This is the primary optimization target.

Prompts live in `graphiti_core/prompts/` (`extract_nodes.py`, `dedupe_nodes.py`, `extract_edges.py`, `dedupe_edges.py`, `summarize_nodes.py`). No `invalidate_edges.py`/`temporal_operations.py` on `main` — invalidation folded into `dedupe_edges.resolve_edge`; dates via `extract_edges.extract_timestamps`.

## 8. Tech stack

- **Backend:** Python 3.11, **FastAPI**, Pydantic v2, `uvicorn`. Async throughout (mirrors Graphiti's async pipeline).
- **Optimizer core:** pure-Python, dependency-light; embeddings via the user's configured embedder (no new vendor lock-in). Optional local models via **Ollama/vLLM** for routing/compression (honors "prefer open models / local inference").
- **Frontend:** **React + TypeScript + Vite**, Tailwind + shadcn/ui, Recharts, **dark mode default**. Responsive.
- **Database:** **PostgreSQL** (prod) / SQLite (zero-config local) for trace + eval storage, via SQLAlchemy + Alembic migrations.
- **Auth:** API-key auth for the API; optional OAuth (GitHub) for the dashboard. JWT sessions. (Local dev: auth-off flag.)
- **Deployment:** **Docker + docker-compose** (api + web + postgres + optional ollama). One-command `make up`. Helm chart / K8s manifests as stretch (honors your K8s strength).
- **AI models:** provider-agnostic. Default demo uses OpenAI-compatible endpoints; local path uses `Qwen`/`Llama` via Ollama for the cheap-router and compressor so the demo runs with zero API keys.
- **Observability:** structured logging (structlog), OpenTelemetry hooks, `/metrics` Prometheus endpoint.

## 9. Evaluation (the differentiator — and a real gap GraphThrift fills)

**What Graphiti already ships** (`tests/evals/`): a *relative* regression harness — freeze a baseline graph, build a candidate, and use a **pairwise LLM-as-judge** (`prompts/eval.py::eval_add_episode_results` → `candidate_is_worse: bool`) scored as the fraction of episodes where the candidate is no-worse. **There is NO gold graph, no F1/precision/recall, no triple matching — anywhere in the repo or the [arXiv paper (2501.13956)](https://arxiv.org/abs/2501.13956), which measures only end-to-end QA accuracy.** That absence is GraphThrift's opening.

GraphThrift's eval stack, built in this order:
1. **Reuse Graphiti's pairwise judge as the CI gate first** (cheapest to wire, catches regressions immediately). Freeze a baseline on the *pre-optimization* pipeline; require candidate score ≥ threshold.
2. **Add intrinsic triple-level P/R/F1 vs a gold graph** — the credible metric the repo lacks. Gold = hand-annotated `(subject, relation, object)` triples + entity set for ~50–100 episodes. Compute **entity P/R/F1** and **triple P/R/F1** with **fuzzy matching** (embedding/LLM) on names + relation semantics.
3. **Temporal-validity accuracy** — Graphiti's differentiator: score `valid_at`/`invalid_at` + invalidation decisions vs time-stamped gold labels.
4. **Extrinsic backstop:** LongMemEval-style QA accuracy (retrieve→answer→judge-vs-gold) as the end-to-end safety net.

**Gate:** an optimization is "safe" only if triple-F1 and QA accuracy hold (≥ baseline − ε, default ε=2% F1) while cost/latency drop. Failing optimizations are flagged, not silently applied.

**Metric-drift caveat (baked into the harness):** paper LongMemEval = 71.2%, blog claims 80%+, product pages claim 90.2% — different dates/judges. GraphThrift always benchmarks against *its own frozen baseline*, never marketing numbers.

## 10. Metrics (what the dashboard reports)

- **$ / 1k episodes** (baseline vs optimized) and projected monthly savings at the user's volume.
- **p50/p95 ingestion latency** per stage (flamebar).
- **Cache hit-rate**, **cheap-model routing rate**, **calls eliminated**.
- **Quality delta:** entity F1, edge F1, graph-diff — with pass/fail gate.
- **Tokens in/out** per stage; redundant-call heatmap.

## 11. API design (FastAPI, OpenAPI-documented)

```
POST /v1/runs                 # start an instrumented ingestion run (baseline or optimized)
GET  /v1/runs/{id}            # run summary: cost, latency, quality, savings
GET  /v1/runs/{id}/traces     # per-call trace (stage, tokens, cost, latency, cache hit)
POST /v1/evals                # run eval: replay dataset baseline vs optimized
GET  /v1/evals/{id}           # eval report: F1s, graph-diff, gate pass/fail
GET  /v1/compare?a=&b=        # side-by-side two runs
GET  /v1/config               # active optimizer config
PUT  /v1/config               # toggle cache/router/compressor + thresholds
GET  /metrics                 # Prometheus
GET  /healthz  /readyz
```
All responses Pydantic-typed; interactive docs at `/docs` (Swagger) and `/redoc`.

## 12. Folder structure

```
graphthrift/
├── packages/
│   └── graphthrift/                 # the pip-installable library
│       ├── graphthrift/
│       │   ├── instrument/        # InstrumentedLLMClient, tracing
│       │   ├── optimize/          # cache, router, compressor, batcher
│       │   ├── eval/              # gold datasets, metrics, gate
│       │   ├── integrations/graphiti.py   # wrap() helpers, hook points
│       │   ├── store/             # SQLAlchemy models, migrations
│       │   └── api/               # FastAPI app, routers, schemas
│       ├── tests/
│       └── pyproject.toml
├── apps/
│   └── web/                        # React + Vite dashboard
├── examples/
│   ├── graphiti_quickstart.py      # runnable: baseline vs optimized on demo data
│   └── datasets/                   # demo episodes + gold graph
├── docker/  docker-compose.yml  Makefile
├── .github/workflows/ci.yml
└── docs/  README.md  PRD.md  ARCHITECTURE.md
```

## 13. Milestones (≤ 1 week build)

- **M0 (Day 1):** repo scaffold, CI, docker-compose, `InstrumentedLLMClient` wrapping Graphiti's client → per-call cost/latency traces on demo data. *Proof: "here's exactly what your ingestion costs, per stage."*
- **M1 (Day 2–3):** SemanticCache + ModelRouter (cheap + judge escalation); FastAPI + trace store; before/after cost numbers.
- **M2 (Day 3–4):** Eval harness (entity/edge F1 + graph-diff + gate) on a gold dataset — the safety proof.
- **M3 (Day 5):** React dark-mode dashboard: cost/latency/quality before-after, savings projection, per-stage flamebars.
- **M4 (Day 6):** PromptCompressor, batching tuner, local-model (Ollama) path so demo runs key-free; polish, tests, logging.
- **M5 (Day 7):** README, architecture diagram, screenshots, demo dataset, one-command startup, OSS polish; open a clean Graphiti PR/issue reference.

## 14. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Graphiti internals differ from assumptions | **Resolved** — teardown (§7) mapped exact calls + hook points from source (`file:line`); wrap at the stable `_generate_response`/`EmbedderClient` seam |
| Graphiti refactors the pipeline | Wrapper hooks the public client abstraction (stable public API), not internal call sites; call-map is versioned in §7 and re-verified per Graphiti release |
| Optimizations degrade quality | Eval gate is core, not optional; default-conservative ε |
| Demo needs API keys / graph DB | Local Ollama path + SQLite + tiny demo dataset → `make demo` runs offline |
| Looks like a wrapper, not real eng | Depth is in the eval harness + routing + graph-diff; measured, reproducible savings |
| Zep ships their own fix first | Positioned as general OSS tool for *any* extraction pipeline; still useful + still a conversation-starter |

## 15. Future roadmap

- Adapters beyond Graphiti (LlamaIndex KG, LangChain graph transformers, custom extraction pipelines).
- Auto-tuner: search optimizer configs to hit a cost target under a quality constraint.
- CI mode: fail a PR if graph-extraction quality regresses (eval-as-a-gate for LLM pipelines).
- Hosted mode + team dashboards; alerting on cost/latency drift.

---

*Next: your go/no-go on this PRD, then I build (Phase 5). Pipeline call map (§7) fills in from the teardown before any code is written.*
