import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import DataTable from '../../components/DataTable'
import useFetch from '../../hooks/useFetch'
import { getMigration } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtCompact, fmtNum } from '../../config/chartTheme'

const COLUMNS = [
  { key: 'region', label: 'Region of origin' },
  { key: 'skilled_emigration_count', label: 'Skilled emigration', align: 'right', render: r => fmtNum(r.skilled_emigration_count) },
  { key: 'return_migration_count', label: 'Return migration', align: 'right', render: r => fmtNum(r.return_migration_count) },
  {
    key: 'net', label: 'Net outflow', align: 'right', title: 'Skilled emigration minus return migration',
    sortValue: r => Number(r.skilled_emigration_count || 0) - Number(r.return_migration_count || 0),
    render: r => fmtNum(Number(r.skilled_emigration_count || 0) - Number(r.return_migration_count || 0)),
  },
]

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
  const latestYear = years[years.length - 1]

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
          <DataNote tone="simulated">{data.note || 'Simulated migration series. Shown as unavailable rather than invented where there is no coverage.'}</DataNote>
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
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={national} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="year" {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtCompact} width={56} />
                    <Tooltip {...tooltipProps} formatter={v => fmtNum(v)} />
                    <Legend />
                    <Line type="monotone" dataKey="skilled_emigration_count" name="Skilled emigration" stroke={SERIES[0]} strokeWidth={2} dot={false} isAnimationActive={false} />
                    <Line type="monotone" dataKey="return_migration_count" name="Return migration" stroke={SERIES[1]} strokeWidth={2} dot={false} isAnimationActive={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="panel" style={{ marginTop: 16 }} data-testid="migration-flow">
                <p className="panel-title">By region{latestYear ? ` · ${latestYear}` : ''}</p>
                <p className="panel-sub">
                  No origin–destination matrix exists: region is the origin, emigration goes abroad and return arrives back in the same region.
                </p>
                <DataTable
                  columns={COLUMNS}
                  rows={data.rows || []}
                  rowKey={(r, i) => r.region ?? i}
                  defaultSort={{ key: 'skilled_emigration_count', dir: 'desc' }}
                  emptyText="No regional rows"
                />
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
