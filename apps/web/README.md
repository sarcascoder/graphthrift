# 🪶 GraphThrift — Web Dashboard

A production-quality React + TypeScript + Vite dashboard for **GraphThrift**, an
LLM cost/latency optimizer for knowledge-graph ingestion. It profiles a baseline
ingestion pipeline against an optimized candidate, then **proves the
optimization is safe** (graph quality stays within an ε tolerance) before
recommending it.

Dark mode by default, with a light toggle. Fully responsive.

## Stack

- Vite + React 18 + TypeScript
- Tailwind CSS v3 (class-based dark mode)
- Recharts (bar charts)
- lucide-react (icons)
- Plain `fetch` — no axios, no component library

## Quick start

```bash
npm install
cp .env.example .env      # optional — defaults to http://localhost:8000
npm run dev               # http://localhost:5173
```

The dev server proxies `/v1`, `/healthz`, `/readyz` and `/metrics` to
`VITE_API_BASE` (default `http://localhost:8000`), so the GraphThrift API can run
without CORS friction.

## Scripts

| Script            | Description                              |
| ----------------- | ---------------------------------------- |
| `npm run dev`     | Start the Vite dev server on `:5173`     |
| `npm run build`   | Type-check (`tsc -b`) and build to `dist/` |
| `npm run preview` | Preview the production build on `:5173`  |
| `npm run lint`    | Type-check only                          |

## Configuration

`VITE_API_BASE` — base URL of the GraphThrift API. Baked in at build time.
Leave empty when serving behind the bundled nginx proxy (relative requests).

## Docker

```bash
# Build (optionally bake an absolute API base):
docker build -t graphthrift-web .

# Run — nginx serves the static site and proxies /v1 to the backend:
docker run -p 8080:80 -e BACKEND_URL=http://host.docker.internal:8000 graphthrift-web
```

The image is a two-stage build: `node:20-alpine` compiles the site, then
`nginx:1.27-alpine` serves it. `BACKEND_URL` is substituted into the nginx
config at container start.

## What it shows

- **Control panel** — Safe / Aggressive / Custom scenarios, per-optimizer
  toggles, monthly volume, and quality tolerance ε.
- **Gate banner** — SAFE (apply) or UNSAFE (blocked), with the gate's reasons.
- **Metric cards** — cost, LLM-call, and latency reductions plus projected
  monthly savings.
- **Charts** — baseline vs optimized (normalized) and graph-quality F1 with the
  ε tolerance band drawn in.
- **Per-stage table** — where the calls and cost go, highlighting the per-edge
  fan-out (`resolve_edge`, `extract_timestamps`) money stages.
- **Run history** — every past comparison, clickable to reload.
