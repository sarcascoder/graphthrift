# 60-second demo recording script

Goal: a tight, silent-or-narrated screen capture that shows the *whole thesis* —
optimize, then the gate **passing** on a safe cut and **failing** on an unsafe one.
Post it in the GitHub comment / X post. A moving demo beats a link every time.

**Record at:** https://graphthrift.vercel.app (or `make up` locally for snappier response).
**Tool:** macOS `Cmd+Shift+5` (screen record) or QuickTime. Capture the browser window
only, ~1280×800. Keep it **under 70 seconds**. Export as `.mp4` (X) or `.gif` (GitHub).

> Tip: do a dry run first so the backend is warm (first serverless call is slow).

---

## Shot list

| Time | On screen | Action / narration (optional captions) |
|---|---|---|
| **0:00–0:05** | Landing page, dark mode | Land on the site. Caption: **"GraphThrift — cut LLM cost of knowledge-graph ingestion, proven safe."** Let the empty state + "8 episodes · 12 gold entities · 15 gold triples" show. |
| **0:05–0:10** | Control panel | Cursor to the **Safe** scenario card (already selected). Caption: **"Safe optimizers: batch the per-edge fan-out, dedup restated facts, cache, compress."** |
| **0:10–0:14** | Click **Run comparison** | Click. Show the button's loading state. |
| **0:14–0:26** | Results render | **Pause here 3–4s.** Green gate banner **"SAFE — apply"**. Then the metric cards: **Cost −47%, Calls −40%, Latency −24%, ~$3.4k/mo saved**. Caption: **"−47% cost. Entity/Triple F1 unchanged. Gate PASS."** |
| **0:26–0:34** | Scroll to charts | Slow scroll. Show **Baseline vs optimized** bars (53% / 60% / 76%) and **Graph quality (F1)** with the two F1 bars nearly identical inside the ε band. Caption: **"Quality preserved — that's why it's safe to ship."** |
| **0:34–0:40** | Scroll to per-stage table | Show `resolve_edge` / `extract_timestamps` rows highlighted. Caption: **"The per-edge fan-out — the money stage — collapsed."** |
| **0:40–0:44** | Back to top, click **Aggressive** | Switch scenario to **Aggressive**. Caption: **"Now push it: route extraction to a tiny model."** |
| **0:44–0:48** | Click **Run comparison** | Click. Loading. |
| **0:48–0:58** | Results render | **Pause 3–4s.** Red banner **"UNSAFE — flagged, not applied"**. Cost shows −97% but Triple F1 visibly drops. Caption: **"−97% cost… but F1 dropped. Gate FAILS. It refuses to ship the cheap-but-broken cut."** |
| **0:58–1:05** | Run history sidebar | Show both runs stacked: green **Safe / gate pass**, red **Aggressive / gate fail**. Caption: **"Cut cost — proven safe. github.com/sarcascoder/graphthrift"** |

---

## Captions block (copy-paste, if adding text overlays)

1. GraphThrift — cut the LLM cost of knowledge-graph ingestion, proven safe
2. Safe optimizers: batch per-edge fan-out · dedup · cache · compress
3. −47% cost, F1 unchanged → GATE PASS
4. Quality preserved inside the ε tolerance band
5. The per-edge fan-out — collapsed
6. Push it: route extraction to a tiny model
7. −97% cost… but F1 dropped → GATE FAILS, flagged not applied
8. Cut cost, proven safe · github.com/sarcascoder/graphthrift

## One-line post caption (for X / GitHub)

> Built GraphThrift: it cuts Graphiti ingestion cost but **blocks** any optimization
> that drops extraction F1. Watch the safe cut ship (green) and the greedy cut get
> refused (red). ~65% cost cut with quality held on a real run. Repo in reply. 🪶

## If you'd rather not narrate

Silent is fine — the captions carry it. Keep cursor movements deliberate and pause
on each result screen for 3–4 seconds so viewers can read the numbers.
