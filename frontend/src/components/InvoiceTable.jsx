import { useNavigate } from 'react-router-dom'
import RiskBadge from './RiskBadge.jsx'

export default function InvoiceTable({ invoices }) {
  const navigate = useNavigate()
  return (
    <div className="card" style={{ overflowX: 'auto' }}>
      <table>
        <thead>
          <tr>
            <th>Invoice ID</th>
            <th>Vendor</th>
            <th>Total</th>
            <th>Status</th>
            <th>Risk</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {invoices.map((inv) => (
            <tr key={inv.invoice_id}>
              <td>{inv.invoice_id}</td>
              <td>{inv.vendor_name}</td>
              <td>₹{Number(inv.total_amount || 0).toLocaleString('en-IN')}</td>
              <td>
                <RiskBadge status={inv.status} />
              </td>
              <td>{inv.risk_score}</td>
              <td>
                <button onClick={() => navigate(`/invoices/${inv.invoice_id}`)}>
                  Details
                </button>
              </td>
            </tr>
          ))}
          {invoices.length === 0 && (
            <tr>
              <td colSpan={6} style={{ textAlign: 'center', color: '#64748b' }}>
                No invoices found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}