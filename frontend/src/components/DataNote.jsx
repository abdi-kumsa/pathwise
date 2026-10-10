/**
 * A visible provenance / caveat note.
 *
 * Exists because some figures in this app are honest but easy to over-read —
 * most importantly the graduate fit classification, which is near-uniform
 * across fields and must not be presented as a ranking. Where the API returns
 * `comparable: false` and a `caveat`, the page shows it here rather than
 * leaving the limitation in a docstring the reader will never see.
 */
export default function DataNote({ children, tone = 'info' }) {
  const tones = {
    info:    { bg: '#F1F5F9', border: '#E2E8F0', fg: '#475569', icon: 'M12 16v-4M12 8h.01' },
    caution: { bg: '#FEF3C7', border: '#FDE68A', fg: '#92400E', icon: 'M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z' },
    simulated: { bg: '#FFF7ED', border: '#FED7AA', fg: '#9A3412', icon: 'M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z' },
  }
  const t = tones[tone] ?? tones.info

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-start', gap: '9px',
      background: t.bg, border: `1px solid ${t.border}`,
      borderRadius: '10px', padding: '10px 13px',
      fontSize: '12.5px', lineHeight: 1.55, color: t.fg,
    }}>
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
           strokeLinecap="round" strokeLinejoin="round"
           style={{ width: 15, height: 15, flexShrink: 0, marginTop: 1 }}>
        {tone === 'info' && <circle cx="12" cy="12" r="9" />}
        <path d={t.icon} />
      </svg>
      <span>{children}</span>
    </div>
  )
}
