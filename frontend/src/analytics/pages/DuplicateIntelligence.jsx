// Phase 6 — Duplicate Intelligence.
import AnalyticsShell, { LoadingGrid } from '../components/AnalyticsShell.jsx'
import AnimatedCounter from '../components/AnimatedCounter.jsx'
import ErrorBanner from '../components/ErrorBanner.jsx'
import { BarChart, DonutChart, LineChart, TrendCard, EmptyState } from '../components/charts.jsx'
import useAnalyticsData from '../lib/useAnalyticsData.js'
import {
  duplicateIntelligence, DUPLICATE_LABELS, DUPLICATE_COLORS, fmtINR, fmtInt,
} from '../lib/aggregations.js'

const SEVERITY_COLORS = { CRITICAL: '#ef4444', ERROR: '#fb923c', WARNING: '#fbbf24' }

export default function DuplicateIntelligence() {
  const { pairs, invoices, loading, error, reload } = useAnalyticsData()

  if (loading) {
    return (
      <AnalyticsShell title="Duplicate Intelligence" subtitle="Duplicate risk by detection level and financial exposure.">
        <LoadingGrid cards={4} charts={2} />
      </AnalyticsShell>
    )
  }

  const levels = duplicateIntelligence(pairs)
  const totalPairs = (pairs || []).length
  const totalExposure = (levels || []).reduce((s, l) => s + l.amount, 0)

  if (!pairs || pairs.length === 0) {
    return (
      <AnalyticsShell title="Duplicate Intelligence" subtitle="Duplicate risk by detection level and financial exposure.">
        <ErrorBanner message={error} onRetry={reload} />
        <div className="glass"><EmptyState icon="🔁" title="No duplicates detected" message="Run the duplicate scanner on uploaded batches (POST /api/duplicates/{batch_id}). Detected pairs will appear here grouped by level." /></div>
      </AnalyticsShell>
    )
  }

  const criticalPairs = levels.filter((l) => l.severity === 'CRITICAL').reduce((s, l) => s + l.count, 0)
  const maxConfidence = Math.max(...levels.map((l) => l.confidence || 0))

  const dkpis = [
    { label: 'Duplicate Pairs', value: totalPairs, icon: '🔁', accent: '#fb923c', sub: 'deduplicated pair rows' },
    { label: 'Critical Level', value: criticalPairs, icon: '🚨', accent: '#ef4444', sub: 'exact/vendor matches' },
    { label: 'Exposure (₹)', value: totalExposure, fmt: 'inr', icon: '💰', accent: '#fbbf24', sub: 'sum of dupe amounts' },
    { label: 'Max Confidence', value: `${Math.round(maxConfidence)}%`, icon: '🎯', accent: '#38bdf8', sub: 'highest certainty match' },
  ]

  const donutData = levels.map((l, i) => ({
    label: DUPLICATE_LABELS[l.type] || l.type,
    value: l.count,
    color: DUPLICATE_COLORS[l.type] || color(i),
  }))

  return (
    <AnalyticsShell title="Duplicate Intelligence" subtitle="Duplicate risk by detection level and financial exposure.">
      <ErrorBanner message={error} onRetry={reload} />

      <div className="kpi-grid">
        {dkpis.map((kp) => (
          <div key={kp.label} className="glass kpi-card">
            <div className="ico" style={{ background: `${kp.accent}22`, color: kp.accent }}>{kp.icon}</div>
            <div className="k-label">{kp.label}</div>
            <div className="k-value" style={{ fontSize: 24 }}>
              {typeof kp.value === 'string'
                ? kp.value
                : <AnimatedCounter value={kp.value} format={(n) => (kp.fmt === 'inr' ? fmtINR(n) : fmtInt(n))} />}
            </div>
            <div className="k-sub">{kp.sub}</div>
          </div>
        ))}
      </div>

      <div className="analytics-grid grid-2" style={{ marginBottom: 20 }}>
        <div className="glass">
          <div className="g-title">Pairs by Detection Level</div>
          {levels.length ? (
            <BarChart
              data={levels.map((l) => ({ label: DUPLICATE_LABELS[l.type] || l.type, value: l.count, color: DUPLICATE_COLORS[l.type] }))}
              valueColor="#cbd5e1"
            />
          ) : <EmptyState icon="📊" />}
        </div>
        <div className="glass">
          <div className="g-title">Detection Mix</div>
          <DonutChart data={donutData} centerValue={totalPairs} centerLabel="pairs" />
        </div>
      </div>

      <div className="analytics-grid grid-3">
        <div className="glass">
          <div className="g-title">Confidence by Level</div>
          {levels.length ? (
            <LineChart data={levels.map((l) => ({ label: (DUPLICATE_LABELS[l.type] || l.type).slice(0, 8), value: l.confidence || 0 }))} color="#38bdf8" />
          ) : <EmptyState icon="🎯" />}
        </div>
        <div className="glass">
          <div className="g-title">Exposure by Level (₹)</div>
          {levels.length ? (
            <BarChart data={levels.map((l) => ({ label: DUPLICATE_LABELS[l.type] || l.type, value: l.amount, color: DUPLICATE_COLORS[l.type] }))} />
          ) : <EmptyState icon="💰" />}
        </div>
        <div className="glass">
          <div className="g-title">Level Analytics</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {levels.map((l) => (
              <TrendCard
                key={l.type}
                label={DUPLICATE_LABELS[l.type] || l.type}
                value={`${l.count} pair${l.count === 1 ? '' : 's'}`}
                icon={severityIcon(l.severity)}
                accent={SEVERITY_COLORS[l.severity] || '#fbbf24'}
                sub={`${Math.round(l.confidence || 0)}% confidence`}
              />
            ))}
          </div>
        </div>
      </div>
    </AnalyticsShell>
  )
}

function severityIcon(s) {
  return s === 'CRITICAL' ? '🚨' : s === 'ERROR' ? '⚠️' : '👀'
}
function color(i) {
  const palette = ['#fb923c', '#fbbf24', '#818cf8', '#38bdf8', '#f87171']
  return palette[i % palette.length]
}
