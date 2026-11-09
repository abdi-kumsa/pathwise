import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getCohortProgression } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtPct } from '../../config/chartTheme'

export default function CohortProgressionPage() {
  const { data, loading, error, refetch } = useFetch(getCohortProgression)
  const rows = data?.rows ?? []
  const years = [...new Set(rows.map(r => r.year))].sort()
  const latest = years[years.length - 1]
  const byProgram = rows
    .filter(r => r.year === latest)
    .map(r => ({
      program: r.program,
      retention: Number(r.retention_rate_pct || 0),
      dropout: Number(r.dropout_rate_pct || 0),
      transfer: Number(r.transfer_rate_pct || 0),
      completion: Number(r.completion_rate_pct || 0),
    }))

  return (
    <div>
      <SectionHeader
        title="Who progresses, who repeats"
        subtitle="Retention, dropout, transfer and completion by programme (M1.C6)"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading cohorts…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Latest year shown: {latest ?? '—'}. Rates are simulated SIS structure, not a live registrar extract.
          </DataNote>
          {byProgram.length === 0 && (
            <EmptyState title="No cohort rows" description="Cohort progression is empty for this institution." />
          )}
          {byProgram.length > 0 && (
            <div className="panel" style={{ marginTop: 16 }} data-testid="cohort-flow">
              <p className="panel-title">Cohort flow by programme · {latest}</p>
              <p className="panel-sub">Stacked retention → dropout → transfer → completion (not separate grouped bars).</p>
              <ResponsiveContainer width="100%" height={380}>
                <BarChart data={byProgram} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="program" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={v => `${v}%`} />
                  <Tooltip {...tooltipProps} formatter={v => fmtPct(v, 1)} />
                  <Legend />
                  <Bar dataKey="retention" name="Retention" stackId="cohort" fill={SERIES[0]} />
                  <Bar dataKey="dropout" name="Dropout" stackId="cohort" fill={SERIES[1]} />
                  <Bar dataKey="transfer" name="Transfer" stackId="cohort" fill={SERIES[2]} />
                  <Bar dataKey="completion" name="Completion" stackId="cohort" fill={SERIES[3]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </>
      )}
    </div>
  )
}
