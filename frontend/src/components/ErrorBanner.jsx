export default function ErrorBanner({ message, onRetry }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: '12px',
      background: '#FEF2F2', border: '1px solid #FECACA',
      borderRadius: '12px', padding: '14px 18px',
      marginBottom: '20px',
    }}>
      {/* warning icon */}
      <svg
        viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2"
        style={{ width: '18px', height: '18px', flexShrink: 0, marginTop: '1px' }}
      >
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/>
        <path d="M12 9v4"/><path d="M12 17h.01"/>
      </svg>

      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontSize: '13px', fontWeight: '600', color: '#B91C1C', marginBottom: message ? '3px' : 0 }}>
          Something went wrong
        </p>
        {message && (
          <p style={{ fontSize: '12.5px', color: '#DC2626', lineHeight: 1.4, wordBreak: 'break-word' }}>
            {message}
          </p>
        )}
      </div>

      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            flexShrink: 0, fontSize: '12px', fontWeight: '600',
            color: '#DC2626', background: 'none', border: '1px solid #FECACA',
            borderRadius: '7px', padding: '4px 10px', cursor: 'pointer',
            fontFamily: 'inherit', whiteSpace: 'nowrap',
          }}
        >
          Retry
        </button>
      )}
    </div>
  )
}
