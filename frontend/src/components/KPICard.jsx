export default function KPICard({ label, value, icon, delta, deltaDirection = 'neutral' }) {
  const deltaColors = {
    up: { text: 'var(--green)', bg: 'var(--green-bg)' },
    down: { text: 'var(--red)', bg: 'var(--red-bg)' },
    neutral: { text: 'var(--text-secondary)', bg: 'var(--page)' }
  }

  const colors = deltaColors[deltaDirection] || deltaColors.neutral

  const arrowIcon = deltaDirection === 'up' ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <path d="M7 17 17 7M7 7h10v10"/>
    </svg>
  ) : deltaDirection === 'down' ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
      <path d="M7 7l10 10M17 7v10H7"/>
    </svg>
  ) : null

  return (
    <div className="kpi-card">
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '13px', color: 'var(--text-secondary)', fontWeight: '500' }}>
          {label}
        </span>
        <div className="kpi-icon">{icon}</div>
      </div>

      <div style={{
        fontFamily: "'IBM Plex Mono', monospace",
        fontWeight: '600',
        fontSize: '28px',
        color: 'var(--navy)',
        marginTop: '10px',
        letterSpacing: '-0.01em'
      }}>
        {value}
      </div>

      {delta && (
        <div style={{ display: 'flex', alignItems: 'center', marginTop: '12px' }}>
          <span
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              fontSize: '12px',
              fontWeight: '600',
              padding: '3px 7px',
              borderRadius: '6px',
              color: colors.text,
              background: colors.bg
            }}
          >
            {arrowIcon && <span style={{ width: '11px', height: '11px', display: 'flex' }}>{arrowIcon}</span>}
            {delta}
          </span>
        </div>
      )}

      <style>{`
        .kpi-card {
          background: var(--white);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 20px 20px 16px;
          position: relative;
          overflow: hidden;
        }
        .kpi-icon {
          width: 30px;
          height: 30px;
          border-radius: 8px;
          background: var(--blue-light);
          color: var(--blue);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .kpi-icon svg {
          width: 16px;
          height: 16px;
        }
      `}</style>
    </div>
  )
}
