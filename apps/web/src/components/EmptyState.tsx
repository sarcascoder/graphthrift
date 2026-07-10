import { Sparkles } from 'lucide-react'
import type { DatasetResponse } from '../lib/api'
import { Card } from './ui'

export function EmptyState({ dataset }: { dataset?: DatasetResponse }) {
  return (
    <Card className="flex flex-col items-center gap-4 py-14 text-center">
      <div className="grid h-16 w-16 place-items-center rounded-2xl bg-brand-500/10 text-brand-500">
        <Sparkles className="h-8 w-8" />
      </div>
      <div>
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-50">
          Ready to shrink your ingestion bill
        </h3>
        <p className="mx-auto mt-1.5 max-w-md text-sm text-zinc-500 dark:text-zinc-400">
          Pick a scenario and run a comparison. GraphThrift profiles a baseline
          knowledge-graph pipeline against an optimized candidate, then proves the
          optimization is safe before recommending it.
        </p>
      </div>
      {dataset && (
        <div className="mt-2 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs text-zinc-500 dark:text-zinc-400">
          <Stat value={dataset.episodes.toLocaleString()} label="episodes" />
          <Stat value={dataset.gold_entities.toLocaleString()} label="gold entities" />
          <Stat value={dataset.gold_triples.toLocaleString()} label="gold triples" />
        </div>
      )}
      {dataset?.description && (
        <p className="max-w-md text-xs italic text-zinc-400 dark:text-zinc-500">
          {dataset.description}
        </p>
      )}
    </Card>
  )
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <span className="inline-flex items-baseline gap-1.5">
      <span className="font-mono text-base font-semibold text-zinc-800 dark:text-zinc-200">
        {value}
      </span>
      <span>{label}</span>
    </span>
  )
}
