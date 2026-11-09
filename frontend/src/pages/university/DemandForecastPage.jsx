import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getUnconstrainedDemand } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function DemandForecastPage() {
  const { data, loading, error, refetch } = useFetch(getUnconstrainedDemand)
  const rows = data?.rows ?? []
  const years = [...new Set(rows.map(r => r.academic_year))].sort()
  const byYear = years.map(year => ({
    academic_year: year,
    unconstrained_demand: rows
      .filter(r => r.academic_year === year)
      .reduce((s, r) => s + Number(r.unconstrained_demand || 0), 0),
  }))
  const latest = years[years.length - 1]
  const byProgram = rows
    .filter(r => r.academic_year === latest)
    .sort((a, b) => Number(b.unconstrained_demand || 0) - Number(a.unconstrained_demand || 0))

  return (
    <div>
      <SectionHeader
        title="Unconstrained student demand"
        subtitle="Likely applications and programme preference before quota, exam and capacity caps"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading unconstrained demand…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Layer {data.layer || 'M1.L1'}. Horizon {data.horizon} years. JWT-scoped to this institution.
          </DataNote>
          <ForecastAccuracyNote />
          {rows.length === 0 && (
            <EmptyState title="No forecast rows" description="Unconstrained demand is empty for this institution." />
          )}
          {rows.length > 0 && (
            <div className="card-grid-2" style={{ marginTop: 16 }}>
              <div className="panel">
                <p className="panel-title">Demand by year</p>
                <p className="panel-sub">Sum of unconstrained applications across programmes</p>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={byYear} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="academic_year" {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtNum} />
                    <Tooltip {...tooltipProps} />
                    <Line type="monotone" dataKey="unconstrained_demand" name="Unconstrained" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="panel">
                <p className="panel-title">Programme preference · {latest}</p>
                <p className="panel-sub">Before caps — popularity, not a placement guarantee</p>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={byProgram} layout="vertical" margin={{ left: 8, right: 12 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis type="number" {...axisProps} tickFormatter={fmtNum} />
                    <YAxis type="category" dataKey="program" width={140} {...axisProps} />
                    <Tooltip {...tooltipProps} />
                    <Bar dataKey="unconstrained_demand" name="Unconstrained" fill={SERIES[0]} radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
