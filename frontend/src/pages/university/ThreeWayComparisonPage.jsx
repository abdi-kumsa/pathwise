import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getDemandVsLabour } from '../../api/roles'
import { SERIES_ALL_PAIRS, STATUS, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

const SERIES_KEYS = [
  { key: 'student_demand', label: 'Student demand', color: SERIES_ALL_PAIRS[0] },
  { key: 'expected_graduates', label: 'Expected graduates', color: SERIES_ALL_PAIRS[1] },
  { key: 'labour_demand', label: 'Labour demand', color: SERIES_ALL_PAIRS[2] },
]

export default function ThreeWayComparisonPage() {
  const { data, loading, error, refetch } = useFetch(getDemandVsLabour)
  const rows = data?.rows ?? []

  return (
    <div>
      <SectionHeader
        title="Demand vs labour"
        subtitle="Student demand, expected graduates and labour demand — three series, not two"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading three-way comparison…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Applications, graduate supply and labour demand side by side: planning on popularity alone misses the other two.
          </DataNote>
          <ForecastAccuracyNote />
          {rows.length === 0 && (
            <EmptyState title="No field rows" description="Three-way comparison is empty for this institution." />
          )}
          {rows.length > 0 && (
            <div className="panel" style={{ marginTop: 16 }}>
              <p className="panel-title">Exactly three series</p>
              <p className="panel-sub">{(data.series || SERIES_KEYS.map(s => s.key)).join(' · ')}</p>
              <ResponsiveContainer width="100%" height={360}>
                <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtNum} />
                  <Tooltip {...tooltipProps} />
                  <Legend />
                  {SERIES_KEYS.map(s => (
                    <Bar key={s.key} dataKey={s.key} name={s.label} fill={s.color} radius={[4, 4, 0, 0]} />
                  ))}
                </BarChart>
              </ResponsiveContainer>
              <div style={{ marginTop: 12 }}>
                {rows.map(r => (
                  <div key={r.field} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                    <span>{r.field}</span>
                    <span style={{ color: r.status === 'shortage' ? STATUS.serious : r.status === 'oversupply' ? STATUS.warning : STATUS.good }}>
                      {r.status} · Q{r.severity}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
