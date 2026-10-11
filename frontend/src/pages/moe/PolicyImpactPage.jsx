import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getPolicyImpact } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum, fmtPct } from '../../config/chartTheme'

export default function PolicyImpactPage() {
  const { data, loading, error, refetch } = useFetch(getPolicyImpact)
  const series = data?.series ?? []

  return (
    <div>
      <SectionHeader
        title="Policy impact monitoring"
        subtitle="Simulated quota and capacity against subsequent enrolment and employment"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading policy impact…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            {data.note} official_forecast: {String(data.official_forecast)}. Not a real MoE circular.
          </DataNote>
          <div className="card-grid-2" style={{ marginTop: 16 }}>
            <div className="panel">
              <p className="panel-title">Quota, capacity and enrolment</p>
              <p className="panel-sub">Counts on one scale — not a dual axis</p>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={series} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtNum} />
                  <Tooltip {...tooltipProps} />
                  <Legend />
                  <Line type="monotone" dataKey="approved_intake_quota" name="Quota" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="program_capacity" name="Capacity" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="enrollment" name="Enrolment" stroke={SERIES[2]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="panel">
              <p className="panel-title">Graduate employment rate</p>
              <p className="panel-sub">Separate chart because the unit is a percentage</p>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={series} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={v => `${v}%`} />
                  <Tooltip {...tooltipProps} formatter={v => fmtPct(v, 1)} />
                  <Line type="monotone" dataKey="employment_rate_pct" name="Employment" stroke={SERIES[3]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
