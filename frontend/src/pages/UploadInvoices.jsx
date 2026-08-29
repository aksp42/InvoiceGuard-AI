import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api.js'

const MODES = [
  { key: 'single', label: 'Single Invoice', hint: 'One invoice per file (may include multiple line items)' },
  { key: 'bulk',   label: 'Bulk File',     hint: 'Many invoices in one CSV / Excel file' },
]

const STATUS_COLORS = {
  Completed: '#15803d',
  Processing: '#b45309',
  Failed: '#b91c1c',
}

export default function UploadInvoices() {
  const inputRef = useRef(null)
  const navigate = useNavigate()
  const [mode, setMode] = useState('bulk')
  const [file, setFile] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [history, setHistory] = useState([])
  const [validating, setValidating] = useState(false)
  const [validation, setValidation] = useState(null)
  const [validationError, setValidationError] = useState('')
  const [scanning, setScanning] = useState(false)
  const [duplicates, setDuplicates] = useState(null)
  const [duplicateError, setDuplicateError] = useState('')

  const loadHistory = () => {
    api.uploadHistory().then(setHistory).catch(() => setHistory([]))
  }

  useEffect(() => { loadHistory() }, [])

  const runValidation = async (batchId) => {
    setValidating(true)
    setValidationError('')
    setValidation(null)
    try {
      const v = await api.validateBatch(batchId)
      setValidation(v)
    } catch (e) {
      setValidationError(e.message)
    } finally {
      setValidating(false)
    }
  }

  const runDuplicates = async (batchId) => {
    setScanning(true)
    setDuplicateError('')
    setDuplicates(null)
    try {
      const d = await api.scanDuplicates(batchId)
      setDuplicates(d)
    } catch (e) {
      setDuplicateError(e.message)
    } finally {
      setScanning(false)
    }
  }

  const upload = async (selected) => {
    if (!selected) return
    setFile(selected)
    setError('')
    setResult(null)
    setValidation(null)
    setValidationError('')
    setDuplicates(null)
    setDuplicateError('')
    setProgress(0)
    setUploading(true)
    try {
      const summary = mode === 'single'
        ? await api.uploadSingle(selected, setProgress)
        : await api.uploadBulk(selected, setProgress)
      setResult(summary)
      setProgress(100)
      loadHistory()
      await runValidation(summary.batch_id)
      await runDuplicates(summary.batch_id)
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragActive(false)
    upload(e.dataTransfer.files[0])
  }

  const handleInput = (e) => upload(e.target.files[0])

  const statusStyle = (status) => ({ color: STATUS_COLORS[status] || '#334155', fontWeight: 600 })

  return (
    <div style={{ maxWidth: 860, margin: '0 auto' }}>
      <h1 style={{ marginBottom: 20 }}>Upload Invoices</h1>

      {/* Mode toggle */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        {MODES.map((m) => (
          <button
            key={m.key}
            onClick={() => setMode(m.key)}
            style={{
              flex: 1,
              padding: '12px 16px',
              borderRadius: 8,
              border: mode === m.key ? '2px solid #2563eb' : '2px solid #e2e8f0',
              background: mode === m.key ? '#eff6ff' : '#ffffff',
              cursor: 'pointer',
              textAlign: 'left',
            }}
          >
            <div style={{ fontWeight: 700, color: '#0f172a' }}>{m.label}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{m.hint}</div>
          </button>
        ))}
      </div>

      {/* Drop zone / choose file */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        style={{
          border: dragActive ? '2px dashed #2563eb' : '2px dashed #cbd5e1',
          background: dragActive ? '#eff6ff' : '#ffffff',
          borderRadius: 12,
          padding: 40,
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'border-color .15s, background .15s',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.xlsx"
          hidden
          onChange={handleInput}
        />
        <div style={{ fontSize: 40 }}>{uploading ? '⏳' : '📄'}</div>
        <h3 style={{ margin: '12px 0 4px', color: '#0f172a' }}>
          {uploading
            ? `Uploading ${file?.name ?? ''}…`
            : 'Drag & drop a CSV / Excel file here, or click to choose'}
        </h3>
        <p style={{ color: '#64748b', fontSize: 13 }}>
          Supported: .csv, .xlsx — required columns: invoice_number, vendor_name, invoice_date,
          product_name, quantity, unit_price, gst_percent
        </p>
      </div>

      {/* Upload progress */}
      {(uploading || (result && progress === 100)) && (
        <div className="card" style={{ marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontWeight: 600, color: '#0f172a' }}>{file?.name}</span>
            <span style={{ color: '#2563eb', fontWeight: 600 }}>{progress}%</span>
          </div>
          <div style={{ background: '#e2e8f0', borderRadius: 999, height: 10, overflow: 'hidden' }}>
            <div
              style={{
                height: '100%',
                width: `${progress}%`,
                background: '#2563eb',
                transition: 'width .2s',
                borderRadius: 999,
              }}
            />
          </div>
        </div>
      )}

      {/* Success card */}
      {result && (
        <div className="card" style={{ marginTop: 16, borderLeft: '4px solid #15803d' }}>
          <h2 style={{ fontSize: 16, color: '#15803d', marginBottom: 12 }}>Upload complete</h2>
          <table style={{ width: '100%' }}>
            <tbody>
              <tr><td style={{ color: '#64748b', padding: '6px 0' }}>Batch ID</td><td style={{ textAlign: 'right', fontWeight: 600 }}>#{result.batch_id}</td></tr>
              <tr><td style={{ color: '#64748b', padding: '6px 0' }}>File</td><td style={{ textAlign: 'right' }}>{result.file_name}</td></tr>
              <tr><td style={{ color: '#64748b', padding: '6px 0' }}>Total invoices</td><td style={{ textAlign: 'right', fontWeight: 600 }}>{result.total}</td></tr>
              <tr><td style={{ color: '#15803d', padding: '6px 0' }}>Processed</td><td style={{ textAlign: 'right', fontWeight: 600 }}>{result.processed}</td></tr>
              <tr><td style={{ color: '#b91c1c', padding: '6px 0' }}>Failed</td><td style={{ textAlign: 'right', fontWeight: 600 }}>{result.failed}</td></tr>
              <tr><td style={{ color: '#64748b', padding: '6px 0' }}>Status</td><td style={{ textAlign: 'right', fontWeight: 600 }}>{result.status}</td></tr>
            </tbody>
          </table>
        </div>
      )}

      {/* Validation summary card */}
      {validating && (
        <div className="card" style={{ marginTop: 16 }}>
          <p style={{ margin: 0, color: '#2563eb', fontWeight: 600 }}>Running validation…</p>
        </div>
      )}

      {validation && (
        <div className="card" style={{ marginTop: 16, borderLeft: '4px solid #6366f1' }}>
          <h2 style={{ fontSize: 16, color: '#4338ca', marginBottom: 12 }}>Validation Summary</h2>
          <table style={{ width: '100%' }}>
            <tbody>
              <tr><td style={{ color: '#64748b', padding: '6px 0' }}>Invoices Checked</td><td style={{ textAlign: 'right', fontWeight: 700 }}>{validation.total_invoices}</td></tr>
              <tr><td style={{ color: '#15803d', padding: '6px 0' }}>Valid</td><td style={{ textAlign: 'right', fontWeight: 600, color: '#15803d' }}>{validation.valid}</td></tr>
              <tr><td style={{ color: '#d97706', padding: '6px 0' }}>Needs Review</td><td style={{ textAlign: 'right', fontWeight: 600, color: '#d97706' }}>{validation.needs_review}</td></tr>
              <tr><td style={{ color: '#dc2626', padding: '6px 0' }}>High Risk</td><td style={{ textAlign: 'right', fontWeight: 600, color: '#dc2626' }}>{validation.high_risk}</td></tr>
              <tr><td style={{ color: '#7f1d1d', padding: '6px 0' }}>Critical</td><td style={{ textAlign: 'right', fontWeight: 600, color: '#7f1d1d' }}>{validation.critical}</td></tr>
            </tbody>
          </table>
          <button
            onClick={() => navigate('/high-risk')}
            style={{
              marginTop: 14,
              padding: '10px 16px',
              border: 'none',
              borderRadius: 8,
              background: '#2563eb',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            View Validation Report
          </button>
        </div>
      )}

      {validationError && (
        <div className="card" style={{ marginTop: 16, borderLeft: '4px solid #d97706' }}>
          <p style={{ color: '#d97706', margin: 0 }}>
            Validation could not be completed on the server: {validationError}
          </p>
        </div>
      )}

      {/* Duplicate detection card */}
      {scanning && (
        <div className="card" style={{ marginTop: 16 }}>
          <p style={{ margin: 0, color: '#2563eb', fontWeight: 600 }}>Scanning for duplicates…</p>
        </div>
      )}

      {duplicates && (
        <div className="card" style={{ marginTop: 16, borderLeft: '4px solid #dc2626' }}>
          <h2 style={{ fontSize: 16, color: '#991b1b', marginBottom: 12 }}>Duplicate Detection</h2>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ flex: 1, minWidth: 150, background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 10, padding: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#b91c1c' }}>{duplicates.exact_duplicates}</div>
              <div style={{ fontSize: 13, color: '#b91c1c', fontWeight: 600 }}>Exact</div>
            </div>
            <div style={{ flex: 1, minWidth: 150, background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: 10, padding: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#c2410c' }}>{duplicates.near_duplicates}</div>
              <div style={{ fontSize: 13, color: '#c2410c', fontWeight: 600 }}>Near</div>
            </div>
            <div style={{ flex: 1, minWidth: 150, background: '#fefce8', border: '1px solid #fde68a', borderRadius: 10, padding: 12 }}>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#a16207' }}>
                {(duplicates.vendor_duplicates || 0) + (duplicates.suspicious_duplicates || 0)}
              </div>
              <div style={{ fontSize: 13, color: '#a16207', fontWeight: 600 }}>Suspicious</div>
            </div>
          </div>
          <button
            onClick={() => navigate('/duplicates')}
            style={{
              marginTop: 14,
              padding: '10px 16px',
              border: 'none',
              borderRadius: 8,
              background: '#dc2626',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            View All Duplicates
          </button>
        </div>
      )}

      {duplicateError && (
        <div className="card" style={{ marginTop: 16, borderLeft: '4px solid #d97706' }}>
          <p style={{ color: '#d97706', margin: 0 }}>
            Duplicate detection could not be completed on the server: {duplicateError}
          </p>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="card" style={{ marginTop: 16, borderLeft: '4px solid #b91c1c' }}>
          <p style={{ color: '#b91c1c', margin: 0 }}>{error}</p>
        </div>
      )}

      {/* Recent upload history */}
      <div style={{ marginTop: 28 }}>
        <h2 style={{ fontSize: 16, marginBottom: 12 }}>Recent Upload History</h2>
        {history.length === 0 ? (
          <p style={{ color: '#64748b' }}>No uploads yet.</p>
        ) : (
          <table className="card" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ textAlign: 'left', color: '#475569', fontSize: 13 }}>
                <th style={{ padding: '8px 10px' }}>Batch</th>
                <th style={{ padding: '8px 10px' }}>File</th>
                <th style={{ padding: '8px 10px' }}>Uploaded by</th>
                <th style={{ padding: '8px 10px' }}>When</th>
                <th style={{ padding: '8px 10px' }}>Total</th>
                <th style={{ padding: '8px 10px' }}>Processed</th>
                <th style={{ padding: '8px 10px' }}>Failed</th>
                <th style={{ padding: '8px 10px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {history.map((b) => (
                <tr key={b.batch_id} style={{ borderTop: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '8px 10px' }}>#{b.batch_id}</td>
                  <td style={{ padding: '8px 10px' }}>{b.file_name}</td>
                  <td style={{ padding: '8px 10px' }}>{b.uploaded_by}</td>
                  <td style={{ padding: '8px 10px', color: '#64748b' }}>
                    {b.uploaded_at ? new Date(b.uploaded_at).toLocaleString() : '—'}
                  </td>
                  <td style={{ padding: '8px 10px' }}>{b.total_invoices}</td>
                  <td style={{ padding: '8px 10px' }}>{b.processed_invoices}</td>
                  <td style={{ padding: '8px 10px' }}>{b.failed_invoices}</td>
                  <td style={{ padding: '8px 10px', ...statusStyle(b.status) }}>{b.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}