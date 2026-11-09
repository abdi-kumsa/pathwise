import { useMemo } from 'react'

/**
 * Pairwise comparison editor for Saaty's AHP (PROC.S7, plan item 4.2).
 *
 * Only the upper triangle is editable; the lower triangle is its reciprocal,
 * so the matrix is always valid input. The consistency ratio is computed as
 * the user types (power iteration on the matrix, Saaty's random index), and
 * the server repeats the check and refuses CR > 0.1 on save.
 */
// Saaty's full 1–9 scale, including the intermediate even values, and their
// reciprocals. Every value the server accepts can be shown exactly.
const NAMES = { 1: 'equal', 3: 'moderate', 5: 'strong', 7: 'very strong', 9: 'extreme' }
const SCALE = [
  ...[9, 8, 7, 6, 5, 4, 3, 2].map(k => ({ v: 1 / k, label: `1/${k}` })),
  ...[1, 2, 3, 4, 5, 6, 7, 8, 9].map(k => ({ v: k, label: NAMES[k] ? `${k} ${NAMES[k]}` : String(k) })),
]
const RI = { 1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49 }
export const CR_MAX = 0.1

export function consistency(matrix) {
  const n = matrix.length
  if (n < 3) return { weights: matrix.map(() => 1 / n), cr: 0, lambda: n }
  let w = Array(n).fill(1 / n)
  for (let it = 0; it < 100; it++) {
    const next = matrix.map(row => row.reduce((s, a, j) => s + a * w[j], 0))
    const total = next.reduce((s, x) => s + x, 0)
    w = next.map(x => x / total)
  }
  const aw = matrix.map(row => row.reduce((s, a, j) => s + a * w[j], 0))
  const lambda = aw.reduce((s, x, i) => s + x / w[i], 0) / n
  const ci = (lambda - n) / (n - 1)
  return { weights: w, lambda, cr: RI[n] ? ci / RI[n] : null }
}

const nearest = (x) => SCALE.reduce((best, s) => (Math.abs(Math.log(s.v / x)) < Math.abs(Math.log(best.v / x)) ? s : best), SCALE[8]).v

export default function AhpMatrixEditor({ labels, matrix, onChange }) {
  const n = labels.length
  const safe = useMemo(() => {
    if (matrix?.length === n && matrix.every(r => r.length === n)) return matrix
    return Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 1 : 1)))
  }, [matrix, n])
  const { weights, cr } = useMemo(() => consistency(safe), [safe])

  const set = (i, j, v) => {
    const next = safe.map(r => [...r])
    next[i][j] = v
    next[j][i] = 1 / v
    onChange(next)
  }

  if (n < 3 || n > 10) {
    return <p style={{ fontSize: 12.5, color: 'var(--text-secondary)' }}>Enter 3 to 10 criteria.</p>
  }
  const ok = cr != null && cr <= CR_MAX
  return (
    <div>
      <table className="data-table" style={{ fontSize: 12 }} data-testid="ahp-grid">
        <thead>
          <tr>
            <th />
            {labels.map(l => <th key={l} style={{ textAlign: 'center' }}>{l}</th>)}
            <th style={{ textAlign: 'right' }}>weight</th>
          </tr>
        </thead>
        <tbody>
          {labels.map((row, i) => (
            <tr key={row}>
              <th style={{ textAlign: 'left' }}>{row}</th>
              {labels.map((col, j) => (
                <td key={col} style={{ textAlign: 'center' }}>
                  {i === j ? '1' : j > i ? (
                    <select aria-label={`${row} vs ${col}`} value={nearest(safe[i][j])}
                            onChange={e => set(i, j, Number(e.target.value))}>
                      {SCALE.map(s => <option key={s.label} value={s.v}>{s.label}</option>)}
                    </select>
                  ) : (
                    <span style={{ color: 'var(--text-muted)' }}>
                      {safe[i][j] >= 1 ? safe[i][j].toFixed(0) : `1/${Math.round(1 / safe[i][j])}`}
                    </span>
                  )}
                </td>
              ))}
              <td style={{ textAlign: 'right', fontFamily: 'IBM Plex Mono, monospace' }}>
                {(weights[i] * 100).toFixed(1)}%
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p data-testid="ahp-live-cr" style={{ fontSize: 12.5, marginTop: 6, color: ok ? 'var(--green)' : 'var(--red)' }}>
        Consistency ratio {cr != null ? cr.toFixed(3) : '—'} — {ok
          ? 'consistent enough to use (≤ 0.10)'
          : 'too inconsistent; the server will refuse these weights (> 0.10)'}
      </p>
    </div>
  )
}
