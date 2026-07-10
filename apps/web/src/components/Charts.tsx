import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  Legend,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { BarChart3, Gauge } from 'lucide-react'
import type { Report } from '../lib/api'
import { Card, SectionTitle } from './ui'

const BASELINE_COLOR = '#a1a1aa' // zinc-400
const OPTIMIZED_COLOR = '#10b981' // brand-500

function TooltipBox({
  active,
  payload,
  label,
  fmt,
}: {
  active?: boolean
  payload?: Array<{ name?: string; value?: number; color?: string }>
  label?: string
  fmt: (n: number) => string
}) {
  if (!active || !payload || payload.length === 0) return null
  return (
    <div className="rounded-lg border border-zinc-200 bg-white/95 px-3 py-2 text-xs shadow-lg backdrop-blur dark:border-zinc-700 dark:bg-zinc-900/95">
      <div className="mb-1 font-medium text-zinc-700 dark:text-zinc-200">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 text-zinc-600 dark:text-zinc-300">
          <span className="h-2 w-2 rounded-full" style={{ background: p.color }} />
          <span className="tabular-nums">
            {p.name}: {fmt(p.value ?? 0)}
          </span>
        </div>
      ))}
    </div>
  )
}

export function Charts({ report }: { report: Report }) {
  const { baseline, candidate, gate } = report

  // Normalize the three savings dimensions to a 0–100 scale so they share one
  // chart: baseline is always 100%, optimized is the remaining fraction.
  const relative = (base: number, opt: number) =>
    base > 0 ? Math.max(0, (opt / base) * 100) : 0

  const savingsData = [
    {
      metric: 'Cost',
      Baseline: 100,
      Optimized: relative(baseline.trace.total_cost_usd, candidate.trace.total_cost_usd),
    },
    {
      metric: 'LLM calls',
      Baseline: 100,
      Optimized: relative(baseline.trace.total_llm_calls, candidate.trace.total_llm_calls),
    },
    {
      metric: 'Latency',
      Baseline: 100,
      Optimized: relative(baseline.trace.total_latency_ms, candidate.trace.total_latency_ms),
    },
  ]

  const qualityData = [
    {
      metric: 'Entity F1',
      Baseline: baseline.eval.entity.f1 * 100,
      Optimized: candidate.eval.entity.f1 * 100,
    },
    {
      metric: 'Triple F1',
      Baseline: baseline.eval.triple.f1 * 100,
      Optimized: candidate.eval.triple.f1 * 100,
    },
  ]

  const epsPct = gate.epsilon * 100

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <SectionTitle
          icon={<BarChart3 className="h-4 w-4" />}
          title="Baseline vs optimized"
          subtitle="Relative to baseline (100%) — lower optimized bar = bigger win"
        />
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={savingsData} margin={{ top: 16, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-800" vertical={false} />
              <XAxis dataKey="metric" tick={{ fontSize: 12 }} className="fill-zinc-500" tickLine={false} axisLine={false} />
              <YAxis
                tick={{ fontSize: 11 }}
                className="fill-zinc-500"
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                unit="%"
              />
              <Tooltip
                cursor={{ fill: 'rgba(113,113,122,0.08)' }}
                content={<TooltipBox fmt={(n) => `${n.toFixed(1)}%`} />}
              />
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} iconType="circle" />
              <Bar dataKey="Baseline" fill={BASELINE_COLOR} radius={[4, 4, 0, 0]} maxBarSize={46} />
              <Bar dataKey="Optimized" fill={OPTIMIZED_COLOR} radius={[4, 4, 0, 0]} maxBarSize={46}>
                <LabelList
                  dataKey="Optimized"
                  position="top"
                  formatter={(v: number) => `${v.toFixed(0)}%`}
                  className="fill-brand-600 dark:fill-brand-400"
                  style={{ fontSize: 11, fontWeight: 600 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card>
        <SectionTitle
          icon={<Gauge className="h-4 w-4" />}
          title="Graph quality (F1)"
          subtitle={`Shaded band = ε tolerance (±${epsPct.toFixed(1)} pts) around baseline`}
        />
        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={qualityData} margin={{ top: 16, right: 8, left: -12, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-zinc-200 dark:stroke-zinc-800" vertical={false} />
              <XAxis dataKey="metric" tick={{ fontSize: 12 }} className="fill-zinc-500" tickLine={false} axisLine={false} />
              <YAxis
                tick={{ fontSize: 11 }}
                className="fill-zinc-500"
                tickLine={false}
                axisLine={false}
                domain={[0, 100]}
                unit="%"
              />
              <Tooltip
                cursor={{ fill: 'rgba(113,113,122,0.08)' }}
                content={<TooltipBox fmt={(n) => `${n.toFixed(1)}%`} />}
              />
              {/* Epsilon tolerance band, per metric, around the baseline F1. */}
              {qualityData.map((d, i) => (
                <ReferenceArea
                  key={i}
                  x1={d.metric}
                  x2={d.metric}
                  y1={Math.max(0, d.Baseline - epsPct)}
                  y2={Math.min(100, d.Baseline + epsPct)}
                  fill="#10b981"
                  fillOpacity={0.12}
                  ifOverflow="hidden"
                />
              ))}
              <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} iconType="circle" />
              <Bar dataKey="Baseline" fill={BASELINE_COLOR} radius={[4, 4, 0, 0]} maxBarSize={46} />
              <Bar dataKey="Optimized" radius={[4, 4, 0, 0]} maxBarSize={46}>
                {qualityData.map((d, i) => {
                  const within = d.Optimized >= d.Baseline - epsPct
                  return <Cell key={i} fill={within ? OPTIMIZED_COLOR : '#ef4444'} />
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>
    </div>
  )
}
