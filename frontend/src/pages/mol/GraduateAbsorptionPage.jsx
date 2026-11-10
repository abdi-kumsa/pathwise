import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getGraduateAbsorption } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtPct } from '../../config/chartTheme'

export default function GraduateAbsorptionPage() {
  const { data, loading, error, refetch } = useFetch(getGraduateAbsorption)
  const series = data?.series ?? []

  return (
    <div>
      <SectionHeader
        title="How fast graduates find work"
        subtitle="Time-to-employment and employment type after graduation — aggregate only"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading absorption…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            {data.note} Fit classification is not used.
          </DataNote>
          {series.length === 0 ? (
            <EmptyState title="No absorption series" description="Time-to-employment rows are empty." />
          ) : (
          <div className="card-grid-2" style={{ marginTop: 16 }}>
            <div className="panel">
              <p className="panel-title">Time-to-employment (share employed within 6 months)</p>
              <p className="panel-sub">Six-month employment proxy — not time-to-graduation.</p>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={series} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={v => `${v}%`} />
                  <Tooltip {...tooltipProps} formatter={v => fmtPct(v, 1)} />
                  <Legend />
                  <Line type="monotone" dataKey="employed_within_6mo_pct" name="Employed ≤ 6 months" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="employment_rate_pct" name="Employment rate" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="panel">
              <p className="panel-title">Employment type shares</p>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={series} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} domain={[0, 1]} tickFormatter={v => fmtPct(v * 100, 0)} />
                  <Tooltip {...tooltipProps} formatter={v => fmtPct(v * 100, 1)} />
                  <Legend />
                  <Line type="monotone" dataKey="share_formal" name="Formal" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="share_informal" name="Informal" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="share_self_employment" name="Self-employment" stroke={SERIES[2]} strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="share_underemployment" name="Underemployment" stroke={SERIES[3]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          )}
        </>
      )}
    </div>
  )
}
