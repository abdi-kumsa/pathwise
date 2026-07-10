export default function SectionHeader({ title, subtitle, showLiveIndicator = false }) {
  return (
    <div style={{ marginBottom: '28px' }}>
      <h1 style={{
        fontFamily: "'Sora', sans-serif",
        fontWeight: '600',
        fontSize: '26px',
        letterSpacing: '-0.015em',
        color: 'var(--navy)'
      }}>
        {title}
      </h1>
      {(subtitle || showLiveIndicator) && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginTop: '8px'
        }}>
          {showLiveIndicator && (
            <>
              <span style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                background: 'var(--green)',
                boxShadow: '0 0 0 3px var(--green-bg)'
              }}></span>
              <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                Live data · synced 2 minutes ago
              </span>
            </>
          )}
          {subtitle && !showLiveIndicator && (
            <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
              {subtitle}
            </span>
          )}
        </div>
      )}
    </div>
  )
}
