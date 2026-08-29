import { useNavigate } from 'react-router-dom'

export default function Navbar() {
  const navigate = useNavigate()
  return (
    <header
      style={{
        background: '#fff',
        padding: '14px 24px',
        borderBottom: '1px solid #e2e8f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}
    >
      <h2 style={{ fontSize: 18 }}>Invoice Error Detector</h2>
      <button
        onClick={() => {
          localStorage.removeItem('token')
          navigate('/login')
        }}
        style={{
          padding: '6px 14px',
          borderRadius: 8,
          border: '1px solid #e2e8f0',
          background: '#fff',
        }}
      >
        Logout
      </button>
    </header>
  )
}