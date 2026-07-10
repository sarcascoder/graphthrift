import { CheckCircle2, ShieldAlert } from 'lucide-react'
import type { Gate } from '../lib/api'
import { cx, signedPct } from '../lib/format'

export function GateBanner({ gate }: { gate: Gate }) {
  const passed = gate.passed
  return (
    <div
      className={cx(
        'animate-fade-in overflow-hidden rounded-2xl border shadow-card',
        passed
          ? 'border-brand-500/40 bg-gradient-to-br from-brand-500/15 to-brand-500/5'
          : 'border-red-500/40 bg-gradient-to-br from-red-500/15 to-red-500/5',
      )}
    >
      <div className="flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
        <div className="flex items-start gap-4">
          <div
            className={cx(
              'grid h-12 w-12 flex-none place-items-center rounded-xl',
              passed
                ? 'bg-brand-500/20 text-brand-600 dark:text-brand-400'
                : 'bg-red-500/20 text-red-600 dark:text-red-400',
            )}
          >
            {passed ? <CheckCircle2 className="h-7 w-7" /> : <ShieldAlert className="h-7 w-7" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2
                className={cx(
                  'text-lg font-bold tracking-tight sm:text-xl',
                  passed ? 'text-brand-700 dark:text-brand-300' : 'text-red-700 dark:text-red-300',
                )}
              >
                {passed ? 'SAFE — apply' : 'UNSAFE — flagged, not applied'}
              </h2>
            </div>
            <p className="mt-1 max-w-2xl text-sm text-zinc-600 dark:text-zinc-300">
              {passed
                ? 'The optimized candidate stayed within the quality tolerance. It is safe to roll out.'
                : 'The optimized candidate regressed graph quality beyond ε. GraphThrift blocked it.'}
            </p>
            {gate.reasons.length > 0 && (
              <ul className="mt-3 space-y-1">
                {gate.reasons.map((r, i) => (
                  <li
                    key={i}
                    className="flex items-start gap-2 text-xs text-zinc-600 dark:text-zinc-400"
                  >
                    <span
                      className={cx(
                        'mt-1.5 h-1.5 w-1.5 flex-none rounded-full',
                        passed ? 'bg-brand-500' : 'bg-red-500',
                      )}
                    />
                    {r}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="flex gap-6 sm:flex-col sm:gap-3 sm:text-right">
          <GateDelta label="Entity F1 Δ" value={gate.entity_f1_delta} />
          <GateDelta label="Triple F1 Δ" value={gate.triple_f1_delta} />
          <div className="hidden text-xs text-zinc-500 dark:text-zinc-400 sm:block">
            ε tolerance = <span className="font-mono">{gate.epsilon.toFixed(3)}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

function GateDelta({ label, value }: { label: string; value: number }) {
  // Positive or zero delta is good (quality held or improved).
  const good = value >= -1e-9
  return (
    <div>
      <div className="text-[11px] uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        {label}
      </div>
      <div
        className={cx(
          'font-mono text-sm font-semibold',
          good ? 'text-brand-600 dark:text-brand-400' : 'text-red-600 dark:text-red-400',
        )}
      >
        {signedPct(value * 100, 2)}
      </div>
    </div>
  )
}
