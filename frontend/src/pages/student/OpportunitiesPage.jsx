import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getOpportunities } from '../../api/student'
import { SERIES } from '../../config/chartTheme'

const KIND_COLOR = {
  scholarship: SERIES[0],
  internship: SERIES[1],
  training: SERIES[2],
  job_fair: SERIES[3],
}

export default function OpportunitiesPage() {
  const { data, loading, error, refetch } = useFetch(getOpportunities)
  const items = [...(data?.items ?? [])].sort((a, b) => Number(b.year || 0) - Number(a.year || 0))
  const kinds = data?.kinds ?? ['scholarship', 'internship', 'training', 'job_fair']

  return (
    <div>
      <SectionHeader
        title="Opportunities and alerts"
        subtitle="Scholarships, internships, training and hiring windows linked to your field"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading opportunities…" height={240} />}
      {data && (
        <>
          <DataNote tone="simulated">
            {data.note} official: {String(data.official === true)}.
          </DataNote>
          <div style={{ display: 'flex', gap: 8, margin: '16px 0', flexWrap: 'wrap' }}>
            {kinds.map(k => (
              <span key={k} style={{
                fontSize: 12, fontWeight: 600, padding: '4px 10px', borderRadius: 999,
                background: 'var(--page)', border: `1px solid ${KIND_COLOR[k] || 'var(--border)'}`,
                color: KIND_COLOR[k],
              }}>{k.replace('_', ' ')}</span>
            ))}
          </div>
          {items.length === 0 && (
            <EmptyState title="No items in this feed" description="When a ministry circular is loaded it will appear here. Until then the simulated feed may be empty for this field." />
          )}
          {items.length > 0 && (
            <ol data-testid="opportunity-feed" style={{ listStyle: 'none', margin: 0, padding: 0, borderLeft: '2px solid var(--border)' }}>
              {items.map((item, i) => (
                <li key={i} style={{ position: 'relative', padding: '0 0 16px 20px' }}>
                  <span style={{
                    position: 'absolute', left: -6, top: 8, width: 10, height: 10, borderRadius: 999,
                    background: KIND_COLOR[item.kind] || 'var(--border)',
                  }} />
                  <div className="panel" style={{ margin: 0 }}>
                    <p className="panel-title">{item.title}</p>
                    <p className="panel-sub" style={{ color: KIND_COLOR[item.kind] }}>{item.kind.replace('_', ' ')} · {item.year}</p>
                    <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>{item.detail}</p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </>
      )}
    </div>
  )
}
