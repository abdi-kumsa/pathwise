import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getFormalInformal } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, RADIUS_V, stackGap, fmtPct } from '../../config/chartTheme'

export default function FormalInformalPage() {
  const { data, loading, error, refetch } = useFetch(getFormalInformal)
  const rows = data?.rows ?? []
  const years = [...new Set(rows.map(r => r.period))].sort()
  const stacked = years.map(period => {
    const slice = rows.filter(r => r.period === period)
    const n = slice.length || 1
    return {
      period,
      formal: slice.reduce((s, r) => s + Number(r.share_formal || 0), 0) / n,
      informal: slice.reduce((s, r) => s + Number(r.share_informal || 0), 0) / n,
      self_employment: slice.reduce((s, r) => s + Number(r.share_self_employment || 0), 0) / n,
      underemployment: slice.reduce((s, r) => s + Number(r.share_underemployment || 0), 0) / n,
    }
  })

  return (
    <div>
      <SectionHeader
        title="Formal vs informal absorption"
        subtitle="Formal wage, informal, self-employment and underemployment — shares sum to 1"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading absorption shares…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            {data.caveat} not_from_job_board: {String(data.not_from_job_board)}.
          </DataNote>
          {rows.length === 0 ? (
            <EmptyState title="No absorption rows" description="Formal, informal, self-employment and underemployment shares are empty." />
          ) : (
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">National share of employment type</p>
            <p className="panel-sub">Four adjacent series colours. Stacked composition, one scale.</p>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={stacked} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="period" {...axisProps} />
                <YAxis {...axisProps} domain={[0, 1]} tickFormatter={v => fmtPct(v * 100, 0)} />
                <Tooltip {...tooltipProps} formatter={v => fmtPct(v * 100, 1)} />
                <Legend />
                <Bar dataKey="formal" name="Formal wage" stackId="s" fill={SERIES[0]} radius={0} {...stackGap} />
                <Bar dataKey="informal" name="Informal" stackId="s" fill={SERIES[1]} {...stackGap} />
                <Bar dataKey="self_employment" name="Self-employment" stackId="s" fill={SERIES[2]} {...stackGap} />
                <Bar dataKey="underemployment" name="Underemployment" stackId="s" fill={SERIES[3]} radius={RADIUS_V} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          )}
        </>
      )}
    </div>
  )
}
