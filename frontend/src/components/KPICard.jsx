/**
 * Headline figure with an optional comparison line.
 *
 * `delta` with direction up/down is a real comparison (year on year, CAGR,
 * ratio against a threshold) and is coloured. A neutral delta is plain
 * context ("8 programmes", "yield 96.8%") and stays grey. Decorative icons
 * were dropped: the label says what the number is.
 */
export default function KPICard({ label, value, delta, deltaDirection = 'neutral' }) {
  const dir = deltaDirection === 'up' || deltaDirection === 'down' ? deltaDirection : 'neutral'
  const arrow = dir === 'up' ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
      <path d="M7 17 17 7M7 7h10v10" />
    </svg>
  ) : dir === 'down' ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" aria-hidden="true">
      <path d="M7 7l10 10M17 7v10H7" />
    </svg>
  ) : null

  return (
    <div className="kpi-card">
      <span className="kpi-label">{label}</span>
      <div className="kpi-value">{value}</div>
      {delta ? (
        <div className={`kpi-delta ${dir}`}>
          {arrow}
          <span>{delta}</span>
        </div>
      ) : null}
    </div>
  )
}
