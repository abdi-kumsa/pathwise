import DataTable, { StatusWord } from './DataTable'
import Sparkline from './Sparkline'
import { STATUS, fmtNum, fmtPct } from '../config/chartTheme'

/** Gap status → colour. The word is always shown; the colour only repeats it. */
export const GAP_STATUS_COLOR = {
  shortage: STATUS.serious,
  balanced: STATUS.good,
  oversupply: STATUS.warning,
  'no modelled institution': '#CBD5E1',
}

// A region with no modelled university has no supply to judge.
const unmodelled = r => !Number(r.expected_graduates) && !Number(r.enrollment) && r.enrollment !== undefined

/**
 * One row per field from the Model 3 gap: enrolment trend, expected graduates,
 * labour demand, coverage, status in words, severity quartile. Shared by the
 * national (MoE), regional and student gap pages so they read the same way.
 */
export default function GapTable({ rows, trendYears, renderField, rowProps, caption }) {
  const span = trendYears?.length ? `${trendYears[0]}–${trendYears[trendYears.length - 1]}` : ''
  const columns = [
    { key: 'field', label: 'Field', render: renderField ?? (r => r.field) },
    {
      key: 'trend', label: span ? `Enrolment ${span}` : 'Enrolment trend', sortable: false,
      render: r => <Sparkline values={r.trend ?? []} />,
    },
    { key: 'expected_graduates', label: 'Expected graduates', align: 'right', render: r => fmtNum(Math.round(r.expected_graduates ?? 0)) },
    { key: 'labour_demand', label: 'Labour demand', align: 'right', render: r => fmtNum(Math.round(r.labour_demand ?? 0)) },
    {
      key: 'coverage_pct', label: 'Coverage', align: 'right', title: 'Expected graduates as a share of labour demand',
      render: r => (r.coverage_pct == null || unmodelled(r) ? '—' : fmtPct(r.coverage_pct, 0)),
    },
    {
      key: 'status', label: 'Status',
      render: r => {
        const st = unmodelled(r) ? 'no modelled institution' : r.status
        return <StatusWord status={st} color={GAP_STATUS_COLOR[st] ?? STATUS.warning} />
      },
    },
    {
      key: 'severity', label: 'Severity', align: 'right', title: 'Quartile of the absolute gap across fields; Q4 is the largest',
      render: r => (r.severity == null ? '—' : `Q${r.severity}`),
    },
  ]
  return (
    <DataTable
      columns={columns}
      rows={rows}
      rowKey="field"
      defaultSort={{ key: 'severity', dir: 'desc' }}
      rowProps={rowProps}
      caption={caption}
      emptyText="No fields in this slice"
    />
  )
}
