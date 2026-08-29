import { apiUrl } from '../services/api.js'

const downloads = [
  { name: 'Validation report (CSV)', endpoint: '/report/csv' },
  { name: 'Validation report (Excel)', endpoint: '/report/excel' },
  { name: 'Validation report (PDF)', endpoint: '/report/pdf' },
]

export default function Reports() {
  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>Reports</h1>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Download the validation report from your latest upload.
      </p>
      <div className="card">
        {downloads.map((d) => (
          <div key={d.endpoint} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 0', borderBottom: '1px solid #f1f5f9' }}>
            <span>{d.name}</span>
            <a
              href={`${apiUrl}${d.endpoint}`}
              download
              style={{ color: '#2563eb', fontWeight: 600 }}
            >
              Download
            </a>
          </div>
        ))}
      </div>
    </div>
  )
}