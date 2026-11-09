import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getSupplyDemandGap } from '../../api/student'
import { SERIES, STATUS, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

const STATUS_COLOR = {
  shortage: STATUS.serious,
  balanced: STATUS.good,
  oversupply: STATUS.warning,
}

export default function SupplyDemandGapPage() {
  const { data, loading, error, refetch } = useFetch(getSupplyDemandGap)
  const rows = (data?.rows ?? []).map(r => ({
    ...r,
    gap: Number(r.signed_gap) || 0,
  }))

  return (
    <div>
      <SectionHeader
        title="Graduate supply–demand gap"
        subtitle="Expected graduates versus projected labour demand. Severity is a quartile of |gap|, not a fixed coverage cut."
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading gap…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Status follows coverage (graduates ÷ demand): below 0.85 is a shortage, above 1.15 an oversupply, in between balanced. Severity Q1–Q4 ranks the size of the gap against the other fields.
            {data.field ? ` Your field (${data.field}) is highlighted.` : ''}
          </DataNote>
          <ForecastAccuracyNote />
          {rows.length === 0 && (
            <EmptyState title="No gap rows" description="Expected graduates versus vacancies is empty for this slice." />
          )}
          {rows.length > 0 && (
            <>
              <div className="panel" style={{ marginTop: 16 }}>
                <ResponsiveContainer width="100%" height={340}>
                  <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtNum} />
                    <Tooltip {...tooltipProps} />
                    <Bar dataKey="gap" name="Labour − graduates">
                      {rows.map(r => (
                        <Cell key={r.field} fill={r.is_own_field ? SERIES[0] : (STATUS_COLOR[r.status] || STATUS.warning)} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="panel" style={{ marginTop: 16 }}>
                {rows.map(r => (
                  <div
                    key={r.field}
                    data-testid={r.is_own_field ? 'own-field' : 'gap-row'}
                    style={{
                      display: 'flex', justifyContent: 'space-between', padding: '8px 0',
                      borderBottom: '1px solid var(--border)',
                      fontWeight: r.is_own_field ? 700 : 400,
                    }}
                  >
                    <span>{r.field}{r.is_own_field ? ' · your field' : ''}</span>
                    <span>
                      <strong>{r.status}</strong> · severity Q{r.severity}
                    </span>
                  </div>
                ))}
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
