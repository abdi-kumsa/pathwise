import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getDemandConstrainedComparison } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function ConstraintComparisonPage() {
  const { data, loading, error, refetch } = useFetch(getDemandConstrainedComparison)
  const rows = data?.rows ?? []
  const years = [...new Set(rows.map(r => r.academic_year))].sort()
  const byYear = years.map(year => {
    const slice = rows.filter(r => r.academic_year === year)
    return {
      academic_year: year,
      unconstrained: slice.reduce((s, r) => s + Number(r.unconstrained || 0), 0),
      constrained: slice.reduce((s, r) => s + Number(r.constrained_enrollment || 0), 0),
    }
  })
  const latest = years[years.length - 1]
  const latestRows = rows
    .filter(r => r.academic_year === latest)
    .sort((a, b) => Number(b.unconstrained || 0) - Number(a.unconstrained || 0))
  const over = byYear.some(r => r.constrained > r.unconstrained + 0.5)

  return (
    <div>
      <SectionHeader
        title="Unconstrained vs constrained demand"
        subtitle="National student demand compared with policy- and capacity-constrained enrolment"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading comparison…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Two series on one scale. Constrained enrolment is at most unconstrained demand. Binding constraint is named when the loss is on the constraint side.
          </DataNote>
          {over && (
            <DataNote tone="caution">Constrained total exceeded unconstrained — inspect the constraint layer.</DataNote>
          )}
          {rows.length === 0 && (
            <EmptyState title="No comparison rows" description="Model 1 returned no national field series." />
          )}
          {rows.length > 0 && (
            <>
              <div className="panel" style={{ marginTop: 16 }}>
                <p className="panel-title">National scenario comparison</p>
                <p className="panel-sub">One axis — both series are headcount</p>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={byYear} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="academic_year" {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtNum} />
                    <Tooltip {...tooltipProps} />
                    <Legend />
                    <Line type="monotone" dataKey="unconstrained" name="Unconstrained" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="constrained" name="Constrained" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <div className="panel" style={{ marginTop: 16 }}>
                <p className="panel-title">By field · {latest}</p>
                <ResponsiveContainer width="100%" height={320}>
                  <BarChart data={latestRows} layout="vertical" margin={{ left: 8, right: 12 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis type="number" {...axisProps} tickFormatter={fmtNum} />
                    <YAxis type="category" dataKey="field" width={170} {...axisProps} />
                    <Tooltip {...tooltipProps} />
                    <Bar dataKey="unconstrained" name="Unconstrained" fill={SERIES[0]} radius={[0, 6, 6, 0]} />
                    <Bar dataKey="constrained_enrollment" name="Constrained" fill={SERIES[1]} radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                <div className="table-scroll" style={{ marginTop: 12 }}>
                  <table>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left' }}>Field</th>
                        <th>Unconstrained</th>
                        <th>Constrained</th>
                        <th>Binding constraint</th>
                      </tr>
                    </thead>
                    <tbody>
                      {latestRows.map(r => (
                        <tr key={r.field}>
                          <td style={{ textAlign: 'left' }}>{r.field}</td>
                          <td className="num">{fmtNum(r.unconstrained)}</td>
                          <td className="num">{fmtNum(r.constrained_enrollment)}</td>
                          <td>{Number(r.constraint_loss) > 0 ? (r.binding_constraint || 'none') : 'none'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </>
      )}
      <style>{`
        .table-scroll th { text-align: right; padding: 8px 12px; font-size: 11px; color: var(--text-muted); border-bottom: 1px solid var(--border); }
        .table-scroll td { padding: 9px 12px; text-align: right; border-bottom: 1px solid #F4F6FA; }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
