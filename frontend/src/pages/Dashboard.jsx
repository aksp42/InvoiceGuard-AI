import { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import KPI_Card from '../components/KPI_Card.jsx'
import InvoiceTable from '../components/InvoiceTable.jsx'

export default function Dashboard() {
  const [invoices, setInvoices] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .listInvoices()
      .then(setInvoices)
      .catch((e) => setError(e.message))
  }, [])

  const flagged = invoices.filter((i) => i.status !== 'Valid')
  const highRisk = invoices.filter((i) => i.status === 'High Risk')
  const dupes = invoices.filter((i) => i.status === 'Duplicate')

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>Dashboard</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16, marginBottom: 20 }}>
        <KPI_Card label="Total Invoices" value={invoices.length} accent="#2563eb" />
        <KPI_Card label="High Risk" value={highRisk.length} accent="#dc2626" />
        <KPI_Card label="Duplicates" value={dupes.length} accent="#6366f1" />
        <KPI_Card label="Flagged (₹)" value={"₹" + flagged.reduce((s, i) => s + (i.total_amount || 0), 0).toLocaleString('en-IN')} accent="#d97706" />
      </div>
      {error && <p style={{ color: '#b91c1c' }}>{error}</p>}
      <h2 style={{ marginBottom: 12, fontSize: 18 }}>Recent Invoices</h2>
      <InvoiceTable invoices={invoices} />
    </div>
  )
}