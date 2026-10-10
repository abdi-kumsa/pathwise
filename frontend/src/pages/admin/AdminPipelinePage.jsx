import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import EmptyState from '../../components/EmptyState'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getPipelineStatus } from '../../api/admin'
import { STATUS } from '../../config/chartTheme'

const FAMILY_LABEL = {
  education: 'Education',
  labor: 'Labor',
  policy: 'Policy',
  investment: 'Investment',
}

const STATUS_COLOR = {
  ok: STATUS.good,
  warning: STATUS.warning,
  error: STATUS.critical,
  missing: STATUS.critical,
}

export default function AdminPipelinePage() {
  const { data, loading, error, refetch } = useFetch(getPipelineStatus)
  const feeds = data?.feeds ?? []

  return (
    <div>
      <SectionHeader
        title="Data pipeline"
        subtitle="Status, freshness and last sync of every Ethiopia feed"
      />
      <DataNote tone="simulated">
        Freshness is parquet mtime and the maximum year in each table. Tier is
        simulated until official CSA / MoE / ESS files replace the generator.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading pipeline status…" height={280} />}

      {data && feeds.length === 0 && (
        <EmptyState title="No feeds registered" description="The spec registry returned no source tables." />
      )}

      {feeds.length > 0 && (
        <ul data-testid="pipeline-list" style={{ listStyle: 'none', marginTop: 16, display: 'grid', gap: 8 }}>
          {feeds.map(feed => {
            const color = STATUS_COLOR[feed.status] || STATUS.warning
            return (
              <li key={feed.source_table} data-testid="pipeline-feed" className="panel"
                  style={{ display: 'flex', gap: 14, alignItems: 'flex-start', padding: '12px 14px' }}>
                <span aria-hidden="true" style={{
                  width: 10, height: 10, borderRadius: '50%', marginTop: 5,
                  background: color, flexShrink: 0,
                }} />
                <div style={{ flex: 1 }}>
                  <p style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--navy)' }}>
                    {feed.source_table}
                    <span style={{ marginLeft: 8, fontWeight: 600, fontSize: 11, color }}>
                      {feed.status_label}
                    </span>
                  </p>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 3 }}>
                    {FAMILY_LABEL[feed.family] || feed.family}
                    {' · '}
                    {feed.rows} rows
                    {feed.year_max != null ? ` · years ${feed.year_min}–${feed.year_max}` : ''}
                    {' · '}
                    last sync {feed.last_sync ? feed.last_sync.replace('T', ' ').slice(0, 19) : 'never'}
                    {' · '}
                    freshness {feed.freshness}
                    {' · '}
                    tier {feed.tier}
                  </p>
                  {feed.errors?.length > 0 && (
                    <p style={{ fontSize: 12, color: 'var(--red)', marginTop: 4 }}>
                      {feed.errors[0]}
                    </p>
                  )}
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
