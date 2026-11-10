import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EmptyState from '../../components/EmptyState'
import DataTable, { StatusWord } from '../../components/DataTable'
import { GAP_STATUS_COLOR } from '../../components/GapTable'
import useFetch from '../../hooks/useFetch'
import { getDemandVsLabour } from '../../api/roles'
import { SERIES_ALL_PAIRS, STATUS, axisProps, gridProps, tooltipProps, fmtCompact, fmtNum } from '../../config/chartTheme'

const SERIES_KEYS = [
  { key: 'student_demand', label: 'Student demand', color: SERIES_ALL_PAIRS[0] },
  { key: 'expected_graduates', label: 'Expected graduates', color: SERIES_ALL_PAIRS[1] },
  { key: 'labour_demand', label: 'Labour demand', color: SERIES_ALL_PAIRS[2] },
]

const COLUMNS = [
  { key: 'field', label: 'Field' },
  { key: 'student_demand', label: 'Student demand', align: 'right', render: r => fmtNum(Math.round(r.student_demand ?? 0)) },
  { key: 'expected_graduates', label: 'Expected graduates', align: 'right', render: r => fmtNum(Math.round(r.expected_graduates ?? 0)) },
  { key: 'labour_demand', label: 'Labour demand', align: 'right', render: r => fmtNum(Math.round(r.labour_demand ?? 0)) },
  { key: 'status', label: 'Status', render: r => <StatusWord status={r.status} color={GAP_STATUS_COLOR[r.status] ?? STATUS.warning} /> },
  { key: 'severity', label: 'Severity', align: 'right', render: r => (r.severity == null ? '—' : `Q${r.severity}`) },
]

export default function ThreeWayComparisonPage() {
  const { data, loading, error, refetch } = useFetch(getDemandVsLabour)
  const rows = data?.rows ?? []

  return (
    <div>
      <SectionHeader
        title="Do your programmes match jobs"
        subtitle="Student demand, expected graduates and labour demand by field"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading three-way comparison…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Applications, graduate supply and labour demand side by side: planning on popularity alone misses the other two.
          </DataNote>
          {rows.length === 0 && (
            <EmptyState title="No field rows" description="Three-way comparison is empty for this institution." />
          )}
          {rows.length > 0 && (
            <>
              <div className="panel" style={{ marginTop: 16 }}>
                <p className="panel-title">Student demand, graduates and labour demand</p>
                <p className="panel-sub">Headcounts on one scale</p>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtCompact} width={56} />
                    <Tooltip {...tooltipProps} formatter={v => fmtNum(Math.round(v))} />
                    <Legend />
                    {SERIES_KEYS.map(s => (
                      <Bar key={s.key} dataKey={s.key} name={s.label} fill={s.color} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                    ))}
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="panel" style={{ marginTop: 16 }}>
                <p className="panel-title">By field</p>
                <DataTable
                  columns={COLUMNS}
                  rows={rows}
                  rowKey="field"
                  defaultSort={{ key: 'severity', dir: 'desc' }}
                />
              </div>
            </>
          )}
          <ForecastAccuracyNote />
        </>
      )}
    </div>
  )
}
