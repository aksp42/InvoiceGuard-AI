// Phase 6 — Analytics aggregation helpers.
// Pure functions that transform the existing REST payloads into
// chart-ready series (the same business measures we report to Power BI).

export const STATUS_LABELS = {
  Valid: 'Valid',
  'Needs Review': 'Needs Review',
  'High Risk': 'High Risk',
  Critical: 'Critical',
  Duplicate: 'Duplicate',
  Pending: 'Pending',
  Paid: 'Paid',
}

export const STATUS_COLORS = {
  Valid: '#34d399',
  'Needs Review': '#fbbf24',
  'High Risk': '#f87171',
  Critical: '#ef4444',
  Duplicate: '#818cf8',
  Pending: '#94a3b8',
  Paid: '#38bdf8',
}

export const DUPLICATE_LABELS = {
  DUPLICATE_EXACT: 'Exact',
  DUPLICATE_VENDOR: 'Vendor',
  DUPLICATE_NEAR: 'Near',
  DUPLICATE_DATE: 'Amount + Date',
  DUPLICATE_ITEM: 'Item-Level',
}

export const DUPLICATE_COLORS = {
  DUPLICATE_EXACT: '#ef4444',
  DUPLICATE_VENDOR: '#fb923c',
  DUPLICATE_NEAR: '#fbbf24',
  DUPLICATE_DATE: '#fbbf24',
  DUPLICATE_ITEM: '#818cf8',
}

export const fmtINR = (n) =>
  n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export const fmtINR2 = (n) =>
  n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

export const fmtInt = (n) =>
  n == null ? '—' : Number(n).toLocaleString('en-IN')

const pad = (n) => String(n).padStart(2, '0')

// Group invoices by ISO date key (YYYY-MM-DD) into a time series.
export function monthlySeries(invoices, { top = null } = {}) {
  const byKey = {}
  for (const inv of invoices || []) {
    if (!inv.invoice_date) continue
    let key = String(inv.invoice_date).slice(0, 10)
    if (key.length === 10) key = key.slice(0, 7) // group by month (YYYY-MM)
    byKey[key] = byKey[key] || 0
    byKey[key] += 1
  }
  let keys = Object.keys(byKey).sort()
  if (top != null && keys.length > top) keys = keys.slice(keys.length - top)
  const monthLabel = (k) => {
    const [y, m] = k.split('-')
    return `${y}-${pad(m)}`
  }
  return keys.map((k) => ({ label: monthLabel(k), value: byKey[k] }))
}

// Amount trends: sum of total_amount per month.
export function amountSeries(invoices) {
  const byKey = {}
  for (const inv of invoices || []) {
    if (!inv.invoice_date) continue
    const key = String(inv.invoice_date).slice(0, 7)
    byKey[key] = (byKey[key] || 0) + Number(inv.total_amount || 0)
  }
  return Object.keys(byKey).sort().map((k) => ({
    label: k,
    value: Math.round(byKey[k]),
  }))
}

// Status distribution (validation insights).
export function statusDistribution(invoices) {
  const dist = {}
  for (const inv of invoices || []) {
    const s = inv.status || 'Pending'
    dist[s] = (dist[s] || 0) + 1
  }
  return Object.entries(dist)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, color: STATUS_COLORS[label] || '#94a3b8' }))
}

// Vendor intelligence: per-vendor aggregation.
export function vendorIntelligence(invoices) {
  const map = {}
  for (const inv of invoices || []) {
    const name = inv.vendor_name || 'Unknown Vendor'
    map[name] = map[name] || { name, count: 0, amount: 0, highRisk: 0, risky: 0 }
    map[name].count += 1
    map[name].amount += Number(inv.total_amount || 0)
    if (inv.status === 'High Risk' || inv.status === 'Critical') map[name].highRisk += 1
    if (inv.risk_score >= 40) map[name].risky += 1
  }
  return Object.values(map).sort((a, b) => b.amount - a.amount)
}

// Risk score distribution buckets.
export function riskBuckets(invoices, buckets = [0, 25, 50, 75, 101]) {
  const labels = []
  for (let i = 0; i < buckets.length - 1; i++) {
    labels.push({ from: buckets[i], to: buckets[i + 1] })
  }
  const out = labels.map((b) => ({
    label: `${b.from}–${b.to === 101 ? '100' : b.to}`,
    value: 0,
  }))
  for (const inv of invoices || []) {
    const s = Number(inv.risk_score || 0)
    const idx = labels.findIndex((b) => s >= b.from && s < b.to)
    if (idx >= 0) out[idx].value += 1
  }
  return out
}

// Duplicate intelligence: pairs grouped by detection level + amount at risk.
export function duplicateIntelligence(pairs) {
  const byType = {}
  for (const p of pairs || []) {
    const t = p.validation_type || 'DUPLICATE_ITEM'
    byType[t] = byType[t] || { type: t, count: 0, amount: 0, severity: p.severity || 'WARNING', confidence: p.confidence_score || 0 }
    byType[t].count += 1
    byType[t].amount += Math.abs(Number(p.amount_a || 0))
    byType[t].confidence = Math.max(byType[t].confidence, Number(p.confidence_score || 0))
  }
  const ordered = ['DUPLICATE_EXACT', 'DUPLICATE_VENDOR', 'DUPLICATE_NEAR', 'DUPLICATE_DATE', 'DUPLICATE_ITEM']
  return ordered.filter((t) => byType[t]).map((t) => byType[t])
}

// KPIs shared by the executive overview.
export function computeKpis(invoices, batches, pairs) {
  const highRisk = (invoices || []).filter((i) => i.status === 'High Risk' || i.status === 'Critical')
  const dupStatus = (invoices || []).filter((i) => i.status === 'Duplicate')
  const potentialLoss = (invoices || []).reduce(
    (s, i) => s + (i.status === 'High Risk' || i.status === 'Critical' || i.status === 'Duplicate' ? Number(i.total_amount || 0) : 0),
    0,
  )
  const totalUploads = (batches || []).length
  const processed = (batches || []).reduce((s, b) => s + Number(b.processed_invoices || 0), 0)
  const failed = (batches || []).reduce((s, b) => s + Number(b.failed_invoices || 0), 0)
  return {
    totalUploads,
    totalInvoices: (invoices || []).length,
    processed,
    failed,
    valid: (invoices || []).filter((i) => i.status === 'Valid').length,
    highRisk: highRisk.length,
    duplicate: dupStatus.length + (pairs || []).length,
    potentialLoss,
  }
}
