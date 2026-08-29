// Phase 6 — Animated number counter (counts up on mount / value change).
import { useEffect, useRef, useState } from 'react'

export default function AnimatedCounter({ value = 0, duration = 900, format = null, prefix = '', suffix = '' }) {
  const target = Number(value) || 0
  const [display, setDisplay] = useState(0)
  const [started, setStarted] = useState(false)
  const raf = useRef(null)
  const startVal = useRef(0)

  useEffect(() => {
    setStarted(false)
  }, [target])

  useEffect(() => {
    if (started) return
    setStarted(true)
    startVal.current = 0
    const start = performance.now()
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - p, 3)
      setDisplay(Math.round(target * eased))
      if (p < 1) raf.current = requestAnimationFrame(tick)
      else setDisplay(target)
    }
    raf.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf.current)
  }, [started, target, duration])

  const rendered = typeof format === 'function' ? format(display) : display.toLocaleString('en-IN')
  return (
    <span>
      {prefix}{rendered}{suffix}
    </span>
  )
}
