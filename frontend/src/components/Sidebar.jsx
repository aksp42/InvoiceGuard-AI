const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/upload', label: 'Upload Invoices' },
  { to: '/high-risk', label: 'High Risk' },
  { to: '/duplicates', label: 'Duplicates' },
  { to: '/reports', label: 'Reports' },
  { to: '/settings', label: 'Settings' },
]

export default function Sidebar() {
  return (
    <nav
      style={{
        width: 220,
        background: '#0f172a',
        color: '#fff',
        padding: '20px 0',
        minHeight: '100vh',
      }}
    >
      <div style={{ padding: '0 20px 20px', fontSize: 20, fontWeight: 700 }}>💼 Invoice AI</div>
      {links.map((link) => (
        <a
          key={link.to}
          href={`#${link.to}`}
          onClick={(e) => {
            e.preventDefault()
            window.location.hash = link.to === '/' ? '/#/' : `#${link.to}`
          }}
          style={{
            display: 'block',
            padding: '10px 20px',
            color: '#cbd5e1',
          }}
        >
          {link.label}
        </a>
      ))}
    </nav>
  )
}