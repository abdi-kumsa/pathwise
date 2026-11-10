import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EmptyState from '../../components/EmptyState'
import GapTable, { GAP_STATUS_COLOR } from '../../components/GapTable'
import useFetch from '../../hooks/useFetch'
import { getSupplyDemandGap } from '../../api/student'
import { SERIES, STATUS, axisProps, gridProps, tooltipProps, fmtCompact, fmtNum } from '../../config/chartTheme'

export default function SupplyDemandGapPage() {
  const { data, loading, error, refetch } = useFetch(getSupplyDemandGap)
  const rows = (data?.rows ?? []).map(r => ({ ...r, gap: Number(r.signed_gap) || 0 }))
  const own = rows.find(r => r.is_own_field)

  return (
    <div>
      <SectionHeader
        title="Shortage or oversupply, by field"
        subtitle={own
          ? `${own.field} is in ${own.status}: expected graduates against projected labour demand`
          : 'Expected graduates against projected labour demand'}
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading gap…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Status follows coverage (graduates ÷ demand): below 0.85 is a shortage, above 1.15 an oversupply, in between balanced. Severity Q1–Q4 ranks the size of the gap against the other fields.
            {data.field ? ` Your field (${data.field}) is highlighted.` : ''}
          </DataNote>
          {rows.length === 0 && (
            <EmptyState title="No gap rows" description="Expected graduates versus vacancies is empty for this slice." />
          )}
          {rows.length > 0 && (
            <>
              <div className="panel" style={{ marginTop: 16 }}>
                <p className="panel-title">Labour demand minus expected graduates</p>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtCompact} width={56} />
                    <Tooltip {...tooltipProps} formatter={v => [fmtNum(Math.round(v)), 'Labour demand − graduates']} />
                    <Bar dataKey="gap" name="Labour demand − graduates" isAnimationActive={false}>
                      {rows.map(r => (
                        <Cell key={r.field} fill={r.is_own_field ? SERIES[0] : (GAP_STATUS_COLOR[r.status] || STATUS.warning)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="panel" style={{ marginTop: 16 }}>
                <p className="panel-title">By field</p>
                <p className="panel-sub">Your field is in bold</p>
                <GapTable
                  rows={rows}
                  trendYears={data.trend_years}
                  renderField={r => `${r.field}${r.is_own_field ? ' · your field' : ''}`}
                  rowProps={r => ({
                    'data-testid': r.is_own_field ? 'own-field' : 'gap-row',
                    className: r.is_own_field ? 'own' : undefined,
                  })}
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
