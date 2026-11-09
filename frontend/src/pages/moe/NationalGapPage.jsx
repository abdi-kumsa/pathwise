import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import useFetch from '../../hooks/useFetch'
import { getEducationGap } from '../../api/roles'
import { STATUS, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

const STATUS_COLOR = {
  shortage: STATUS.serious,
  balanced: STATUS.good,
  oversupply: STATUS.warning,
}

export default function NationalGapPage() {
  const { data, loading, error, refetch } = useFetch(getEducationGap)
  const rows = (data?.rows ?? []).map(r => ({
    ...r,
    gap: Number(r.signed_gap) || 0,
  }))

  return (
    <div>
      <SectionHeader
        title="National field supply–demand gap"
        subtitle="Expected graduates versus projected labour demand. Severity is a quartile of |gap|."
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading national gap…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Shortage, balanced and oversupply are labelled in text as well as colour. Status follows coverage (graduates ÷ demand): below 0.85 is a shortage, above 1.15 an oversupply, in between balanced. Severity Q1–Q4 ranks the size of the gap against the other fields. This is the Model 3 national gap, not the US-compat labour gap.
          </DataNote>
          <ForecastAccuracyNote />
          <div className="panel" style={{ marginTop: 16 }}>
            <ResponsiveContainer width="100%" height={340}>
              <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                <YAxis {...axisProps} tickFormatter={fmtNum} />
                <Tooltip {...tooltipProps} />
                <Bar dataKey="gap" name="Labour − graduates">
                  {rows.map(r => (
                    <Cell key={r.field} fill={STATUS_COLOR[r.status] || STATUS.warning} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            {rows.map(r => (
              <div key={r.field} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span>{r.field}</span>
                <span>
                  <strong>{r.status}</strong> · severity Q{r.severity}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
