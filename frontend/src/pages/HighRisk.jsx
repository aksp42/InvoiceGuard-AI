import { useEffect, useState } from 'react'
import { api } from '../services/api.js'
import InvoiceTable from '../components/InvoiceTable.jsx'

export default function HighRisk() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .listInvoices()
      .then((list) => setRows(list.filter((i) => i.status !== 'Valid')))
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>High Risk & Flagged Invoices</h1>
      {error && <p style={{ color: '#b91c1c' }}>{error}</p>}
      <InvoiceTable invoices={rows} />
    </div>
  )
}