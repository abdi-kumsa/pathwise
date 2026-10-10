import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getDemandComparison } from '../../api/student'
import { SERIES, SERIES_ALL_PAIRS, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function DemandComparisonPage() {
  const { data, loading, error, refetch } = useFetch(getDemandComparison)
  const rows = data?.rows ?? []

  return (
    <div>
      <SectionHeader
        title="Student demand vs market demand"
        subtitle="Where popularity and employment opportunity diverge"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading comparison…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">{data.note}</DataNote>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Two measures, two charts would be used if the scales fought. Here they share a count scale.</p>
            <ResponsiveContainer width="100%" height={360}>
              <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                <YAxis {...axisProps} tickFormatter={fmtNum} />
                <Tooltip {...tooltipProps} />
                <Bar dataKey="student_demand" name="Student demand" fill={SERIES_ALL_PAIRS[0]} radius={[4, 4, 0, 0]} />
                <Bar dataKey="labour_demand" name="Labour demand" fill={SERIES_ALL_PAIRS[1]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Divergence (student − labour)</p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={rows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="field" interval={0} angle={-28} textAnchor="end" height={70} {...axisProps} />
                <YAxis {...axisProps} tickFormatter={fmtNum} />
                <Tooltip {...tooltipProps} />
                <Bar dataKey="divergence" name="Divergence">
                  {rows.map((r) => (
                    <Cell key={r.field} fill={r.is_own_field ? SERIES[2] : SERIES[0]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}
