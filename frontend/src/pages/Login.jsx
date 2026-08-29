import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../services/api.js'

export default function Login() {
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    try {
      const { access_token } = await api.login(username, password)
      localStorage.setItem('token', access_token)
      navigate('/')
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        background: '#0f172a',
      }}
    >
      <form
        onSubmit={submit}
        className="card"
        style={{ width: 360, padding: 32 }}
      >
        <h2 style={{ marginBottom: 4 }}>Invoice Error Detector</h2>
        <p style={{ color: '#64748b', marginBottom: 20 }}>Sign in to continue</p>
        <label style={label}>Username</label>
        <input style={input} value={username} onChange={(e) => setUsername(e.target.value)} />
        <label style={label}>Password</label>
        <input
          style={input}
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p style={{ color: '#b91c1c', marginTop: 8 }}>{error}</p>}
        <button
          type="submit"
          style={{
            width: '100%',
            marginTop: 16,
            padding: 10,
            borderRadius: 8,
            border: 0,
            background: '#2563eb',
            color: '#fff',
            fontWeight: 600,
          }}
        >
          Login
        </button>
      </form>
    </div>
  )
}

const label = { display: 'block', margin: '10px 0 4px', fontSize: 13, color: '#475569' }
const input = {
  width: '100%',
  padding: 9,
  borderRadius: 8,
  border: '1px solid #cbd5e1',
  fontSize: 14,
}