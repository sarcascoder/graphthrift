import { useState } from 'react'
import { Play, Loader2, Sliders, ShieldCheck, Zap, Wrench } from 'lucide-react'
import type { OptimizerOverrides, RunRequest, Scenario } from '../lib/api'
import { Card, SectionTitle } from './ui'
import { cx } from '../lib/format'

interface ToggleDef {
  key: keyof OptimizerOverrides
  label: string
  hint: string
}

const TOGGLES: ToggleDef[] = [
  { key: 'cache_enabled', label: 'Response cache', hint: 'Memoize identical LLM calls' },
  { key: 'embedding_cache_enabled', label: 'Embedding cache', hint: 'Reuse embeddings across episodes' },
  { key: 'router_enabled', label: 'Model router', hint: 'Downgrade cheap-enough stages' },
  { key: 'dedup_prefilter_enabled', label: 'Dedup prefilter', hint: 'Skip near-duplicate extractions' },
  { key: 'edge_batcher_enabled', label: 'Edge batcher', hint: 'Batch per-edge fan-out calls' },
  { key: 'compressor_enabled', label: 'Prompt compressor', hint: 'Trim redundant prompt tokens' },
]

const SCENARIOS: { id: Scenario; label: string; icon: typeof ShieldCheck; blurb: string }[] = [
  { id: 'safe', label: 'Safe', icon: ShieldCheck, blurb: 'Conservative, quality-preserving optimizers' },
  { id: 'aggressive', label: 'Aggressive', icon: Zap, blurb: 'Every optimizer on — maximum savings' },
  { id: 'custom', label: 'Custom', icon: Wrench, blurb: 'Hand-pick the optimizer stack' },
]

const DEFAULT_CUSTOM: Required<OptimizerOverrides> = {
  cache_enabled: true,
  embedding_cache_enabled: true,
  router_enabled: false,
  dedup_prefilter_enabled: true,
  edge_batcher_enabled: true,
  compressor_enabled: false,
  router_downgrade_stages: [],
}

export function ControlPanel({
  onRun,
  running,
  defaultEpsilon,
}: {
  onRun: (req: RunRequest) => void
  running: boolean
  defaultEpsilon: number
}) {
  const [scenario, setScenario] = useState<Scenario>('safe')
  const [monthlyVolume, setMonthlyVolume] = useState<number>(1_000_000)
  const [epsilon, setEpsilon] = useState<number>(defaultEpsilon)
  const [epsilonTouched, setEpsilonTouched] = useState(false)
  const [overrides, setOverrides] = useState<Required<OptimizerOverrides>>(DEFAULT_CUSTOM)

  // Keep epsilon in sync with server default until the user edits it.
  const effectiveEpsilon = epsilonTouched ? epsilon : defaultEpsilon

  const toggle = (key: keyof OptimizerOverrides) =>
    setOverrides((o) => ({ ...o, [key]: !o[key as keyof typeof o] }))

  const submit = () => {
    const req: RunRequest = {
      scenario,
      monthly_volume: monthlyVolume || 0,
      epsilon: effectiveEpsilon,
    }
    if (scenario === 'custom') {
      req.overrides = { ...overrides }
    }
    onRun(req)
  }

  return (
    <Card>
      <SectionTitle
        icon={<Sliders className="h-4 w-4" />}
        title="Run a comparison"
        subtitle="Profile the baseline pipeline against an optimized candidate"
      />

      {/* Scenario segmented control */}
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        {SCENARIOS.map((s) => {
          const Icon = s.icon
          const active = scenario === s.id
          return (
            <button
              key={s.id}
              onClick={() => setScenario(s.id)}
              className={cx(
                'group flex flex-col items-start gap-1 rounded-xl border p-3 text-left transition',
                active
                  ? 'border-brand-500/60 bg-brand-500/10 ring-1 ring-brand-500/30'
                  : 'border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800/40 dark:hover:border-zinc-600 dark:hover:bg-zinc-800/70',
              )}
            >
              <span
                className={cx(
                  'flex items-center gap-2 text-sm font-medium',
                  active ? 'text-brand-700 dark:text-brand-300' : 'text-zinc-800 dark:text-zinc-200',
                )}
              >
                <Icon className="h-4 w-4" />
                {s.label}
              </span>
              <span className="text-xs leading-snug text-zinc-500 dark:text-zinc-400">
                {s.blurb}
              </span>
            </button>
          )
        })}
      </div>

      {/* Custom toggles */}
      {scenario === 'custom' && (
        <div className="mt-4 grid grid-cols-1 gap-2 rounded-xl border border-zinc-200 bg-zinc-50/60 p-3 sm:grid-cols-2 dark:border-zinc-800 dark:bg-zinc-950/40">
          {TOGGLES.map((t) => {
            const on = Boolean(overrides[t.key])
            return (
              <button
                key={t.key}
                onClick={() => toggle(t.key)}
                className="flex items-center justify-between gap-3 rounded-lg px-3 py-2 text-left transition hover:bg-white dark:hover:bg-zinc-800/60"
                role="switch"
                aria-checked={on}
              >
                <span className="min-w-0">
                  <span className="block text-sm font-medium text-zinc-800 dark:text-zinc-100">
                    {t.label}
                  </span>
                  <span className="block truncate text-xs text-zinc-500 dark:text-zinc-400">
                    {t.hint}
                  </span>
                </span>
                <span
                  className={cx(
                    'relative h-5 w-9 flex-none rounded-full transition-colors',
                    on ? 'bg-brand-500' : 'bg-zinc-300 dark:bg-zinc-700',
                  )}
                >
                  <span
                    className={cx(
                      'absolute top-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform',
                      on ? 'translate-x-4' : 'translate-x-0.5',
                    )}
                  />
                </span>
              </button>
            )
          })}
        </div>
      )}

      {/* Numeric inputs + run */}
      <div className="mt-4 grid grid-cols-1 items-end gap-4 sm:grid-cols-[1fr_1fr_auto]">
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Monthly volume (episodes)
          </span>
          <input
            type="number"
            min={0}
            step={1000}
            value={monthlyVolume}
            onChange={(e) => setMonthlyVolume(Number(e.target.value))}
            className="input font-mono"
          />
        </label>

        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-zinc-600 dark:text-zinc-400">
            Quality tolerance ε (F1 delta)
          </span>
          <input
            type="number"
            min={0}
            max={1}
            step={0.005}
            value={effectiveEpsilon}
            onChange={(e) => {
              setEpsilonTouched(true)
              setEpsilon(Number(e.target.value))
            }}
            className="input font-mono"
          />
        </label>

        <button onClick={submit} disabled={running} className="btn btn-primary h-[42px] w-full sm:w-auto">
          {running ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <Play className="h-4 w-4" />
              Run comparison
            </>
          )}
        </button>
      </div>
    </Card>
  )
}
