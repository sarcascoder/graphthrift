import { Layers, Flame } from 'lucide-react'
import type { Report, StageMetrics } from '../lib/api'
import { Card, SectionTitle, Chip } from './ui'
import { cx, integer, money } from '../lib/format'

// The per-edge fan-out stages — the "money" stages worth highlighting.
const MONEY_STAGES = new Set(['resolve_edge', 'extract_timestamps'])

interface Row {
  stage: string
  baselineCalls: number
  optimizedCalls: number
  eliminated: number
  baselineCost: number
  optimizedCost: number
  isMoney: boolean
}

function prettyStage(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

export function StageTable({ report }: { report: Report }) {
  const base = report.baseline.trace.by_stage
  const cand = report.candidate.trace.by_stage
  const stageNames = Array.from(new Set([...Object.keys(base), ...Object.keys(cand)]))

  const rows: Row[] = stageNames.map((stage) => {
    const b: StageMetrics = base[stage] ?? { calls: 0, cost: 0, latency_ms: 0, eliminated: 0 }
    const c: StageMetrics = cand[stage] ?? { calls: 0, cost: 0, latency_ms: 0, eliminated: 0 }
    return {
      stage,
      baselineCalls: b.calls,
      optimizedCalls: c.calls,
      eliminated: c.eliminated || Math.max(0, b.calls - c.calls),
      baselineCost: b.cost,
      optimizedCost: c.cost,
      isMoney: MONEY_STAGES.has(stage),
    }
  })

  // Money stages first, then by baseline cost descending.
  rows.sort((a, b) => {
    if (a.isMoney !== b.isMoney) return a.isMoney ? -1 : 1
    return b.baselineCost - a.baselineCost
  })

  const totalEliminated = rows.reduce((s, r) => s + r.eliminated, 0)

  return (
    <Card>
      <SectionTitle
        icon={<Layers className="h-4 w-4" />}
        title="Per-stage breakdown"
        subtitle="Where the calls (and cost) go — highlighted rows are the per-edge fan-out"
        right={
          <Chip tone="good">
            <Flame className="h-3 w-3" />
            {integer(totalEliminated)} calls eliminated
          </Chip>
        }
      />

      <div className="-mx-1 overflow-x-auto">
        <table className="w-full min-w-[560px] border-separate border-spacing-0 text-sm">
          <thead>
            <tr className="text-left text-xs uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              <th className="px-3 py-2 font-medium">Stage</th>
              <th className="px-3 py-2 text-right font-medium">Baseline calls</th>
              <th className="px-3 py-2 text-right font-medium">Optimized calls</th>
              <th className="px-3 py-2 text-right font-medium">Eliminated</th>
              <th className="px-3 py-2 text-right font-medium">Cost (base → opt)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const savedCalls = r.eliminated > 0
              return (
                <tr
                  key={r.stage}
                  className={cx(
                    'group border-t border-zinc-100 transition-colors dark:border-zinc-800/70',
                    r.isMoney
                      ? 'bg-amber-500/[0.07] hover:bg-amber-500/10'
                      : 'hover:bg-zinc-50 dark:hover:bg-zinc-800/40',
                  )}
                >
                  <td className="whitespace-nowrap px-3 py-2.5">
                    <div className="flex items-center gap-2">
                      {r.isMoney && <Flame className="h-3.5 w-3.5 text-amber-500" />}
                      <span
                        className={cx(
                          'font-medium',
                          r.isMoney ? 'text-amber-700 dark:text-amber-300' : 'text-zinc-800 dark:text-zinc-200',
                        )}
                      >
                        {prettyStage(r.stage)}
                      </span>
                    </div>
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums text-zinc-600 dark:text-zinc-400">
                    {integer(r.baselineCalls)}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums text-zinc-800 dark:text-zinc-200">
                    {integer(r.optimizedCalls)}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums">
                    {savedCalls ? (
                      <span className="text-brand-600 dark:text-brand-400">−{integer(r.eliminated)}</span>
                    ) : (
                      <span className="text-zinc-400 dark:text-zinc-600">—</span>
                    )}
                  </td>
                  <td className="px-3 py-2.5 text-right font-mono tabular-nums">
                    <span className="text-zinc-400 line-through decoration-zinc-400/50 dark:text-zinc-500">
                      {money(r.baselineCost)}
                    </span>
                    <span className="mx-1 text-zinc-400">→</span>
                    <span className="text-zinc-800 dark:text-zinc-200">{money(r.optimizedCost)}</span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </Card>
  )
}
