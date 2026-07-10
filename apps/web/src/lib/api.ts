// Typed API client for the GraphThrift backend.
//
// In dev/preview the Vite server proxies /v1, /healthz and /metrics to
// VITE_API_BASE, so relative requests work out of the box. When the built
// site is served standalone (e.g. behind nginx), we fall back to the absolute
// VITE_API_BASE if provided.

export const API_BASE: string = (import.meta.env.VITE_API_BASE ?? '').replace(/\/+$/, '')

// ---------------------------------------------------------------------------
// Types mirroring the backend response shapes.
// ---------------------------------------------------------------------------

export type Scenario = 'safe' | 'aggressive' | 'custom'

export interface OptimizerOverrides {
  cache_enabled?: boolean
  embedding_cache_enabled?: boolean
  router_enabled?: boolean
  dedup_prefilter_enabled?: boolean
  edge_batcher_enabled?: boolean
  compressor_enabled?: boolean
  router_downgrade_stages?: string[]
}

export interface RunRequest {
  scenario: Scenario
  monthly_volume: number
  epsilon?: number
  overrides?: OptimizerOverrides
}

export interface StageMetrics {
  calls: number
  cost: number
  latency_ms: number
  eliminated: number
}

export interface Trace {
  total_cost_usd: number
  total_llm_calls: number
  calls_eliminated: number
  cache_hits: number
  routed_calls: number
  prompt_tokens: number
  completion_tokens: number
  total_latency_ms: number
  latency_p50_ms: number
  latency_p95_ms: number
  by_stage: Record<string, StageMetrics>
}

export interface EvalScore {
  precision: number
  recall: number
  f1: number
  tp: number
  fp: number
  fn: number
}

export interface EvalResult {
  entity: EvalScore
  triple: EvalScore
}

export interface Side {
  trace: Trace
  eval: EvalResult
}

export interface OptimizerConfig {
  cache_enabled: boolean
  embedding_cache_enabled: boolean
  router_enabled: boolean
  dedup_prefilter_enabled: boolean
  edge_batcher_enabled: boolean
  compressor_enabled: boolean
  router_downgrade_stages: string[]
  dedup_threshold: number
}

export interface Savings {
  cost_reduction_pct: number
  llm_calls_reduction_pct: number
  latency_reduction_pct: number
  calls_eliminated: number
  cache_hits: number
  routed_calls: number
  per_episode_saved_usd: number
  monthly_volume_episodes: number
  projected_monthly_saved_usd: number
}

export interface Gate {
  passed: boolean
  epsilon: number
  entity_f1_delta: number
  triple_f1_delta: number
  reasons: string[]
}

export interface GraphDiff {
  entities_added: number
  entities_removed: number
  triples_added: number
  triples_removed: number
  identical: boolean
}

export interface Report {
  candidate_label: string
  run_id: string
  n_episodes: number
  verdict: string
  config: OptimizerConfig
  baseline: Side
  candidate: Side
  savings: Savings
  gate: Gate
  graph_diff: GraphDiff
}

export interface RunSummary {
  run_id: string
  label: string
  scenario: string
  backend: string
  gate_passed: boolean
  cost_reduction_pct: number
  latency_reduction_pct: number
  calls_reduction_pct: number
  n_episodes: number
  created_at: string
}

export interface RunDetail extends RunSummary {
  report: Report
}

export interface TracesResponse {
  run_id: string
  baseline_by_stage: Record<string, StageMetrics>
  candidate_by_stage: Record<string, StageMetrics>
}

export interface ConfigResponse {
  backend: string
  quality_epsilon: number
  defaults: OptimizerConfig
}

export interface DatasetResponse {
  episodes: number
  gold_entities: number
  gold_triples: number
  description: string
}

// ---------------------------------------------------------------------------
// Fetch helpers
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  let res: Response
  try {
    res = await fetch(url, {
      ...init,
      headers: {
        Accept: 'application/json',
        ...(init?.body ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })
  } catch (e) {
    throw new ApiError(
      `Network error reaching the GraphThrift API${API_BASE ? ` at ${API_BASE}` : ''}. Is it running?`,
      0,
    )
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body?.detail) detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
    } catch {
      /* ignore parse errors */
    }
    throw new ApiError(`${res.status} · ${detail}`, res.status)
  }

  return (await res.json()) as T
}

export const api = {
  createRun: (body: RunRequest) =>
    request<Report>('/v1/runs', { method: 'POST', body: JSON.stringify(body) }),
  listRuns: () => request<RunSummary[]>('/v1/runs'),
  getRun: (id: string) => request<RunDetail>(`/v1/runs/${encodeURIComponent(id)}`),
  getTraces: (id: string) => request<TracesResponse>(`/v1/runs/${encodeURIComponent(id)}/traces`),
  getConfig: () => request<ConfigResponse>('/v1/config'),
  getDataset: () => request<DatasetResponse>('/v1/dataset'),
}
