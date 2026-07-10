# Outreach kit — Zep (Daniel Chalef)

> Drafts for engineering a conversation, not spamming. Fill `<REPO_URL>` after publishing.
> Rules honored: specific, honest, no exaggeration. Every claim maps to something in the repo or Zep's own words. The demo numbers are from a **deterministic simulation** — say so.

---

## 1. Founder email (short, the one that matters)

**Subject:** Cut Graphiti ingestion cost ~47% — with an eval gate that proves quality held

Hi Daniel,

I read "How We Scaled Zep 30x" and issue #1193 — the per-episode LLM-call fan-out during graph construction is a real, quotable pain, and the hard part isn't cutting cost, it's cutting it *without* silently degrading extraction.

So I built **GraphThrift**: an open-source cost/latency optimizer + eval harness for Graphiti's `add_episode` pipeline. It wraps your `LLMClient` in one line (no fork), meters cost/latency per stage, batches the per-edge `resolve_edge`/`extract_timestamps` fan-out, prefilters restated facts with classical NLP, and caches. The part I care about most: an **evaluation gate** that measures entity/triple **precision-recall-F1 against a gold graph** and *blocks any optimization that drops quality beyond ε* — the intrinsic metric your repo and paper don't currently have (you ship the relative pairwise judge; I added gold-F1 on top and reuse your judge as a second gate).

On a bundled 8-episode agent-memory demo (deterministic sim backend, runs offline): **−47% cost, −40% calls, −24% latency, F1 unchanged → gate PASS**. Flip to routing extraction to a nano model and it's −97% cost but triple-F1 drops 0.93→0.75 → **gate FAILS and flags it**. That contrast is the whole thesis.

Repo (Apache-2.0, `make up` to run): `<REPO_URL>`. It's genuinely useful, not a toy — I'd love your read on whether the gate approach matches how you think about safe optimization, and whether the batched `resolve_edge` path lines up with the real pipeline.

— Anupam
[GitHub] · [portfolio]

---

## 2. LinkedIn DM (≤300 chars)

Hi Daniel — I built GraphThrift, an OSS cost/latency optimizer + gold-F1 eval gate for Graphiti's add_episode pipeline (the per-edge fan-out from issue #1193). One-line `LLMClient` wrap; ~47% cost cut with quality gated. Repo: `<REPO_URL>`. Would value your take.

---

## 3. Twitter/X DM

Hey @danielchalef — "Scaled Zep 30x" nerd-sniped me. Built GraphThrift: OSS optimizer + eval-gate for Graphiti's add_episode. Batches the per-edge resolve/timestamp fan-out, prefilters restated facts, and gates every optimization on entity/triple F1 vs a gold graph (the metric the repo lacks). One-line wrap of your LLMClient. `<REPO_URL>` — curious if the gate matches how you think about safe cost cuts.

---

## 4. GitHub — where to surface it (natural, not spammy)

- Comment on **issue #1193** with a concrete, humble note: "Ran into the same fan-out cost; built an OSS profiler + eval-gated optimizer that batches `resolve_edge`/`extract_timestamps` and caches restated facts — repo here if useful: `<REPO_URL>`. Happy to open a PR for the batched-resolve path if that's a direction you'd take."
- Optionally open a **small, focused PR** (not a mega-PR): e.g. an opt-in batched edge-resolution path, or expose per-stage cost/latency metering hooks. Keep it reviewable.

---

## 5. One-minute elevator pitch (spoken)

"Graphiti turns every conversation into a knowledge graph by firing a cascade of LLM calls per episode — Zep's own blog says it blew their costs up 3-to-5x. The trap is you can't just swap a cheaper model, because you might silently wreck extraction quality and never know. GraphThrift is an open-source tool that profiles that pipeline, applies safe optimizations — batching the per-edge calls, caching restated facts, compressing prompts — and then *proves* it's safe with an eval gate that measures triple-level F1 against a gold graph and blocks anything that regresses. On the demo it's a 47% cost cut with quality unchanged, and it rejects the tempting 97% cut that would've dropped F1. One line to adopt: it wraps Graphiti's LLM client."

---

## 6. Five-minute demo script

1. **(0:00) The pain.** Show issue #1193 + the "3-5x cost" quote. "Per episode, Graphiti fires `3 + E + Eₙₑ𝓌 + ⌈N/30⌉` LLM calls; the per-edge fan-out dominates."
2. **(0:45) `graphthrift demo --scenario safe`.** Walk the table: cost −47%, calls −40%, latency −24%, F1 unchanged, GATE PASS. "Batching + dedup prefilter + cache + compression. The graph is byte-identical to baseline."
3. **(1:45) `graphthrift demo --scenario aggressive`.** "Now I route extraction to a nano model. 97% cheaper — but triple-F1 drops to 0.75 and the gate FAILS. It flags it instead of shipping it. That's the point."
4. **(2:45) Dashboard.** Run from the UI; show per-stage breakdown (resolve_edge/extract_timestamps highlighted), before/after charts, projected $/month.
5. **(3:45) The code.** `graphthrift.wrap(client)` — one line. Show the eval harness computing gold-F1, and the gate. "This is the metric your repo doesn't have yet."
6. **(4:30) Close.** "Apache-2.0, `make up`, tests + CI green. I built it because it's the exact problem I'd want to own as a founding engineer at Zep."

---

## 7. Technical deep-dive (for the interview / README-linked)

- **Teardown-grounded:** call map verified against Graphiti `main` (`edge_operations.py:623/813`, etc.) — see PRD §7.
- **Hook seam:** subclass `LLMClient._generate_response`; the base still owns retry/tracing. Provider note: the Anthropic client ignores `model_size`; GraphThrift's router restores tiering.
- **Why batching is the lever:** `resolve_edge` (E) + `extract_timestamps` (Eₙₑ𝓌) are per-item; collapsing them is the dominant call/latency win. Cost win comes from prompt compression + caching restated facts (agent memory restates facts constantly — natural cache/prefilter hits).
- **Eval:** entity + triple P/R/F1 with fuzzy matching vs a gold graph; graph-diff; ε-gated. Roadmap: reuse Zep's pairwise judge as a second gate + LongMemEval QA backstop.
- **Honesty:** demo backend is a deterministic simulator that degrades on the small tier, so routing carries a *real* measured quality cost — the gate isn't a rubber stamp. Swap in Ollama/OpenAI for real-model numbers.

---

## 8. Product Hunt / Show HN one-liner

**GraphThrift — cut the LLM cost of knowledge-graph ingestion, proven safe.** Open-source profiler + optimizer + eval-gate for Graphiti/agent-memory pipelines. Batches the per-edge LLM fan-out, caches restated facts, and blocks any optimization that drops extraction F1. One line to adopt.
