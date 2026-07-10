# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [0.1.0] — 2026-07-10

### Added
- **Instrumentation engine** (`InstrumentedLLM`) — per-call cost/latency/token metering into a `RunTrace`.
- **Optimizer chain**: edge batcher (collapses the per-edge resolve/timestamp fan-out), classical-NLP dedup prefilter, response + embedding caches, model router (honors the small tier / optional downgrade), prompt compressor.
- **Evaluation harness** — entity- and triple-level precision/recall/F1 against a gold graph, plus graph diff. Fills the gap that Graphiti's repo lacks (it ships only a relative pairwise judge).
- **Quality gate** — blocks any optimization that drops F1 beyond ε.
- **Graphiti drop-in** (`graphthrift.wrap`) — one-line instrumentation of Graphiti's `LLMClient`.
- **Offline demo** — faithful reproduction of Graphiti's `add_episode` call graph with a deterministic simulation backend (no keys/GPU), plus Ollama and OpenAI-compatible backends.
- **FastAPI service** — runs, traces, config, dataset, health, Prometheus metrics; OpenAPI docs.
- **React + TypeScript dashboard** — dark mode, before/after cost/latency/quality, savings projection, per-stage breakdown, run history.
- **Ops** — Docker + docker-compose (API + dashboard + Postgres), Makefile one-command startup, GitHub Actions CI (lint, tests, frontend build, docker build), `.env` config.

[0.1.0]: https://github.com/anupam/graphthrift/releases/tag/v0.1.0
