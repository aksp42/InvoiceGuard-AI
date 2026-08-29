// Phase 6 — Executive Overview (landing analytics page).
import AnalyticsShell, { LoadingGrid } from '../components/AnalyticsShell.jsx'
import AnimatedCounter from '../components/AnimatedCounter.jsx'
import ErrorBanner from '../components/ErrorBanner.jsx'
import {
  LineChart, BarChart, DonutChart, TrendCard, EmptyState,
} from '../components/charts.jsx'
import useAnalyticsData from '../lib/useAnalyticsData.js'
import {
  computeKpis, monthlySeries, amountSeries, statusDistribution, fmtINR, fmtInt,
} from '../lib/aggregations.js'

export default function ExecutiveOverview() {
  const { invoices, batches, pairs, loading, error, reload } = useAnalyticsData()

  if (loading) {
    return (
      <AnalyticsShell title="Executive Overview" subtitle="Company-wide invoice health at a glance.">
        <LoadingGrid />
      </AnalyticsShell>
    )
  }

  if (!invoices || invoices.length === 0) {
    return (
      <AnalyticsShell title="Executive Overview" subtitle="Company-wide invoice health at a glance.">
        <ErrorBanner message={error} onRetry={reload} />
        <div className="glass"><EmptyState title="No invoices yet" message="Upload and validate invoices to populate the executive overview with KPIs, trends and risk analytics." /></div>
      </AnalyticsShell>
    )
  }

  const k = computeKpis(invoices, batches, pairs)
  const countTrend = monthlySeries(invoices, { top: 10 })
  const amountTrend = amountSeries(invoices).slice(-10)
  const statusDist = statusDistribution(invoices)
  const validShare = k.totalInvoices ? Math.round((k.valid / k.totalInvoices) * 100) : 0
  const riskShare = k.totalInvoices ? Math.round((k.highRisk / k.totalInvoices) * 100) : 0
  const totalValue = invoices.reduce((s, i) => s + (Number(i.total_amount) || 0), 0)

  const kpis = [
    { label: 'Total Uploads', value: k.totalUploads, fmt: 'int', icon: '📤', accent: '#38bdf8', sub: `${k.processed} processed · ${k.failed} failed` },
    { label: 'Total Invoices', value: k.totalInvoices, fmt: 'int', icon: '🧾', accent: '#818cf8', sub: `${validShare}% valid` },
    { label: 'Valid', value: k.valid, fmt: 'int', icon: '✅', accent: '#34d399', sub: `${fmtINR(totalValue)} invoiced` },
    { label: 'High Risk', value: k.highRisk, fmt: 'int', icon: '⚠️', accent: '#f87171', sub: `${riskShare}% of total` },
    { label: 'Duplicates', value: k.duplicate, fmt: 'int', icon: '🔁', accent: '#fb923c', sub: 'across all batches' },
    { label: 'Potential Loss', value: k.potentialLoss, fmt: 'inr', icon: '💸', accent: '#fbbf24', sub: 'at-risk invoice value' },
  ]

  return (
    <AnalyticsShell title="Executive Overview" subtitle="Company-wide invoice health at a glance.">
      <ErrorBanner message={error} onRetry={reload} />

      <div className="kpi-grid">
        {kpis.map((kp) => (
          <div key={kp.label} className="glass kpi-card">
            <div className="ico" style={{ background: `${kp.accent}22`, color: kp.accent }}>{kp.icon}</div>
            <div className="k-label">{kp.label}</div>
            <div className="k-value" style={{ fontSize: 24 }}>
              <AnimatedCounter
                value={kp.value}
                format={(n) => (kp.fmt === 'inr' ? fmtINR(n) : fmtInt(n))}
              />
            </div>
            <div className="k-sub">{kp.sub}</div>
          </div>
        ))}
      </div>

      <div className="analytics-grid grid-2" style={{ marginBottom: 20 }}>
        <div className="glass">
          <div className="g-title">Invoice Volume Trend</div>
          {countTrend.length ? <BarChart data={countTrend} color="rgba(56,189,248,0.9)" /> : <EmptyState icon="📉" title="No trend" message="Volume over time appears after you upload invoices." />}
        </div>
        <div className="glass">
          <div className="g-title">Invoiced Value Trend (₹)</div>
          {amountTrend.length ? <AreaChart data={amountTrend} color="#818cf8" /> : <EmptyState icon="📈" title="No trend" />}
        </div>
      </div>

      <div className="analytics-grid grid-3">
        <div className="glass">
          <div className="g-title">Invoice Status Mix</div>
          <DonutChart data={statusDist} centerLabel="invoices" />
        </div>
        <div className="glass">
          <div className="g-title">Monthly Volume</div>
          {countTrend.length ? <LineChart data={countTrend} color="#fbbf24" /> : <EmptyState icon="📉" title="No data" />}
        </div>
        <div className="glass">
          <div className="g-title">Quick Insights</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <TrendCard label="Valid share" value={`${validShare}%`} icon="✅" accent="#34d399" sub="of invoices pass all rules" />
            <TrendCard label="High risk share" value={`${riskShare}%`} icon="⚠️" accent="#f87171" sub="needs immediate review" />
            <TrendCard label="Duplicate pairs" value={pairs.length} icon="🔁" accent="#fb923c" sub="flagged constraints" />
          </div>
        </div>
      </div>
    </AnalyticsShell>
  )
}
