// Phase 6 — Vendor Intelligence.
import AnalyticsShell, { LoadingGrid } from '../components/AnalyticsShell.jsx'
import AnimatedCounter from '../components/AnimatedCounter.jsx'
import ErrorBanner from '../components/ErrorBanner.jsx'
import { BarChart, DonutChart, Heatmap, TrendCard, EmptyState } from '../components/charts.jsx'
import useAnalyticsData from '../lib/useAnalyticsData.js'
import { vendorIntelligence, fmtINR, fmtInt } from '../lib/aggregations.js'

const heatOf = (value, max) => (max ? Math.round((value / max) * 100) : 0)

export default function VendorIntelligence() {
  const { invoices, loading, error, reload } = useAnalyticsData()

  if (loading) {
    return (
      <AnalyticsShell title="Vendor Intelligence" subtitle="Who drives value — and who drives risk.">
        <LoadingGrid cards={4} charts={2} />
      </AnalyticsShell>
    )
  }

  if (!invoices || invoices.length === 0) {
    return (
      <AnalyticsShell title="Vendor Intelligence" subtitle="Who drives value — and who drives risk.">
        <ErrorBanner message={error} onRetry={reload} />
        <div className="glass"><EmptyState icon="🏢" title="No vendor activity" message="Vendor breakdowns appear once invoices reference vendors." /></div>
      </AnalyticsShell>
    )
  }

  const vendors = vendorIntelligence(invoices)
  const topValue = vendors.slice(0, 8)
  const totalAmount = vendors.reduce((s, v) => s + v.amount, 0)
  const totalHighRisk = vendors.reduce((s, v) => s + v.highRisk, 0)
  const riskyVendors = vendors.filter((v) => v.highRisk > 0).length
  const maxAmount = Math.max(1, ...vendors.map((v) => v.amount))
  const maxCount = Math.max(1, ...vendors.map((v) => v.count))

  const vKpis = [
    { label: 'Active Vendors', value: vendors.length, icon: '🏢', accent: '#38bdf8', sub: `${totalHighRisk} with high-risk invoices` },
    { label: 'Total Spend', value: totalAmount, fmt: 'inr', icon: '💳', accent: '#818cf8', sub: 'across all vendors' },
    { label: 'Risky Vendors', value: riskyVendors, icon: '⚠️', accent: '#f87171', sub: 'flagged at least once' },
    { label: 'Avg / Vendor', value: vendors.length ? Math.round(totalAmount / vendors.length) : 0, fmt: 'inr', icon: '⚖️', accent: '#fbbf24', sub: 'mean invoiced value' },
  ]

  return (
    <AnalyticsShell title="Vendor Intelligence" subtitle="Who drives value — and who drives risk.">
      <ErrorBanner message={error} onRetry={reload} />

      <div className="kpi-grid">
        {vKpis.map((kp) => (
          <div key={kp.label} className="glass kpi-card">
            <div className="ico" style={{ background: `${kp.accent}22`, color: kp.accent }}>{kp.icon}</div>
            <div className="k-label">{kp.label}</div>
            <div className="k-value" style={{ fontSize: 24 }}>
              <AnimatedCounter value={Number(kp.value) || 0} format={(n) => (kp.fmt === 'inr' ? fmtINR(n) : fmtInt(n))} />
            </div>
            <div className="k-sub">{kp.sub}</div>
          </div>
        ))}
      </div>

      <div className="analytics-grid grid-2" style={{ marginBottom: 20 }}>
        <div className="glass">
          <div className="g-title">Spend by Vendor (₹)</div>
          {topValue.length ? <BarChart data={topValue.map((v) => ({ label: short(v.name), value: v.amount }))} color="rgba(56,189,248,0.9)" /> : <EmptyState icon="📊" />}
        </div>
        <div className="glass">
          <div className="g-title">Share of Spend</div>
          <DonutChart
            data={vendors.slice(0, 7).map((v, i) => ({ label: short(v.name), value: Math.round((v.amount / (totalAmount || 1)) * 100), color: color(i) }))}
            centerLabel="% of spend"
          />
        </div>
      </div>

      <div className="analytics-grid grid-2">
        <div className="glass">
          <div className="g-title">Vendor × Risk Heatmap</div>
          <p style={{ color: '#6b7f96', fontSize: 12, marginBottom: 10 }}>Rows = vendors · cols = invoices · intensity = risk score</p>
          {vendors.length ? (
            <Heatmap
              rows={vendors.slice(0, 8).map((v) => short(v.name))}
              columns={['Invoices', 'High Risk', 'Spend ₹k']}
              cells={vendors.slice(0, 8).map((v) => [
                { value: heatOf(v.count, maxCount) },
                { value: heatOf(v.highRisk, Math.max(1, ...vendors.map((x) => x.highRisk))) },
                { value: heatOf(v.amount, maxAmount) },
              ])}
            />
          ) : <EmptyState icon="▦" />}
        </div>
        <div className="glass">
          <div className="g-title">Vendor Rankings</div>
          {vendors.length ? (
            <table className="analytics-table">
              <thead><tr><th>Vendor</th><th>Invoices</th><th>High Risk</th><th>Spend</th></tr></thead>
              <tbody>
                {vendors.slice(0, 10).map((v) => (
                  <tr key={v.name}>
                    <td style={{ fontWeight: 600 }}>{v.name}</td>
                    <td>{fmtInt(v.count)}</td>
                    <td>{v.highRisk ? <span className="badge" style={{ background: 'rgba(248,113,113,.15)', color: '#f87171' }}><span className="dot" />{v.highRisk}</span> : <span style={{ color: '#34d399' }}>0</span>}</td>
                    <td>{fmtINR(v.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : <EmptyState icon="🏢" />}
        </div>
      </div>
    </AnalyticsShell>
  )
}

function short(name) {
  if (!name) return 'Unknown'
  return name.length > 16 ? name.slice(0, 15) + '…' : name
}
function color(i) {
  const palette = ['#38bdf8', '#818cf8', '#34d399', '#fbbf24', '#f87171', '#fb923c', '#e879f9']
  return palette[i % palette.length]
}
