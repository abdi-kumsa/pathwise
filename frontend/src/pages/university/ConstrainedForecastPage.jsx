import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import ForecastChart, { sumBy } from '../../components/ForecastChart'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getConstrainedDemand } from '../../api/roles'
import { SERIES, STATUS, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

const APPLICATIONS = 'Applications'
const ENROLMENT = 'Constrained enrolment'

export default function ConstrainedForecastPage() {
  const { data, loading, error, refetch } = useFetch(getConstrainedDemand)
  const rows = data?.rows ?? []
  const history = data?.history ?? []

  const byYear = sumBy(rows, 'academic_year',
    ['unconstrained_demand', 'constrained_enrollment', 'interval_low', 'interval_high'])
  const observed = sumBy(history, 'academic_year', ['applications', 'enrollment'])
  const series = [
    {
      key: APPLICATIONS,
      history: observed.map(h => ({ x: h.academic_year, y: h.applications })),
      forecast: byYear.map(r => ({
        x: r.academic_year, y: r.unconstrained_demand, low: r.interval_low, high: r.interval_high,
      })),
    },
    {
      key: ENROLMENT,
      history: observed.map(h => ({ x: h.academic_year, y: h.enrollment })),
      forecast: byYear.map(r => ({ x: r.academic_year, y: r.constrained_enrollment })),
    },
  ]

  const latest = byYear.length ? byYear[byYear.length - 1].academic_year : null
  const byProgram = rows
    .filter(r => r.academic_year === latest)
    .sort((a, b) => Number(b.unconstrained_demand || 0) - Number(a.unconstrained_demand || 0))
  const over = byYear.some(r => r.constrained_enrollment > r.unconstrained_demand + 0.5)

  return (
    <div>
      <SectionHeader
        title="How many you can enrol"
        subtitle="Intake after exam, placement, quota and capacity rules, shown against the applications behind it"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading constrained forecast…" height={280} />}
      {data && rows.length === 0 && (
        <EmptyState title="No constrained rows" description="The constraint layer returned no programmes for this institution." />
      )}
      {data && rows.length > 0 && (
        <>
          {over && (
            <DataNote tone="caution">Constrained total exceeded unconstrained demand; inspect the constraint layer.</DataNote>
          )}
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Applications and constrained enrolment</p>
            <p className="panel-sub">Both are headcounts; constrained enrolment can never exceed applications</p>
            <ForecastChart
              series={series}
              defaultFocus={ENROLMENT}
              height={300}
              caption="The 90% range belongs to the applications forecast; the constraint layer is a rule set, not an estimate."
            />
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Binding constraint by programme · {latest}</p>
            <p className="panel-sub">Which rule removed the last seat in each programme</p>
            <ResponsiveContainer width="100%" height={Math.max(240, 32 * byProgram.length + 60)}>
              <BarChart data={byProgram} layout="vertical" margin={{ left: 8, right: 24 }}>
                <CartesianGrid {...gridProps} />
                <XAxis type="number" {...axisProps} tickFormatter={fmtNum} />
                <YAxis type="category" dataKey="program" width={150} {...axisProps} />
                <Tooltip {...tooltipProps} formatter={v => fmtNum(v)} />
                <Legend />
                <Bar dataKey="unconstrained_demand" name="Applications" fill={SERIES[0]} radius={[0, 4, 4, 0]} />
                <Bar dataKey="constrained_enrollment" name="Constrained enrolment" fill={SERIES[1]} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
            {byProgram.map(r => (
              <div key={r.program} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
                <span>{r.program}</span>
                <span style={{ color: r.binding_constraint && r.binding_constraint !== 'none' ? STATUS.serious : STATUS.good }}>
                  {r.binding_constraint || 'none'}
                </span>
              </div>
            ))}
          </div>
          <ForecastAccuracyNote accuracy={data.accuracy} />
        </>
      )}
    </div>
  )
}
