// Phase 6 — Analytics page shell: dark-blue theme, header + nav tabs.
import { NavLink } from 'react-router-dom'
import { Skeleton } from './charts.jsx'

export const ANALYTICS_TABS = [
  { to: '/analytics', label: 'Executive Overview', icon: '📊' },
  { to: '/analytics/vendors', label: 'Vendor Intelligence', icon: '🏢' },
  { to: '/analytics/validation', label: 'Validation Insights', icon: '✅' },
  { to: '/analytics/duplicates', label: 'Duplicate Intelligence', icon: '🔁' },
  { to: '/analytics/audit', label: 'Audit Center', icon: '🛡️' },
]

export default function AnalyticsShell({ title, subtitle, children }) {
  return (
    <div className="analytics-root">
      <div className="analytics-inner">
        <header className="analytics-header">
          <div>
            <div className="analytics-tag live"><span className="dot" />Live · Real-time source of truth</div>
            <h1>{title}</h1>
            <div className="sub">{subtitle}</div>
          </div>
          <span className="analytics-tag">InvoiceGuard · Power BI ready</span>
        </header>

        <nav className="analytics-tabs">
          {ANALYTICS_TABS.map((t) => (
            <NavLink key={t.to} to={t.to} end={t.to === '/analytics'} className={({ isActive }) => `analytics-tab${isActive ? ' active' : ''}`}>
              <span>{t.icon}</span>{t.label}
            </NavLink>
          ))}
        </nav>

        {children}
      </div>
    </div>
  )
}

export function LoadingGrid({ cards = 6, charts = 2 }) {
  return (
    <>
      <div className="kpi-grid">
        {Array.from({ length: cards }).map((_, i) => <Skeleton key={i} type="kpi" />)}
      </div>
      <div className={`analytics-grid grid-${charts >= 2 ? '2' : '1'}`}>
        {Array.from({ length: charts }).map((_, i) => <Skeleton key={i} type="chart" />)}
      </div>
    </>
  )
}
