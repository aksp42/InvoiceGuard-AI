import { useState } from 'react'
import { api } from '../services/api.js'

export default function Settings() {
  const [health, setHealth] = useState(null)

  const check = async () => {
    try {
      const h = await api.health()
      setHealth(`Backend reachable: ${h.status}`)
    } catch {
      setHealth('Backend not reachable')
    }
  }

  return (
    <div>
      <h1 style={{ marginBottom: 20 }}>Settings</h1>
      <div className="card" style={{ maxWidth: 480 }}>
        <h3 style={{ marginBottom: 12 }}>API Status</h3>
        <button
          onClick={check}
          style={{ padding: '8px 16px', borderRadius: 8, border: 0, background: '#2563eb', color: '#fff' }}
        >
          Check backend health
        </button>
        {health && <p style={{ marginTop: 12, color: '#475569' }}>{health}</p>}
      </div>
    </div>
  )
}