import type { PropsWithChildren, ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { cx } from '../lib/format'

export function Card({
  className,
  children,
}: PropsWithChildren<{ className?: string }>) {
  return <div className={cx('card p-5 sm:p-6', className)}>{children}</div>
}

export function SectionTitle({
  icon,
  title,
  subtitle,
  right,
}: {
  icon?: ReactNode
  title: string
  subtitle?: string
  right?: ReactNode
}) {
  return (
    <div className="mb-4 flex items-start justify-between gap-4">
      <div className="flex items-center gap-2.5">
        {icon && (
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-brand-500/10 text-brand-500 dark:text-brand-400">
            {icon}
          </span>
        )}
        <div>
          <h2 className="text-base font-semibold tracking-tight text-zinc-900 dark:text-zinc-50">
            {title}
          </h2>
          {subtitle && (
            <p className="mt-0.5 text-xs text-zinc-500 dark:text-zinc-400">{subtitle}</p>
          )}
        </div>
      </div>
      {right}
    </div>
  )
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cx('skeleton', className)} />
}

export function ErrorState({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/5 p-4 text-sm text-red-700 dark:text-red-300">
      <div className="flex items-center gap-2 font-medium">
        <AlertTriangle className="h-4 w-4" />
        Something went wrong
      </div>
      <p className="text-red-600/90 dark:text-red-300/80">{message}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-ghost !py-1.5 !px-3 text-xs">
          Try again
        </button>
      )}
    </div>
  )
}

export function Chip({
  tone = 'neutral',
  children,
}: PropsWithChildren<{ tone?: 'good' | 'bad' | 'neutral' | 'accent' }>) {
  const tones: Record<string, string> = {
    good: 'bg-brand-500/15 text-brand-700 dark:text-brand-300 ring-1 ring-inset ring-brand-500/30',
    bad: 'bg-red-500/15 text-red-700 dark:text-red-300 ring-1 ring-inset ring-red-500/30',
    accent: 'bg-blue-500/15 text-blue-700 dark:text-blue-300 ring-1 ring-inset ring-blue-500/30',
    neutral:
      'bg-zinc-500/10 text-zinc-600 dark:text-zinc-300 ring-1 ring-inset ring-zinc-500/20',
  }
  return <span className={cx('chip', tones[tone])}>{children}</span>
}
