import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getGraduateOutcomes } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum, fmtPct } from '../../config/chartTheme'

export default function GraduateOutcomesPage() {
  const { data, loading, error, refetch } = useFetch(getGraduateOutcomes)
  const rows = data?.rows ?? []
  const cohort = data?.cohort ?? []
  const years = [...new Set(rows.map(r => r.year))].sort()
  const employment = years.map(year => {
    const slice = rows.filter(r => r.year === year)
    const mean = slice.length
      ? slice.reduce((s, r) => s + Number(r.graduate_employment_rate_pct || 0), 0) / slice.length
      : 0
    const earn = slice.length
      ? slice.reduce((s, r) => s + Number(r.median_earnings_etb || 0), 0) / slice.length
      : 0
    return { year, employment: mean, earnings: earn }
  })
  const latestCohortYear = [...new Set(cohort.map(r => r.year))].sort().at(-1)
  const timeToGrad = cohort
    .filter(r => r.year === latestCohortYear)
    .map(r => ({
      program: r.program,
      years: Number(r.time_to_graduation_years || 0),
    }))
  const timeToEmployment = data?.time_to_employment ?? []

  return (
    <div>
      <SectionHeader
        title="Graduate outcomes"
        subtitle="Employment, earnings and time-to-graduation for prior cohorts — not fit classification"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading outcomes…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Fit classification is not plotted here. Employment and earnings are lagged field outcomes (M1.C7). Time-to-graduation stays labelled as graduation. Time-to-employment is the six-month employment share — not graduation years.
          </DataNote>
          {rows.length === 0 && (
            <EmptyState title="No outcome rows" description="Graduate tracking is empty for this institution." />
          )}
          {rows.length > 0 && (
            <div className="card-grid-2" style={{ marginTop: 16 }}>
              <div className="panel">
                <p className="panel-title">Employment rate</p>
                <p className="panel-sub">Mean across fields by year</p>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={employment} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="year" {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={v => `${v}%`} />
                    <Tooltip {...tooltipProps} formatter={v => fmtPct(v, 1)} />
                    <Line type="monotone" dataKey="employment" name="Employment" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="panel">
                <p className="panel-title">Median earnings (ETB)</p>
                <p className="panel-sub">Median graduate earnings by year</p>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={employment} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="year" {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtNum} />
                    <Tooltip {...tooltipProps} />
                    <Line type="monotone" dataKey="earnings" name="Median earnings" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
          {timeToEmployment.length > 0 && (
            <div className="panel" style={{ marginTop: 16 }} data-testid="time-to-employment">
              <p className="panel-title">Time to employment</p>
              <p className="panel-sub">{data.time_to_employment_note || 'Share employed within six months. Not time-to-graduation.'}</p>
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={timeToEmployment} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={v => `${v}%`} />
                  <Tooltip {...tooltipProps} formatter={v => fmtPct(v, 1)} />
                  <Line type="monotone" dataKey="employed_within_6mo_pct" name="Employed ≤ 6 months" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
          {timeToGrad.length > 0 && (
            <div className="panel" style={{ marginTop: 16 }}>
              <p className="panel-title">Time to graduation · {latestCohortYear}</p>
              <p className="panel-sub">Years to graduation from the cohort table — not employment.</p>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={timeToGrad} layout="vertical" margin={{ left: 8, right: 12 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis type="number" {...axisProps} />
                  <YAxis type="category" dataKey="program" width={140} {...axisProps} />
                  <Tooltip {...tooltipProps} />
                  <Legend />
                  <Bar dataKey="years" name="Years to graduation" fill={SERIES[2]} radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}
