import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../services/api.js'
import RiskBadge from '../components/RiskBadge.jsx'

export default function InvoiceDetails() {
  const { id } = useParams()
  const [inv, setInv] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .getInvoice(id)
      .then(setInv)
      .catch((e) => setError(e.message))
  }, [id])

  if (error) return <p style={{ color: '#b91c1c' }}>{error}</p>
  if (!inv) return <p>Loading…</p>

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>Invoice {inv.invoice_id}</h1>
      <div className="card" style={{ marginBottom: 20 }}>
        <Row k="Vendor" v={inv.vendor?.vendor_name} />
        <Row k="GST Number" v={inv.vendor?.gst_number} />
        <Row k="Date" v={inv.invoice_date} />
        <Row k="Total Amount" v={"₹" + (inv.total_amount ?? 0).toLocaleString('en-IN')} />
        <Row k="Risk Score" v={inv.risk_score} />
        <Row k="Status" v={<RiskBadge status={inv.status} />} />
      </div>
      <h2 style={{ marginBottom: 12, fontSize: 18 }}>Line Items</h2>
      <div className="card">
        <table>
          <thead>
            <tr><th>Product</th><th>Qty</th><th>Unit Price</th><th>Amount</th></tr>
          </thead>
          <tbody>
            {(inv.items || []).map((it, i) => (
              <tr key={i}>
                <td>{it.product_name}</td>
                <td>{it.quantity}</td>
                <td>₹{it.unit_price}</td>
                <td>₹{(it.quantity * it.unit_price).toLocaleString('en-IN')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const Row = ({ k, v }) => (
  <div style={{ display: 'flex', gap: 12, padding: '8px 0', borderBottom: '1px solid #f1f5f9' }}>
    <span style={{ width: 140, color: '#64748b' }}>{k}</span>
    <span>{v}</span>
  </div>
)