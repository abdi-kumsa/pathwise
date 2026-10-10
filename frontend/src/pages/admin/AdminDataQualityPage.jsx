import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import EmptyState from '../../components/EmptyState'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getDataQuality } from '../../api/admin'
import { STATUS } from '../../config/chartTheme'

const SEV_COLOR = {
  critical: STATUS.critical,
  high: STATUS.serious,
  moderate: STATUS.warning,
  low: STATUS.good,
}

export default function AdminDataQualityPage() {
  const { data, loading, error, refetch } = useFetch(getDataQuality)
  const alerts = data?.alerts ?? []

  return (
    <div>
      <SectionHeader
        title="Data quality"
        subtitle="Missing values, duplicates, outliers and inconsistent records"
      />
      <DataNote tone="simulated">
        Scans of the Ethiopia parquet tables, not the old Postgres warehouse
        script. Figures stay simulated until official files land.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Scanning tables…" height={280} />}

      {data && alerts.length === 0 && (
        <EmptyState
          title="No quality alerts"
          description="Contract checks and parquet scans did not flag missing values, duplicates, outliers or inconsistent records."
        />
      )}

      {alerts.length > 0 && (
        <ul data-testid="quality-alerts" style={{ listStyle: 'none', marginTop: 16, display: 'grid', gap: 8 }}>
          {alerts.map((alert, i) => {
            const color = SEV_COLOR[alert.severity] || STATUS.warning
            return (
              <li key={`${alert.table}-${alert.check}-${i}`} className="panel"
                  style={{ display: 'flex', gap: 12, padding: '12px 14px' }}>
                <span aria-hidden="true" style={{
                  width: 10, height: 10, borderRadius: '50%', marginTop: 5, background: color, flexShrink: 0,
                }} />
                <div>
                  <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)' }}>
                    {alert.table}
                    <span style={{ marginLeft: 8, color, fontSize: 11 }}>{alert.severity_label}</span>
                    <span style={{ marginLeft: 8, color: 'var(--text-secondary)', fontWeight: 500, fontSize: 11 }}>
                      {alert.check}
                    </span>
                  </p>
                  <p style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 4 }}>
                    {alert.message}
                  </p>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
