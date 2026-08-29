import { Link, useLocation } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/upload', label: 'Upload Invoices' },
  { to: '/high-risk', label: 'High Risk' },
  { to: '/duplicates', label: 'Duplicates' },
  { to: '/reports', label: 'Reports' },
  { to: '/settings', label: 'Settings' },
]

const analyticsLinks = [
  { to: '/analytics', label: 'Executive Overview' },
  { to: '/analytics/vendors', label: 'Vendor Intelligence' },
  { to: '/analytics/validation', label: 'Validation Insights' },
  { to: '/analytics/duplicates', label: 'Duplicate Intelligence' },
  { to: '/analytics/audit', label: 'Audit Center' },
]

function SideLink({ to, label, active, indent }) {
  return (
    <Link
      to={to}
      style={{
        display: 'block',
        padding: '10px 20px',
        paddingLeft: indent ? 32 : 20,
        color: active ? '#38bdf8' : '#cbd5e1',
        fontWeight: active ? 700 : 500,
        background: active ? 'rgba(56,189,248,0.12)' : 'transparent',
        borderLeft: active ? '3px solid #38bdf8' : '3px solid transparent',
      }}
    >
      {label}
    </Link>
  )
}

export default function Sidebar() {
  const { pathname } = useLocation()
  const isAnalytics = pathname.startsWith('/analytics')
  return (
    <nav
      style={{
        width: 230,
        background: '#0f172a',
        color: '#fff',
        padding: '20px 0',
        minHeight: '100vh',
        flexShrink: 0,
      }}
    >
      <div style={{ padding: '0 20px 20px', fontSize: 20, fontWeight: 700 }}>💼 Invoice AI</div>
      {links.map((link) => (
        <SideLink key={link.to} to={link.to} label={link.label} active={pathname === link.to || (link.to === '/' && pathname === '/')} />
      ))}
      <div style={{ padding: '18px 20px 6px', fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '.08em' }}>Analytics</div>
      {analyticsLinks.map((link) => (
        <SideLink key={link.to} to={link.to} label={link.label} active={isAnalytics && pathname === link.to} indent />
      ))}
    </nav>
  )
}
