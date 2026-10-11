import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getMigration } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function MigrationPage() {
  const { data, loading, error, refetch } = useFetch(getMigration)
  const series = data?.series ?? []
  const years = [...new Set(series.map(r => r.year))].sort()
  const national = years.map(year => {
    const slice = series.filter(r => r.year === year)
    return {
      year,
      skilled_emigration_count: slice.reduce((s, r) => s + Number(r.skilled_emigration_count || 0), 0),
      return_migration_count: slice.reduce((s, r) => s + Number(r.return_migration_count || 0), 0),
    }
  })

  return (
    <div>
      <SectionHeader
        title="Migration and labour supply pressure"
        subtitle="Skilled emigration and return migration where the series exists"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading migration…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">{data.note || 'Simulated migration series. Degrades to unavailable rather than inventing coverage.'}</DataNote>
          {data.available === false && (
            <EmptyState
              title="Migration series unavailable"
              description={data.reason || 'No authorised migration file is on the request path.'}
            />
          )}
          {data.available !== false && (
            <>
            <div className="panel" style={{ marginTop: 16 }}>
              <p className="panel-title">National trend</p>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={national} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtNum} />
                  <Tooltip {...tooltipProps} />
                  <Legend />
                  <Line type="monotone" dataKey="skilled_emigration_count" name="Skilled emigration" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="return_migration_count" name="Return migration" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="panel" style={{ marginTop: 16 }} data-testid="migration-flow">
              <p className="panel-title">Origin → destination (latest year)</p>
              <p className="panel-sub">
                No origin–destination matrix exists. Region is treated as origin;
                emigration goes abroad and return arrives back to the same region.
              </p>
              {(data.rows || []).slice(0, 12).map((r, i) => (
                <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                  <span>{r.region} → abroad</span>
                  <span>{fmtNum(r.skilled_emigration_count)} out · {fmtNum(r.return_migration_count)} return</span>
                </div>
              ))}
            </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
