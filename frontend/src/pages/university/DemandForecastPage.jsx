import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import ForecastChart, { sumBy } from '../../components/ForecastChart'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getUnconstrainedDemand } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function DemandForecastPage() {
  const { data, loading, error, refetch } = useFetch(getUnconstrainedDemand)
  const rows = data?.rows ?? []
  const history = data?.history ?? []

  const byYear = sumBy(rows, 'academic_year', ['unconstrained_demand', 'interval_low', 'interval_high'])
  const observed = sumBy(history, 'academic_year', ['applications'])
  const series = [{
    key: 'Applications',
    history: observed.map(h => ({ x: h.academic_year, y: h.applications })),
    forecast: byYear.map(r => ({
      x: r.academic_year, y: r.unconstrained_demand, low: r.interval_low, high: r.interval_high,
    })),
  }]

  const latest = byYear.length ? byYear[byYear.length - 1].academic_year : null
  const byProgram = rows
    .filter(r => r.academic_year === latest)
    .sort((a, b) => Number(b.unconstrained_demand || 0) - Number(a.unconstrained_demand || 0))

  return (
    <div>
      <SectionHeader
        title="How many will apply"
        subtitle="Applications this institution would receive before quota, exam and capacity caps"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading unconstrained demand…" height={280} />}
      {data && rows.length === 0 && (
        <EmptyState title="No forecast rows" description="Unconstrained demand is empty for this institution." />
      )}
      {data && rows.length > 0 && (
        <>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Applications by year</p>
            <p className="panel-sub">All programmes at this institution</p>
            <ForecastChart
              series={series}
              height={300}
              unit="applications"
              caption="The range for the total is the sum of the per-programme ranges, which is conservative."
            />
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Programme preference · {latest}</p>
            <p className="panel-sub">Forecast applications before caps: popularity, not a placement guarantee</p>
            <ResponsiveContainer width="100%" height={Math.max(220, 28 * byProgram.length + 40)}>
              <BarChart data={byProgram} layout="vertical" margin={{ left: 8, right: 24 }}>
                <CartesianGrid {...gridProps} />
                <XAxis type="number" {...axisProps} tickFormatter={fmtNum} />
                <YAxis type="category" dataKey="program" width={150} {...axisProps} />
                <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), 'Applications']} />
                <Bar dataKey="unconstrained_demand" name="Applications" fill={SERIES[0]} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ForecastAccuracyNote accuracy={data.accuracy} />
        </>
      )}
    </div>
  )
}
