import { History, CheckCircle2, XCircle, RefreshCw } from 'lucide-react'
import type { RunSummary } from '../lib/api'
import { Card, SectionTitle, Skeleton, ErrorState } from './ui'
import { cx, pct, relativeTime } from '../lib/format'

export function RunsHistory({
  runs,
  loading,
  error,
  activeRunId,
  onSelect,
  onRefresh,
}: {
  runs: RunSummary[]
  loading: boolean
  error?: string
  activeRunId?: string
  onSelect: (id: string) => void
  onRefresh: () => void
}) {
  return (
    <Card className="lg:sticky lg:top-20">
      <SectionTitle
        icon={<History className="h-4 w-4" />}
        title="Run history"
        subtitle="Click to reload a past comparison"
        right={
          <button
            onClick={onRefresh}
            aria-label="Refresh runs"
            className="grid h-8 w-8 place-items-center rounded-lg border border-zinc-200 text-zinc-500 transition hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-800"
          >
            <RefreshCw className={cx('h-3.5 w-3.5', loading && 'animate-spin')} />
          </button>
        }
      />

      {error ? (
        <ErrorState message={error} onRetry={onRefresh} />
      ) : loading && runs.length === 0 ? (
        <div className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : runs.length === 0 ? (
        <p className="rounded-xl border border-dashed border-zinc-200 px-4 py-8 text-center text-sm text-zinc-500 dark:border-zinc-800 dark:text-zinc-400">
          No runs yet. Run your first comparison to see it here.
        </p>
      ) : (
        <ul className="max-h-[calc(100vh-12rem)] space-y-2 overflow-y-auto pr-1">
          {runs.map((r) => {
            const active = r.run_id === activeRunId
            return (
              <li key={r.run_id}>
                <button
                  onClick={() => onSelect(r.run_id)}
                  className={cx(
                    'w-full rounded-xl border p-3 text-left transition',
                    active
                      ? 'border-brand-500/50 bg-brand-500/10 ring-1 ring-brand-500/20'
                      : 'border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-900/40 dark:hover:border-zinc-700 dark:hover:bg-zinc-800/60',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-1.5 text-sm font-medium capitalize text-zinc-800 dark:text-zinc-100">
                      {r.gate_passed ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-brand-500" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 text-red-500" />
                      )}
                      {r.scenario}
                    </span>
                    <span className="font-mono text-xs font-semibold text-brand-600 dark:text-brand-400">
                      −{pct(r.cost_reduction_pct, 0)}
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-center justify-between gap-2 text-[11px] text-zinc-500 dark:text-zinc-400">
                    <span
                      className={cx(
                        'rounded-md px-1.5 py-0.5 font-medium',
                        r.gate_passed
                          ? 'bg-brand-500/10 text-brand-700 dark:text-brand-300'
                          : 'bg-red-500/10 text-red-700 dark:text-red-300',
                      )}
                    >
                      {r.gate_passed ? 'gate pass' : 'gate fail'}
                    </span>
                    <span>{relativeTime(r.created_at)}</span>
                  </div>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </Card>
  )
}
