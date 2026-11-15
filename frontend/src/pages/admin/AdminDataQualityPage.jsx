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
        Scans of the Ethiopia tables. Figures are simulated, calibrated to published
        sources, until official files land.
      </DataNote>

      {data?.calibration?.available && (
        <div className="panel" style={{ marginTop: 16 }} data-testid="calibration-summary">
          <p className="panel-title">What the simulation is calibrated to</p>
          <p className="panel-sub">
            Figures in <code>{data.calibration.file}</code> across {data.calibration.sections.length} sections,
            each with its source and a confidence tier
          </p>
          <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', margin: '4px 0 12px' }}>
            {data.calibration.tiers.map(t => (
              <div key={t.tier}>
                <div style={{ fontSize: 22, fontWeight: 600, color: 'var(--navy)' }}>{t.count}</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>{t.tier}</div>
              </div>
            ))}
          </div>
          {data.calibration.gaps.length > 0 && (
            <>
              <p style={{ fontSize: 12.5, fontWeight: 600, color: 'var(--navy)', marginBottom: 4 }}>Known gaps</p>
              <ul style={{ fontSize: 12.5, color: 'var(--text-secondary)', paddingLeft: 18, lineHeight: 1.6 }}>
                {data.calibration.gaps.map(g => <li key={g}>{g}</li>)}
              </ul>
            </>
          )}
        </div>
      )}

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
