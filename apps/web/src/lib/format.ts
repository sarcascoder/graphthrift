// Small formatting helpers shared across components.

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

const usd0 = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

const usd2 = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 2,
})

const num = new Intl.NumberFormat('en-US')

export function money0(n: number): string {
  return usd0.format(n)
}

export function money(n: number): string {
  // Use more precision for tiny per-episode figures.
  if (Math.abs(n) > 0 && Math.abs(n) < 1) {
    return `$${n.toPrecision(3)}`
  }
  return usd2.format(n)
}

export function integer(n: number): string {
  return num.format(Math.round(n))
}

export function pct(n: number, digits = 1): string {
  const sign = n > 0 ? '' : ''
  return `${sign}${n.toFixed(digits)}%`
}

export function signedPct(n: number, digits = 2): string {
  const s = n > 0 ? '+' : n < 0 ? '−' : ''
  return `${s}${Math.abs(n).toFixed(digits)}%`
}

export function ms(n: number): string {
  if (n >= 1000) return `${(n / 1000).toFixed(2)} s`
  return `${integer(n)} ms`
}

export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return iso
  const diff = Date.now() - then
  const s = Math.round(diff / 1000)
  if (s < 60) return 'just now'
  const m = Math.round(s / 60)
  if (m < 60) return `${m}m ago`
  const h = Math.round(m / 60)
  if (h < 24) return `${h}h ago`
  const d = Math.round(h / 24)
  if (d < 30) return `${d}d ago`
  return new Date(then).toLocaleDateString()
}
