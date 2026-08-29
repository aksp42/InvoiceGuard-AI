// Phase 6.1 — Reusable error banner with retry for dashboard resilience.
export default function ErrorBanner({ message, onRetry }) {
  if (!message) return null
  return (
    <div
      className="glass"
      style={{
        marginBottom: 20,
        color: '#f87171',
        borderColor: 'rgba(248,113,113,.4)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: 16,
        flexWrap: 'wrap',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontSize: 18 }}>⚠️</span>
        <span style={{ fontSize: 13.5 }}>{message}</span>
      </div>
      {typeof onRetry === 'function' && (
        <button
          onClick={onRetry}
          style={{
            background: 'linear-gradient(135deg, #38bdf8, #818cf8)',
            color: '#04101f',
            border: 'none',
            borderRadius: 10,
            padding: '8px 16px',
            fontWeight: 700,
            fontSize: 13,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          ↻ Retry
        </button>
      )}
    </div>
  )
}
