import { useRef, useState } from 'react'

export default function UploadBox({ onUploaded }) {
  const inputRef = useRef(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')

  const handleFile = async (file) => {
    if (!file) return
    setUploading(true)
    setError('')
    try {
      const summary = await onUploaded(file)
      setUploading(false)
      return summary
    } catch (e) {
      setError(e.message)
      setUploading(false)
    }
  }

  return (
    <div
      className="card"
      style={{
        border: '2px dashed #cbd5e1',
        textAlign: 'center',
        padding: 48,
        cursor: 'pointer',
      }}
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => e.preventDefault()}
      onDrop={(e) => {
        e.preventDefault()
        handleFile(e.dataTransfer.files[0])
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        hidden
        onChange={(e) => handleFile(e.target.files[0])}
      />
      <div style={{ fontSize: 40 }}>⬆️</div>
      <h3 style={{ margin: '12px 0 4px' }}>
        {uploading ? 'Uploading…' : 'Drop a CSV / Excel file here or click to browse'}
      </h3>
      <p style={{ color: '#64748b' }}>
        Required columns: invoice_id, vendor_name, quantity, unit_price, total_amount
      </p>
      {error && <p style={{ color: '#b91c1c', marginTop: 12 }}>{error}</p>}
    </div>
  )
}