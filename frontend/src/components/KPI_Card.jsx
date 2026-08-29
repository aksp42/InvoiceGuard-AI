export default function KPI_Card({ label, value, accent = '#2563eb' }) {
  return (
    <div
      className="card"
      style={{ borderTop: `4px solid ${accent}`, textAlign: 'center' }}
    >
      <div style={{ color: '#64748b', fontSize: 14 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, marginTop: 8 }}>{value}</div>
    </div>
  )
}