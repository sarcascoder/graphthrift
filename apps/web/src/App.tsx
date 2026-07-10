import { useCallback, useEffect, useState } from 'react'
import { FileText } from 'lucide-react'
import {
  api,
  ApiError,
  type ConfigResponse,
  type DatasetResponse,
  type Report,
  type RunRequest,
  type RunSummary,
} from './lib/api'
import { useTheme } from './lib/useTheme'
import { Header } from './components/Header'
import { ControlPanel } from './components/ControlPanel'
import { GateBanner } from './components/GateBanner'
import { MetricCards } from './components/MetricCards'
import { Charts } from './components/Charts'
import { StageTable } from './components/StageTable'
import { RunsHistory } from './components/RunsHistory'
import { EmptyState } from './components/EmptyState'
import { Card, SectionTitle, Skeleton, ErrorState, Chip } from './components/ui'

const DEFAULT_EPSILON = 0.02

export default function App() {
  const { theme, toggle } = useTheme()

  // Meta: config + dataset
  const [config, setConfig] = useState<ConfigResponse | null>(null)
  const [configLoading, setConfigLoading] = useState(true)
  const [dataset, setDataset] = useState<DatasetResponse | undefined>(undefined)

  // Runs list
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [runsLoading, setRunsLoading] = useState(true)
  const [runsError, setRunsError] = useState<string | undefined>(undefined)

  // Active report
  const [report, setReport] = useState<Report | null>(null)
  const [activeRunId, setActiveRunId] = useState<string | undefined>(undefined)
  const [running, setRunning] = useState(false)
  const [reportError, setReportError] = useState<string | undefined>(undefined)

  // ---- data loaders --------------------------------------------------------

  const loadRuns = useCallback(async () => {
    setRunsLoading(true)
    setRunsError(undefined)
    try {
      const data = await api.listRuns()
      setRuns(data)
    } catch (e) {
      setRunsError(e instanceof ApiError ? e.message : 'Failed to load runs')
    } finally {
      setRunsLoading(false)
    }
  }, [])

  const loadMeta = useCallback(async () => {
    setConfigLoading(true)
    try {
      const cfg = await api.getConfig()
      setConfig(cfg)
    } catch {
      setConfig(null)
    } finally {
      setConfigLoading(false)
    }
    try {
      const ds = await api.getDataset()
      setDataset(ds)
    } catch {
      setDataset(undefined)
    }
  }, [])

  useEffect(() => {
    void loadMeta()
    void loadRuns()
  }, [loadMeta, loadRuns])

  // ---- actions -------------------------------------------------------------

  const runComparison = useCallback(
    async (req: RunRequest) => {
      setRunning(true)
      setReportError(undefined)
      try {
        const r = await api.createRun(req)
        setReport(r)
        setActiveRunId(r.run_id)
        void loadRuns()
      } catch (e) {
        setReportError(e instanceof ApiError ? e.message : 'Run failed')
      } finally {
        setRunning(false)
      }
    },
    [loadRuns],
  )

  const selectRun = useCallback(async (id: string) => {
    setActiveRunId(id)
    setReportError(undefined)
    setRunning(true)
    try {
      const detail = await api.getRun(id)
      setReport(detail.report)
    } catch (e) {
      setReportError(e instanceof ApiError ? e.message : 'Failed to load run')
    } finally {
      setRunning(false)
    }
  }, [])

  const showEmpty = !report && !running && !reportError

  return (
    <div className="min-h-screen">
      <Header
        theme={theme}
        onToggleTheme={toggle}
        backend={config?.backend}
        backendLoading={configLoading}
      />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 sm:py-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_320px]">
          {/* Main column */}
          <div className="space-y-6">
            <ControlPanel
              onRun={runComparison}
              running={running}
              defaultEpsilon={config?.quality_epsilon ?? DEFAULT_EPSILON}
            />

            {reportError && (
              <ErrorState
                message={reportError}
                onRetry={activeRunId ? () => void selectRun(activeRunId) : undefined}
              />
            )}

            {running && !report && <RunningSkeleton />}

            {showEmpty && <EmptyState dataset={dataset} />}

            {report && (
              <div className="space-y-6">
                <GateBanner gate={report.gate} />
                <MetricCards report={report} />
                <Charts report={report} />
                <StageTable report={report} />
                <ReportFooter report={report} />
              </div>
            )}
          </div>

          {/* Sidebar */}
          <aside>
            <RunsHistory
              runs={runs}
              loading={runsLoading}
              error={runsError}
              activeRunId={activeRunId}
              onSelect={(id) => void selectRun(id)}
              onRefresh={() => void loadRuns()}
            />
          </aside>
        </div>

        <footer className="mx-auto mt-10 max-w-7xl border-t border-zinc-200 pt-6 text-center text-xs text-zinc-400 dark:border-zinc-800 dark:text-zinc-500">
          🪶 GraphThrift — an open-source LLM cost & latency optimizer for
          knowledge-graph ingestion. Every optimization is gated on graph quality.
        </footer>
      </main>
    </div>
  )
}

function RunningSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-28 w-full" />
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-80 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
      <Skeleton className="h-64 w-full" />
    </div>
  )
}

function ReportFooter({ report }: { report: Report }) {
  const cfg = report.config
  const activeOptimizers: string[] = []
  if (cfg.cache_enabled) activeOptimizers.push('response cache')
  if (cfg.embedding_cache_enabled) activeOptimizers.push('embedding cache')
  if (cfg.router_enabled) activeOptimizers.push('model router')
  if (cfg.dedup_prefilter_enabled) activeOptimizers.push('dedup prefilter')
  if (cfg.edge_batcher_enabled) activeOptimizers.push('edge batcher')
  if (cfg.compressor_enabled) activeOptimizers.push('prompt compressor')

  const gd = report.graph_diff

  return (
    <Card>
      <SectionTitle
        icon={<FileText className="h-4 w-4" />}
        title="Run detail"
        subtitle={report.candidate_label}
      />
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
        <div>
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Active optimizers
          </div>
          {activeOptimizers.length ? (
            <div className="flex flex-wrap gap-2">
              {activeOptimizers.map((o) => (
                <Chip key={o} tone="good">
                  {o}
                </Chip>
              ))}
            </div>
          ) : (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">None enabled (pure baseline).</p>
          )}
          <div className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
            Dedup threshold:{' '}
            <span className="font-mono text-zinc-700 dark:text-zinc-300">
              {cfg.dedup_threshold}
            </span>
            {cfg.router_downgrade_stages.length > 0 && (
              <>
                {' · '}downgrade stages:{' '}
                <span className="font-mono text-zinc-700 dark:text-zinc-300">
                  {cfg.router_downgrade_stages.join(', ')}
                </span>
              </>
            )}
          </div>
        </div>

        <div>
          <div className="mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Graph diff vs baseline
          </div>
          {gd.identical ? (
            <Chip tone="good">Identical graph — zero quality drift</Chip>
          ) : (
            <div className="grid grid-cols-2 gap-2 text-sm">
              <DiffStat label="Entities added" value={gd.entities_added} />
              <DiffStat label="Entities removed" value={gd.entities_removed} negative />
              <DiffStat label="Triples added" value={gd.triples_added} />
              <DiffStat label="Triples removed" value={gd.triples_removed} negative />
            </div>
          )}
          <div className="mt-3 text-xs text-zinc-500 dark:text-zinc-400">
            {report.n_episodes.toLocaleString()} episodes · run{' '}
            <span className="font-mono">{report.run_id.slice(0, 8)}</span>
          </div>
        </div>
      </div>
    </Card>
  )
}

function DiffStat({
  label,
  value,
  negative,
}: {
  label: string
  value: number
  negative?: boolean
}) {
  return (
    <div className="rounded-lg border border-zinc-200 bg-zinc-50/60 px-3 py-2 dark:border-zinc-800 dark:bg-zinc-950/40">
      <div className="text-[11px] text-zinc-500 dark:text-zinc-400">{label}</div>
      <div
        className={
          value === 0
            ? 'font-mono text-sm text-zinc-500'
            : negative
              ? 'font-mono text-sm font-semibold text-red-600 dark:text-red-400'
              : 'font-mono text-sm font-semibold text-zinc-800 dark:text-zinc-200'
        }
      >
        {value.toLocaleString()}
      </div>
    </div>
  )
}
