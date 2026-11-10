import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import GapTable, { GAP_STATUS_COLOR } from '../../components/GapTable'
import useFetch from '../../hooks/useFetch'
import { getEducationGap } from '../../api/roles'
import { STATUS, axisProps, gridProps, tooltipProps, fmtCompact, fmtNum } from '../../config/chartTheme'

export default function NationalGapPage() {
  const { data, loading, error, refetch } = useFetch(getEducationGap)
  const rows = (data?.rows ?? []).map(r => ({ ...r, gap: Number(r.signed_gap) || 0 }))
  const shortages = rows.filter(r => r.status === 'shortage').length
  const oversupplied = rows.filter(r => r.status === 'oversupply').length

  return (
    <div>
      <SectionHeader
        title="Where demand outruns graduates"
        subtitle="National expected graduates against projected labour demand, by field"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading national gap…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Status follows coverage (graduates ÷ demand): below 0.85 is a shortage, above 1.15 an oversupply, in between balanced. Severity Q1–Q4 ranks the size of the gap against the other fields.
          </DataNote>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Labour demand minus expected graduates</p>
            <p className="panel-sub">
              {shortages} {shortages === 1 ? 'field' : 'fields'} in shortage, {oversupplied} in oversupply, {rows.length - shortages - oversupplied} balanced
            </p>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                <YAxis {...axisProps} tickFormatter={fmtCompact} width={56} />
                <Tooltip {...tooltipProps} formatter={v => [fmtNum(Math.round(v)), 'Labour demand − graduates']} />
                <Bar dataKey="gap" name="Labour demand − graduates" isAnimationActive={false}>
                  {rows.map(r => (
                    <Cell key={r.field} fill={GAP_STATUS_COLOR[r.status] || STATUS.warning} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">By field</p>
            <p className="panel-sub">Sorted by severity; click a heading to sort by another column</p>
            <GapTable rows={rows} trendYears={data.trend_years} />
          </div>
          <ForecastAccuracyNote />
        </>
      )}
    </div>
  )
}
