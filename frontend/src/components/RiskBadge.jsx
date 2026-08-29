export default function RiskBadge({ status }) {
  const colors = {
    Valid: { bg: '#dcfce7', fg: '#166534' },
    'Needs Review': { bg: '#fef9c3', fg: '#854d0e' },
    'High Risk': { bg: '#fee2e2', fg: '#991b1b' },
    Duplicate: { bg: '#e0e7ff', fg: '#3730a3' },
  }
  const c = colors[status] || { bg: '#e2e8f0', fg: '#0f172a' }
  return (
    <span
      style={{
        background: c.bg,
        color: c.fg,
        padding: '4px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
      }}
    >
      {status}
    </span>
  )
}