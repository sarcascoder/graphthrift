import type { ReactNode } from 'react'
import { DollarSign, Phone, Timer, PiggyBank, ArrowRight } from 'lucide-react'
import type { Report } from '../lib/api'
import { cx, money, money0, ms, pct } from '../lib/format'

export function MetricCards({ report }: { report: Report }) {
  const { savings, baseline, candidate } = report

  const cards = [
    {
      icon: <DollarSign className="h-4 w-4" />,
      label: 'Cost',
      reduction: savings.cost_reduction_pct,
      baseline: money(baseline.trace.total_cost_usd),
      optimized: money(candidate.trace.total_cost_usd),
    },
    {
      icon: <Phone className="h-4 w-4" />,
      label: 'LLM calls',
      reduction: savings.llm_calls_reduction_pct,
      baseline: baseline.trace.total_llm_calls.toLocaleString(),
      optimized: candidate.trace.total_llm_calls.toLocaleString(),
    },
    {
      icon: <Timer className="h-4 w-4" />,
      label: 'Latency',
      reduction: savings.latency_reduction_pct,
      baseline: ms(baseline.trace.total_latency_ms),
      optimized: ms(candidate.trace.total_latency_ms),
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => (
        <ReductionCard key={c.label} {...c} />
      ))}

      {/* Projected monthly savings — the hero number */}
      <div className="animate-fade-in rounded-2xl border border-brand-500/40 bg-gradient-to-br from-brand-500/15 to-brand-500/5 p-5 shadow-card">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-2 text-xs font-medium text-brand-700 dark:text-brand-300">
            <PiggyBank className="h-4 w-4" />
            Projected savings
          </span>
        </div>
        <div className="mt-3 font-mono text-3xl font-bold tracking-tight text-brand-700 dark:text-brand-300">
          {money0(savings.projected_monthly_saved_usd)}
        </div>
        <div className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
          per month at{' '}
          <span className="font-medium">
            {savings.monthly_volume_episodes.toLocaleString()}
          </span>{' '}
          episodes
        </div>
        <div className="mt-2 text-[11px] text-zinc-500 dark:text-zinc-500">
          {money(savings.per_episode_saved_usd)} saved / episode
        </div>
      </div>
    </div>
  )
}

function ReductionCard({
  icon,
  label,
  reduction,
  baseline,
  optimized,
}: {
  icon: ReactNode
  label: string
  reduction: number
  baseline: string
  optimized: string
}) {
  const positive = reduction > 0.05
  return (
    <div className="animate-fade-in card p-5">
      <div className="flex items-center justify-between">
        <span className="flex items-center gap-2 text-xs font-medium text-zinc-500 dark:text-zinc-400">
          <span className="grid h-6 w-6 place-items-center rounded-md bg-zinc-500/10 text-zinc-500 dark:text-zinc-400">
            {icon}
          </span>
          {label}
        </span>
      </div>
      <div
        className={cx(
          'mt-3 font-mono text-3xl font-bold tracking-tight',
          positive ? 'text-brand-600 dark:text-brand-400' : 'text-zinc-700 dark:text-zinc-300',
        )}
      >
        −{pct(reduction)}
      </div>
      <div className="mt-2 flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
        <span className="font-mono line-through decoration-zinc-400/60">{baseline}</span>
        <ArrowRight className="h-3 w-3 text-brand-500" />
        <span className="font-mono font-medium text-zinc-700 dark:text-zinc-200">{optimized}</span>
      </div>
    </div>
  )
}
