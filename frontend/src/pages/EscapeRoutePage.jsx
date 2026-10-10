import { useState } from 'react'

import SectionHeader from '../components/SectionHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorBanner from '../components/ErrorBanner'
import DataNote from '../components/DataNote'
import EmptyState from '../components/EmptyState'
import useFetch from '../hooks/useFetch'
import { getAlternatives, getStudentProfile } from '../api/student'
import { SERIES, STATUS } from '../config/chartTheme'

export default function EscapeRoutePage() {
  const { data: profile } = useFetch(getStudentProfile)
  const [field, setField] = useState('')
  const current = field || profile?.field || ''
  const { data, loading, error, refetch } = useFetch(
    () => getAlternatives(current),
    [current],
  )
  const rows = (data?.rows ?? []).filter(r => r.rank != null)

  return (
    <div>
      <SectionHeader
        title="Alternative fields"
        subtitle="Ranked on labour demand, expected supply, eligibility and skills fit — not graduate fit classification"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      <DataNote tone="simulated">
        {data?.method || 'Fit classification does not enter this ranking.'}
        {data?.fit_classification_used === false ? ' Fit classification is not used.' : ''}
      </DataNote>
      <div className="panel" style={{ margin: '16px 0' }}>
        <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)' }}>Current field</label>
        <input
          value={field}
          onChange={e => setField(e.target.value)}
          placeholder={profile?.field || 'Engineering & Technology'}
          style={{
            display: 'block', width: '100%', marginTop: 6, padding: '8px 10px',
            border: '1px solid var(--border)', borderRadius: 8,
          }}
        />
      </div>
      {loading && <LoadingSpinner message="Ranking alternatives…" height={240} />}
      {data && rows.length === 0 && (
        <EmptyState title="No alternatives" description="No ranked fields for this starting programme." />
      )}
      {rows.map(row => (
        <div key={row.field} className="panel" style={{ marginBottom: 12 }} data-testid="alternative-row">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
            <p className="panel-title">{row.rank}. {row.field}</p>
            <span style={{ fontFamily: 'IBM Plex Mono, monospace', color: SERIES[0] }}>{row.score}</span>
          </div>
          <p className="panel-sub">{row.status} · severity Q{row.severity}</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
            {(row.factors || []).map(f => (
              <span key={f.factor} data-testid="factor" style={{
                fontSize: 12, padding: '4px 8px', borderRadius: 8, background: 'var(--page)',
              }}>
                {f.factor} {(f.weight * 100).toFixed(0)}% → {f.contribution}
              </span>
            ))}
          </div>
        </div>
      ))}
      {data && (
        <p style={{ fontSize: 12, color: STATUS.good, marginTop: 8 }}>
          Ranking factors: {(data.ranking_factors || []).join(', ')}
        </p>
      )}
    </div>
  )
}
