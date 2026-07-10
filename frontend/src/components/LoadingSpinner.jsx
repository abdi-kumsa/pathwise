export default function LoadingSpinner({ message = 'Loading…', height = 280 }) {
  return (
    <div style={{
      height, display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', gap: '12px',
    }}>
      <div style={{
        width: '32px', height: '32px', borderRadius: '50%',
        border: '3px solid #E2E8F0',
        borderTopColor: '#2563EB',
        animation: 'pathwise-spin 0.75s linear infinite',
      }} />
      <p style={{ fontSize: '13px', color: 'var(--text-muted)', fontWeight: '500' }}>
        {message}
      </p>
      <style>{`@keyframes pathwise-spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
