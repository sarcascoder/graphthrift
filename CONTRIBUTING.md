# Contributing to GraphThrift

Thanks for your interest! GraphThrift is early and contributions are very welcome.

## Dev setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q          # backend tests
ruff check .       # lint

cd apps/web && npm install && npm run dev   # dashboard
```

## Ground rules

- **Every optimization must be gated.** If you add an optimizer that can change
  extraction output, it must be measured by `eval/metrics.py` and pass through
  `eval/gate.py`. "Cut cost, proven safe" is the whole point — no silent quality loss.
- **Account eliminated calls.** If an optimizer skips a call, record it via
  `InstrumentedLLM.record_eliminated` so savings are honest and visible.
- Keep the core **Graphiti-agnostic**; framework-specific code lives in `integrations/`.
- Add tests for new behavior. Keep `ruff` clean.

## Good first issues

- Add a real gold-annotated dataset (LongMemEval-derived) and wire it as a second eval target.
- Implement a semantic (embedding-based) response cache with a similarity threshold.
- Add an auto-tuner that searches optimizer configs to hit a cost target under a quality constraint.
- Add a LlamaIndex / LangChain KG integration mirroring `integrations/graphiti.py`.

## PRs

Open a PR against `main` with a clear description and before/after numbers
(`graphthrift demo` output) when relevant. CI must be green.
