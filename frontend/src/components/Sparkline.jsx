import { fmtNum } from '../config/chartTheme'

/**
 * Inline trend for a table row: one observed series, first-to-last, with the
 * last point marked. No axes: the row's numbers carry the scale, the line
 * carries the shape. Needs at least two finite values, otherwise a dash.
 */
export default function Sparkline({ values = [], width = 72, height = 20, stroke = '#2563EB', label }) {
  const pts = values
    .map((v, i) => [i, v == null ? null : Number(v)])
    .filter(p => p[1] != null && Number.isFinite(p[1]))
  if (pts.length < 2) return <span className="spark spark-empty" aria-hidden="true">—</span>

  const ys = pts.map(p => p[1])
  const n = Math.max(values.length - 1, 1)
  const min = Math.min(...ys)
  const max = Math.max(...ys)
  const pad = 2
  const sx = i => pad + (i / n) * (width - 2 * pad)
  const sy = v => (max === min ? height / 2 : pad + (1 - (v - min) / (max - min)) * (height - 2 * pad))
  const d = pts.map(([i, v], k) => `${k ? 'L' : 'M'}${sx(i).toFixed(1)} ${sy(v).toFixed(1)}`).join(' ')
  const [lastI, lastV] = pts[pts.length - 1]
  const title = label ?? `${fmtNum(Math.round(ys[0]))} → ${fmtNum(Math.round(lastV))}`

  return (
    <svg className="spark" width={width} height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={title}>
      <title>{title}</title>
      <path d={d} fill="none" stroke={stroke} strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
      <circle cx={sx(lastI)} cy={sy(lastV)} r="2" fill={stroke} />
    </svg>
  )
}
