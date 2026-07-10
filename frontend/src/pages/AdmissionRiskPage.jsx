import { useState, useEffect, useRef } from 'react'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getAdmissionRisk } from '../api/enrollment'

const TREND_BADGE = {
  up:     { label: 'Growing',   color: '#10b981', bg: '#ecfdf5' },
  down:   { label: 'Declining', color: '#ef4444', bg: '#fef2f2' },
  stable: { label: 'Stable',    color: '#64748b', bg: '#f8fafc' },
}

const RISK_COLOR = score =>
  score >= 20 ? '#ef4444' : score >= 10 ? '#f59e0b' : '#10b981'

export default function AdmissionRiskPage() {
  // limit slider — debounced 500ms before triggering a new API call
  const [limit,          setLimit]          = useState(12)
  const [debouncedLimit, setDebouncedLimit] = useState(12)
  const timerRef = useRef(null)

  useEffect(() => {
    clearTimeout(timerRef.current)
    timerRef.current = setTimeout(() => setDebouncedLimit(limit), 500)
    return () => clearTimeout(timerRef.current)
  }, [limit])

  const { data: risks, loading, error, refetch } = useFetch(
    () => getAdmissionRisk(debouncedLimit),
    [debouncedLimit]
  )

  const data      = risks ?? []
  const declining = data.filter(r => r.trend === 'down').length
  const totalIn   = data.reduce((s, r) => s + r.recommended_intake, 0)
  const topRisk   = data[0]?.program ?? '—'
  const avgRisk   = data.length
    ? (data.reduce((s, r) => s + r.risk_score, 0) / data.length).toFixed(1)
    : '—'

  return (
    <div>
      <SectionHeader title="Admission risk" showLiveIndicator={true} />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Programmes declining"
          value={loading ? '—' : declining}
          delta="Below prior-year enrolment"
          deltaDirection={declining > 0 ? 'down' : 'up'}
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>}
        />
        <KPICard
          label="Total recommended intake"
          value={loading ? '—' : totalIn.toLocaleString()}
          delta="Across all programmes"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>}
        />
        <KPICard
          label="Highest risk programme"
          value={loading ? '—' : topRisk}
          delta={loading ? '' : 'Risk score: ' + (data[0]?.risk_score?.toFixed(1) ?? '—')}
          deltaDirection="down"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>}
        />
        <KPICard
          label="Avg risk score"
          value={loading ? '—' : avgRisk}
          delta="Lower is better"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
        />
      </div>

      <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
        {/* header + limit slider */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '4px', gap: '16px' }}>
          <div>
            <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '2px' }}>
              Programme Risk Assessment
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Risk score = % enrolment decline 2023→2024. Green &lt;10 · Amber 10–20 · Red &gt;20.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}>
            <label style={{ fontSize: '12px', color: 'var(--text-secondary)', fontWeight: '500', whiteSpace: 'nowrap' }}>
              Show top {limit}
            </label>
            <input
              type="range" min={3} max={12} step={1} value={limit}
              onChange={e => setLimit(Number(e.target.value))}
              style={{ width: '100px', accentColor: '#2563eb', cursor: 'pointer' }}
            />
          </div>
        </div>

        {loading ? (
          <LoadingSpinner message="Loading risk data…" height={200} />
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', marginTop: '16px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                {['Programme', 'Trend', 'Risk Score', 'Rec. Intake'].map(h => (
                  <th key={h} style={{ textAlign: h === 'Programme' ? 'left' : 'center', padding: '8px 12px', color: 'var(--text-muted)', fontWeight: '600', fontSize: '12px' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.map((r, i) => {
                const badge = TREND_BADGE[r.trend] ?? TREND_BADGE.stable
                return (
                  <tr key={r.program} style={{ borderBottom: '1px solid #f8fafc', background: i % 2 === 0 ? 'transparent' : '#fafafa' }}>
                    <td style={{ padding: '10px 12px', color: 'var(--navy)', fontWeight: '500' }}>{r.program}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <span style={{ background: badge.bg, color: badge.color, borderRadius: '6px', padding: '2px 8px', fontSize: '11px', fontWeight: '600' }}>
                        {badge.label}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'center', fontWeight: '600', color: RISK_COLOR(r.risk_score) }}>
                      {r.risk_score.toFixed(1)}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                      {r.recommended_intake}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
