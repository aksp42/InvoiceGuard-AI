// Phase 6 — Audit Center.
// Renders a data-driven audit trail from upload batches (uploaded_by,
// timestamp, processed/failed counts, status) plus invoice/duplicate signal.
import AnalyticsShell, { LoadingGrid } from '../components/AnalyticsShell.jsx'
import AnimatedCounter from '../components/AnimatedCounter.jsx'
import ErrorBanner from '../components/ErrorBanner.jsx'
import { DonutChart, EmptyState } from '../components/charts.jsx'
import useAnalyticsData from '../lib/useAnalyticsData.js'
import { fmtInt } from '../lib/aggregations.js'

export default function AuditCenter() {
  const { batches, invoices, pairs, loading, error, reload } = useAnalyticsData()

  if (loading) {
    return (
      <AnalyticsShell title="Audit Center" subtitle="Immutable record of every upload and validation action.">
        <LoadingGrid cards={4} charts={0} />
      </AnalyticsShell>
    )
  }

  if (!batches || batches.length === 0) {
    return (
      <AnalyticsShell title="Audit Center" subtitle="Immutable record of every upload and validation action.">
        <ErrorBanner message={error} onRetry={reload} />
        <div className="glass">
          <EmptyState icon="🛡️" title="No audit events yet" message="Each upload and validation action is recorded here, forming an auditable trail for compliance and reconciliation." />
        </div>
      </AnalyticsShell>
    )
  }

  const total = batches.length
  const completed = batches.filter((b) => b.status === 'Completed').length
  const failed = batches.filter((b) => b.status === 'Failed').length
  const processing = batches.filter((b) => b.status === 'Processing').length
  const totalProcessed = batches.reduce((s, b) => s + Number(b.processed_invoices || 0), 0)
  const totalFailed = batches.reduce((s, b) => s + Number(b.failed_invoices || 0), 0)

  const statusDonut = [
    { label: 'Completed', value: completed, color: '#34d399' },
    { label: 'Processing', value: processing, color: '#38bdf8' },
    { label: 'Failed', value: failed, color: '#f87171' },
  ].filter((d) => d.value > 0)

  const aKpis = [
    { label: 'Upload Events', value: total, icon: '📤', accent: '#38bdf8', sub: 'total batch records' },
    { label: 'Completed', value: completed, icon: '✅', accent: '#34d399', sub: `${fmtInt(totalProcessed)} invoices` },
    { label: 'Failed', value: failed, icon: '⛔', accent: '#f87171', sub: `${fmtInt(totalFailed)} failed rows` },
    { label: 'In Process', value: processing, icon: '⏳', accent: '#fbbf24', sub: 'from totals' },
  ]

  return (
    <AnalyticsShell title="Audit Center" subtitle="Immutable record of every upload and validation action.">
      <ErrorBanner message={error} onRetry={reload} />

      <div className="kpi-grid">
        {aKpis.map((kp) => (
          <div key={kp.label} className="glass kpi-card">
            <div className="ico" style={{ background: `${kp.accent}22`, color: kp.accent }}>{kp.icon}</div>
            <div className="k-label">{kp.label}</div>
            <div className="k-value" style={{ fontSize: 24 }}><AnimatedCounter value={kp.value} format={fmtInt} /></div>
            <div className="k-sub">{kp.sub}</div>
          </div>
        ))}
      </div>

      <div className="analytics-grid grid-3" style={{ marginBottom: 20 }}>
        <div className="glass">
          <div className="g-title">Batch Health</div>
          <DonutChart data={statusDonut} centerValue={total} centerLabel="batches" />
        </div>
        <div className="glass" style={{ gridColumn: 'span 2' }}>
          <div className="g-title">Recent Activity Timeline</div>
          <div style={{ maxHeight: 400, overflowY: 'auto' }}>
            {batches.map((b) => (
              <AuditRow key={b.batch_id} b={b} invoices={invoices} />
            ))}
          </div>
        </div>
      </div>

      <div className="analytics-grid grid-4">
        <div className="glass">
          <div className="g-title">Invoices Tracked</div>
          <div className="g-value" style={{ color: '#38bdf8' }}>{fmtInt((invoices || []).length)}</div>
          <div className="g-label">in database</div>
        </div>
        <div className="glass">
          <div className="g-title">Duplicate Pairs</div>
          <div className="g-value" style={{ color: '#fb923c' }}>{fmtInt((pairs || []).length)}</div>
          <div className="g-label">flagged</div>
        </div>
        <div className="glass">
          <div className="g-title">Data Sources</div>
          <div className="g-value" style={{ color: '#818cf8' }}>{fmtInt(total)}</div>
          <div className="g-label">upload files</div>
        </div>
        <div className="glass">
          <div className="g-title">Operator</div>
          <div className="g-value" style={{ fontSize: 20, color: '#f1f5f9' }}>
            {batches[0]?.uploaded_by || 'admin'}
          </div>
          <div className="g-label">latest actor</div>
        </div>
      </div>
    </AnalyticsShell>
  )
}

function AuditRow({ b, invoices }) {
  const isFailed = b.status === 'Failed'
  const accent = isFailed ? '#f87171' : b.status === 'Processing' ? '#fbbf24' : '#34d399'
  const icon = isFailed ? '⛔' : b.status === 'Processing' ? '⏳' : '✅'
  const stamp = b.uploaded_at ? new Date(b.uploaded_at).toLocaleString('en-IN') : '—'
  const batchInvoices = (b.total_invoices || 0) + (b.failed_invoices || 0)
  return (
    <div style={{ display: 'flex', gap: 14, padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.06)', alignItems: 'flex-start' }}>
      <div style={{ width: 38, height: 38, borderRadius: 10, background: `${accent}22`, color: accent, display: 'grid', placeItems: 'center', fontSize: 18, flexShrink: 0 }}>{icon}</div>
      <div style={{ flex: 1 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 700 }}>Batch #{b.batch_id} · {b.file_name}</span>
          <span className="badge" style={{ background: `${accent}1f`, color: accent }}><span className="dot" />{b.status}</span>
        </div>
        <div style={{ color: '#9fb0c3', fontSize: 12, marginTop: 2 }}>{stamp}</div>
        <div style={{ color: '#6b7f96', fontSize: 12, marginTop: 4 }}>
          {fmtInt(b.processed_invoices || 0)} processed · {fmtInt(b.failed_invoices || 0)} failed of {fmtInt(b.total_invoices || 0)} total
          {!isFailed && batchInvoices > 0 && ' · audit-logged'}
        </div>
      </div>
    </div>
  )
}
