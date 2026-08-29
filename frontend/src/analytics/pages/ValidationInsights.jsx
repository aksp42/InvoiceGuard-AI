// Phase 6 — Validation Insights.
import AnalyticsShell, { LoadingGrid } from '../components/AnalyticsShell.jsx'
import AnimatedCounter from '../components/AnimatedCounter.jsx'
import ErrorBanner from '../components/ErrorBanner.jsx'
import { BarChart, DonutChart, AreaChart, TrendCard, EmptyState } from '../components/charts.jsx'
import useAnalyticsData from '../lib/useAnalyticsData.js'
import { statusDistribution, riskBuckets, monthlySeries, fmtINR, fmtInt } from '../lib/aggregations.js'

const VALID_COLOR = '#34d399'
const REVIEW_COLOR = '#fbbf24'
const HIGH_COLOR = '#f87171'
const CRITICAL_COLOR = '#ef4444'
const DUP_COLOR = '#818cf8'

export default function ValidationInsights() {
  const { invoices, batches, loading, error, reload } = useAnalyticsData()

  if (loading) {
    return (
      <AnalyticsShell title="Validation Insights" subtitle="Rule-engine outcomes, risk distribution and pass rates.">
        <LoadingGrid cards={4} charts={2} />
      </AnalyticsShell>
    )
  }

  if (!invoices || invoices.length === 0) {
    return (
      <AnalyticsShell title="Validation Insights" subtitle="Rule-engine outcomes, risk distribution and pass rates.">
        <ErrorBanner message={error} onRetry={reload} />
        <div className="glass"><EmptyState icon="✅" title="No validation data" message="Run the validation engine on an uploaded batch to see rule outcomes and risk buckets." /></div>
      </AnalyticsShell>
    )
  }

  const dist = statusDistribution(invoices)
  const buckets = riskBuckets(invoices)
  const volumeByMonth = monthlySeries(invoices, { top: 10 })
  const processed = batches.reduce((s, b) => s + Number(b.processed_invoices || 0), 0)
  const failed = batches.reduce((s, b) => s + Number(b.failed_invoices || 0), 0)
  const total = invoices.length
  const passRate = total ? Math.round(((dist.find((d) => d.label === 'Valid')?.value || 0) / total) * 100) : 0
  const atRisk = (dist.find((d) => d.label === 'High Risk')?.value || 0) + (dist.find((d) => d.label === 'Critical')?.value || 0)
  const flaggedAmount = invoices.reduce((s, i) => s + ((i.status !== 'Valid' && i.status !== 'Pending') ? (Number(i.total_amount) || 0) : 0), 0)

  const vkpis = [
    { label: 'Pass Rate', value: `${passRate}%`, icon: '🏅', accent: VALID_COLOR, sub: `of ${total} invoices valid` },
    { label: 'Needs Review', value: dist.find((d) => d.label === 'Needs Review')?.value || 0, icon: '🟡', accent: REVIEW_COLOR, sub: 'manual check advised' },
    { label: 'High Risk + Critical', value: atRisk, icon: '🚨', accent: HIGH_COLOR, sub: 'escalate immediately' },
    { label: 'Flagged Value', value: flaggedAmount, fmt: 'inr', icon: '💰', accent: CRITICAL_COLOR, sub: `${failed} failed rows` },
  ]

  const donut = [
    { label: 'Valid', value: dist.find((d) => d.label === 'Valid')?.value || 0, color: VALID_COLOR },
    { label: 'Needs Review', value: dist.find((d) => d.label === 'Needs Review')?.value || 0, color: REVIEW_COLOR },
    { label: 'High Risk', value: dist.find((d) => d.label === 'High Risk')?.value || 0, color: HIGH_COLOR },
    { label: 'Critical', value: dist.find((d) => d.label === 'Critical')?.value || 0, color: CRITICAL_COLOR },
    { label: 'Duplicate', value: dist.find((d) => d.label === 'Duplicate')?.value || 0, color: DUP_COLOR },
  ].filter((d) => d.value > 0)

  return (
    <AnalyticsShell title="Validation Insights" subtitle="Rule-engine outcomes, risk distribution and pass rates.">
      <ErrorBanner message={error} onRetry={reload} />

      <div className="kpi-grid">
        {vkpis.map((kp) => (
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

      <div className="analytics-grid grid-3" style={{ marginBottom: 20 }}>
        <div className="glass">
          <div className="g-title">Validation Outcome</div>
          <DonutChart data={donut} centerValue={total} centerLabel="total invoices" />
        </div>
        <div className="glass">
          <div className="g-title">Risk Score Buckets</div>
          {buckets.length ? <BarChart data={buckets.map((b) => ({ label: b.label, value: b.value, color: bucketColor(b.label) }))} valueColor="#cbd5e1" /> : <EmptyState icon="📊" />}
        </div>
        <div className="glass">
          <div className="g-title">Validation Volume Trend</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <TrendCard label="Invoices this period" value={total} icon="🧾" accent="#38bdf8" sub={`${processed} processed`} />
            <TrendCard label="Flagged rate" value={`${atRisk ? Math.round((atRisk / total) * 100) : 0}%`} icon="🚨" accent="#f87171" sub="high-risk + critical" />
            <TrendCard label="Processed in pipeline" value={processed} icon="⚙️" accent="#818cf8" sub={`${failed} failed`} />
          </div>
        </div>
      </div>

      <div className="analytics-grid grid-2">
        <div className="glass">
          <div className="g-title">Volume by Month</div>
          {volumeByMonth.length ? <AreaChart data={volumeByMonth} color="#38bdf8" /> : <EmptyState icon="📈" />}
        </div>
        <div className="glass">
          <div className="g-title">Full Status Breakdown</div>
          {dist.length ? (
            <table className="analytics-table">
              <thead><tr><th>Status</th><th>Invoices</th><th>Share</th></tr></thead>
              <tbody>
                {dist.map((d) => (
                  <tr key={d.label}>
                    <td><span className="badge" style={{ background: `${d.color}22`, color: d.color }}><span className="dot" />{d.label}</span></td>
                    <td style={{ fontWeight: 700 }}>{fmtInt(d.value)}</td>
                    <td style={{ width: '40%' }}><div className="progress-bar"><div style={{ width: `${(d.value / total) * 100}%`, background: d.color }} /></div></td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <EmptyState icon="✅" />}
        </div>
      </div>
    </AnalyticsShell>
  )
}

function bucketColor(label) {
  const lo = parseInt(label.split('–')[0], 10)
  if (lo >= 75) return HIGH_COLOR
  if (lo >= 50) return CRITICAL_COLOR
  if (lo >= 25) return REVIEW_COLOR
  return VALID_COLOR
}
