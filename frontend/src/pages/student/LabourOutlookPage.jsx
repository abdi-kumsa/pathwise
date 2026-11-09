import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getLabourOutlook } from '../../api/student'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function LabourOutlookPage() {
  const { data, loading, error, refetch } = useFetch(getLabourOutlook)
  const h3 = data?.series?.['3'] ?? []
  const h5 = data?.series?.['5'] ?? []
  const merged = h5.map(row => {
    const three = h3.find(s => s.period === row.period)
    return { period: row.period, y3: three?.vacancies ?? null, y5: row.vacancies }
  })
  const occupations = data?.occupations ?? []

  return (
    <div>
      <SectionHeader
        title="Labour-market outlook"
        subtitle={data?.field ? `3- and 5-year vacancy outlook for ${data.field}` : 'Projected occupational demand'}
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading outlook…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">{data.note}</DataNote>
          <ForecastAccuracyNote />
          {data.cell_withheld && (
            <DataNote tone="caution">
              Occupation cells smaller than {data.min_cell_size ?? 5} are withheld
              (n &lt; {data.min_cell_size ?? 5}). The vacancy series is still shown.
            </DataNote>
          )}
          <div className="card-grid-2" style={{ marginTop: 16 }}>
            <div className="panel">
              <p className="panel-title">Vacancy forecast</p>
              <p className="panel-sub">Two horizons, two lines — not a dual axis.</p>
              {merged.length === 0 ? (
                <EmptyState title="No vacancy series" description="No 3- or 5-year outlook rows for this field." />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={merged} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis dataKey="period" {...axisProps} />
                    <YAxis {...axisProps} tickFormatter={fmtNum} />
                    <Tooltip {...tooltipProps} />
                    <Line type="monotone" dataKey="y3" name="3-year path" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                    <Line type="monotone" dataKey="y5" name="5-year path" stroke={SERIES[1]} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="panel">
              <p className="panel-title">Related occupations</p>
              {occupations.length === 0 ? (
                <EmptyState
                  title={data.cell_withheld ? 'Occupations withheld' : 'No occupations'}
                  description={
                    data.cell_withheld
                      ? `Cells smaller than ${data.min_cell_size ?? 5} are not shown.`
                      : 'No occupation rows for this field.'
                  }
                />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={occupations.slice(0, 8)} layout="vertical" margin={{ left: 8, right: 12 }}>
                    <CartesianGrid {...gridProps} />
                    <XAxis type="number" {...axisProps} tickFormatter={fmtNum} />
                    <YAxis type="category" dataKey="occupation" width={120} {...axisProps} />
                    <Tooltip {...tooltipProps} />
                    <Bar dataKey="vacancies" fill={SERIES[0]} radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
