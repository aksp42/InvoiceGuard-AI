// Phase 6 — Reusable, dependency-free SVG chart components.
// Lightweight + portable; the same measures can be mirrored in Power BI.

import { useEffect, useRef } from 'react'

const UR = (x) => Math.round(x * 100) / 100

/* ----------------------------- Line chart ----------------------------- */
export function LineChart({ data, color = '#38bdf8', height = 220, width = null, y = 'value', points = true }) {
  const wrapRef = useRef(null)
  const w = width || 560
  const pad = { l: 44, r: 12, t: 12, b: 26 }
  const iw = w - pad.l - pad.r
  const ih = height - pad.t - pad.b
  const max = Math.max(1, ...data.map((d) => Number(d[y] || 0)))
  const X = (i) => pad.l + (data.length === 1 ? iw / 2 : (i / (data.length - 1)) * iw)
  const Y = (v) => pad.t + ih - (Number(v) / max) * ih
  const coords = data.map((d, i) => [X(i), Y(d[y])])
  const path = coords.map((c, i) => `${i ? 'L' : 'M'}${UR(c[0])},${UR(c[1])}`).join(' ')
  const area = `${path} L${UR(coords[coords.length - 1][0])},${UR(pad.t + ih)} L${UR(coords[0][0])},${UR(pad.t + ih)} Z`
  const ticks = 4
  return (
    <div className="chart-wrap" ref={wrapRef}>
      <svg viewBox={`0 0 ${w} ${height}`} role="img" aria-label="line chart">
        {Array.from({ length: ticks + 1 }).map((_, i) => {
          const v = (max / ticks) * i
          const yy = Y(v)
          return (
            <g key={i}>
              <line x1={pad.l} y1={yy} x2={w - pad.r} y2={yy} stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
              <text x={pad.l - 8} y={yy + 4} textAnchor="end" fontSize="10" fill="#6b7f96">{shortNum(v)}</text>
            </g>
          )
        })}
        <path d={area} fill={color} opacity="0.12" />
        <path d={path} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />
        {points && coords.map((c, i) => (
          <circle key={i} cx={c[0]} cy={c[1]} r="3.5" fill={color} stroke="#0b1c31" strokeWidth="2" />
        ))}
        {data.map((d, i) => (
          <text key={i} x={X(i)} y={height - 8} textAnchor="middle" fontSize="10" fill="#6b7f96">{d.label}</text>
        ))}
      </svg>
    </div>
  )
}

/* ----------------------------- Area chart ----------------------------- */
export function AreaChart({ data, color = '#818cf8', height = 220, width = 560 }) {
  return <LineChart data={data} color={color} height={height} width={width} points={false} />
}

/* ----------------------------- Bar chart ------------------------------ */
export function BarChart({ data, color = '#38bdf8', height = 220, width = 560, y = 'value', valueColor = null }) {
  const pad = { l: 44, r: 12, t: 12, b: 26 }
  const iw = width - pad.l - pad.r
  const ih = height - pad.t - pad.b
  const max = Math.max(1, ...data.map((d) => Number(d[y] || 0)))
  const slot = iw / data.length
  const bw = Math.min(34, slot * 0.55)
  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="bar chart">
        {Array.from({ length: 5 }).map((_, i) => {
          const v = (max / 4) * i
          const yy = pad.t + ih - (v / max) * ih
          return (
            <g key={i}>
              <line x1={pad.l} y1={yy} x2={width - pad.r} y2={yy} stroke="rgba(255,255,255,0.08)" strokeWidth="1" />
              <text x={pad.l - 8} y={yy + 4} textAnchor="end" fontSize="10" fill="#6b7f96">{shortNum(v)}</text>
            </g>
          )
        })}
        {data.map((d, i) => {
          const h = (Number(d[y]) / max) * ih
          const x = pad.l + i * slot + (slot - bw) / 2
          const yy = pad.t + ih - h
          return (
            <g key={i}>
              <rect x={x} y={yy} width={bw} height={h} rx="5" fill={d.color || color} />
              {valueColor !== null && (
                <text x={x + bw / 2} y={yy - 6} textAnchor="middle" fontSize="10" fill={valueColor}>{shortNum(d[y])}</text>
              )}
              <text x={x + bw / 2} y={height - 8} textAnchor="middle" fontSize="10" fill="#6b7f96">{d.label}</text>
            </g>
          )
        })}
      </svg>
    </div>
  )
}

/* ----------------------------- Donut chart ---------------------------- */
export function DonutChart({ data, size = 190, thickness = 26, centerLabel = '', centerValue = '', centerSub = '' }) {
  const total = data.reduce((s, d) => s + Number(d.value || 0), 0) || 1
  const r = (size - thickness) / 2
  const cx = size / 2, cy = size / 2
  const circ = 2 * Math.PI * r
  let offset = 0
  return (
    <div className="chart-wrap" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
      <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} role="img" aria-label="donut chart">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={thickness} />
        {data.map((d, i) => {
          const frac = Number(d.value || 0) / total
          const len = frac * circ
          const el = (
            <circle
              key={i}
              cx={cx} cy={cy} r={r} fill="none"
              stroke={d.color || '#38bdf8'} strokeWidth={thickness}
              strokeDasharray={`${UR(len)} ${UR(circ - len)}`}
              strokeDashoffset={UR(-offset)} strokeLinecap="butt"
              transform={`rotate(-90 ${cx} ${cy})`}
            />
          )
          offset += len
          return el
        })}
        <text x={cx} y={cy - (centerValue ? 4 : 0)} textAnchor="middle" fontSize="26" fontWeight="800" fill="#f1f5f9">{centerValue || total}</text>
        {centerValue && <text x={cx} y={cy + 16} textAnchor="middle" fontSize="10" fill="#9fb0c3">{centerLabel}</text>}
        {!centerValue && centerLabel && <text x={cx} y={cy + 16} textAnchor="middle" fontSize="11" fill="#9fb0c3">{centerLabel}</text>}
      </svg>
      <div className="chart-legend">
        {data.map((d, i) => (
          <span className="legend-item" key={i}>
            <span className="legend-dot" style={{ background: d.color }} />
            {d.label} · {d.value}
          </span>
        ))}
      </div>
    </div>
  )
}

/* ----------------------------- Heatmap -------------------------------- */
export function Heatmap({ rows, columns, cells, height = 260 }) {
  const cellW = 86, rowH = 44, labelW = 150
  const w = labelW + columns.length * cellW
  const h = Math.max(120, 30 + rows.length * rowH)
  const max = Math.max(1, ...cells.flat().map((c) => c.value || 0))
  const heat = (v) => {
    const t = Number(v || 0) / max
    const r = 7 + Math.round(t * 180)
    const g = Math.round(38 + (1 - t) * 120)
    const b = 49 + Math.round(t * 90)
    return `rgb(${r},${g},${b})`
  }
  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="heatmap" style={{ minHeight: 220 }}>
        {columns.map((c, ci) => (
          <text key={ci} x={labelW + ci * cellW + cellW / 2} y="16" textAnchor="middle" fontSize="11" fontWeight="700" fill="#9fb0c3">{c}</text>
        ))}
        {rows.map((row, ri) => (
          <g key={ri}>
            <text x={labelW - 8} y={30 + ri * rowH + cellW / 2} textAnchor="end" fontSize="11" fill="#cbd5e1">{row}</text>
            {columns.map((_, ci) => {
              const c = cells[ri][ci]
              const v = c.value
              return (
                <g key={ci}>
                  <rect x={labelW + ci * cellW} y={20 + ri * rowH} width={cellW - 6} height={rowH - 8} rx="7" fill={v ? heat(v) : 'rgba(255,255,255,0.03)'} stroke="rgba(255,255,255,0.06)" />
                  <text x={labelW + ci * cellW + (cellW - 6) / 2} y={20 + ri * rowH + (rowH - 8) / 2 + 4} textAnchor="middle" fontSize="11" fontWeight="600" fill={v ? '#f8fafc' : '#5b6b7f'}>{v || '—'}</text>
                </g>
              )
            })}
          </g>
        ))}
      </svg>
      {rows.length === 0 && (
        <div className="empty"><div className="empty-ico">▦</div><h3>No data to map</h3></div>
      )}
    </div>
  )
}

/* --------------------------- Trend card ------------------------------- */
export function TrendCard({ label, value, delta, icon, accent = '#38bdf8', sub }) {
  const up = (delta || 0) >= 0
  return (
    <div className="glass kpi-card">
      <div className="ico" style={{ background: `${accent}22`, color: accent }}>{icon}</div>
      <div className="k-label">{label}</div>
      <div className="k-value">{value}</div>
      {(delta != null || sub) && (
        <div className="k-sub">
          {delta != null && (
            <span className={`g-delta ${up ? 'gd-good' : 'gd-bad'}`}>{up ? '▲' : '▼'} {Math.abs(delta)}%</span>
          )}
          {sub && <span style={{ marginLeft: delta != null ? 8 : 0 }}>{sub}</span>}
        </div>
      )}
    </div>
  )
}

/* --------------------------- Skeleton block --------------------------- */
export function Skeleton({ type = 'chart' }) {
  return <div className={`skeleton sk-${type}`} />
}

/* --------------------------- Empty state ------------------------------ */
export function EmptyState({ icon = '📭', title = 'No data yet', message = 'Data will appear here once you upload and process invoices.' }) {
  return (
    <div style={{ maxWidth: 640, margin: '0 auto' }}>
      <div className="empty">
        <div className="empty-ico">{icon}</div>
        <h3>{title}</h3>
        <p>{message}</p>
      </div>
    </div>
  )
}

function shortNum(n) {
  if (n >= 1e6) return `${UR(n / 1e6)}M`
  if (n >= 1e3) return `${UR(n / 1e3)}k`
  return String(n)
}
