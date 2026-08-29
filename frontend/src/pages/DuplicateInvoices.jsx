import { useEffect, useState } from 'react'
import { api } from '../services/api.js'

const TYPE_LABELS = {
  DUPLICATE_EXACT: 'Exact',
  DUPLICATE_VENDOR: 'Vendor',
  DUPLICATE_NEAR: 'Near',
  DUPLICATE_DATE: 'Amount + Date',
  DUPLICATE_ITEM: 'Item-Level',
}

const SEVERITY_COLORS = {
  CRITICAL: { bg: '#fef2f2', border: '#fecaca', text: '#b91c1c' },
  ERROR:    { bg: '#fff7ed', border: '#fed7aa', text: '#c2410c' },
  WARNING:  { bg: '#fefce8', border: '#fde68a', text: '#a16207' },
}

export default function DuplicateInvoices() {
  const [pairs, setPairs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    api.listDuplicates()
      .then(setPairs)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const countByType = (types) =>
    pairs.filter((p) => types.includes(p.validation_type)).length

  const badges = [
    { label: 'Exact', count: countByType(['DUPLICATE_EXACT']), color: SEVERITY_COLORS.CRITICAL },
    { label: 'Near', count: countByType(['DUPLICATE_NEAR']), color: SEVERITY_COLORS.ERROR },
    {
      label: 'Suspicious',
      count: countByType(['DUPLICATE_VENDOR', 'DUPLICATE_DATE', 'DUPLICATE_ITEM']),
      color: SEVERITY_COLORS.WARNING,
    },
  ]

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 20 }}>Duplicate Detection</h1>

      {error && (
        <div className="card" style={{ marginBottom: 16, borderLeft: '4px solid #b91c1c' }}>
          <p style={{ color: '#b91c1c', margin: 0 }}>{error}</p>
        </div>
      )}

      {loading ? (
        <p style={{ color: '#64748b' }}>Loading duplicates…</p>
      ) : pairs.length === 0 ? (
        <div className="card">
          <p style={{ margin: 0, color: '#64748b' }}>No duplicates detected yet.</p>
        </div>
      ) : (
        <>
          <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
            {badges.map((b) => (
              <div
                key={b.label}
                style={{
                  flex: 1,
                  minWidth: 160,
                  background: b.color.bg,
                  border: `1px solid ${b.color.border}`,
                  borderRadius: 10,
                  padding: 14,
                }}
              >
                <div style={{ fontSize: 26, fontWeight: 800, color: b.color.text }}>{b.count}</div>
                <div style={{ fontSize: 13, color: b.color.text, fontWeight: 600 }}>{b.label}</div>
              </div>
            ))}
          </div>

          <table className="card" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#475569', fontSize: 13 }}>
                <th style={{ padding: '8px 10px' }}>Invoice A</th>
                <th style={{ padding: '8px 10px' }}>Invoice B</th>
                <th style={{ padding: '8px 10px' }}>Vendor</th>
                <th style={{ padding: '8px 10px' }}>Amount</th>
                <th style={{ padding: '8px 10px' }}>Type</th>
                <th style={{ padding: '8px 10px' }}>Confidence</th>
                <th style={{ padding: '8px 10px' }}>Similarity</th>
              </tr>
            </thead>
            <tbody>
              {pairs.map((p) => {
                const color = SEVERITY_COLORS[p.severity] || SEVERITY_COLORS.WARNING
                return (
                  <tr key={`${p.validation_type}-${p.invoice_a_id}-${p.invoice_b_id}`} style={{ borderTop: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '8px 10px' }}>
                      <div style={{ fontWeight: 600 }}>#{p.invoice_a_id}</div>
                      <div style={{ color: '#64748b', fontSize: 12 }}>{p.invoice_a_number || '—'}</div>
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <div style={{ fontWeight: 600 }}>#{p.invoice_b_id}</div>
                      <div style={{ color: '#64748b', fontSize: 12 }}>{p.invoice_b_number || '—'}</div>
                    </td>
                    <td style={{ padding: '8px 10px' }}>{p.vendor_name || '—'}</td>
                    <td style={{ padding: '8px 10px' }}>
                      <div>{p.amount_a != null ? `₹${Number(p.amount_a).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'}</div>
                      <div style={{ color: '#64748b', fontSize: 12 }}>{p.amount_b != null ? `₹${Number(p.amount_b).toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '—'}</div>
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '3px 10px',
                          borderRadius: 999,
                          fontSize: 12,
                          fontWeight: 700,
                          background: color.bg,
                          color: color.text,
                          border: `1px solid ${color.border}`,
                        }}
                      >
                        {TYPE_LABELS[p.validation_type] || p.validation_type}
                      </span>
                    </td>
                    <td style={{ padding: '8px 10px' }}>
                      <span style={{ fontWeight: 700, color: color.text }}>
                        {p.confidence_score != null ? `${Number(p.confidence_score).toFixed(0)}%` : '—'}
                      </span>
                    </td>
                    <td style={{ padding: '8px 10px', color: '#334155' }}>
                      {p.similarity != null ? `${Number(p.similarity).toFixed(1)}%` : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </>
      )}
    </div>
  )
}