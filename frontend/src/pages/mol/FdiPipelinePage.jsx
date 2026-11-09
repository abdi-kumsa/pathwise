import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import EthiopiaRegionMap from '../../components/EthiopiaRegionMap'
import useFetch from '../../hooks/useFetch'
import { getFdiPipeline } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function FdiPipelinePage() {
  const { data, loading, error, refetch } = useFetch(getFdiPipeline)
  const rows = data?.rows ?? []
  const years = [...new Set(rows.map(r => r.year))].sort()
  const timeline = years.map(year => {
    const slice = rows.filter(r => r.year === year)
    return {
      year,
      expected_employment: slice.reduce((s, r) => s + Number(r.expected_employment || 0), 0),
      openings: slice.filter(r => r.opening_year).length,
    }
  })
  const latest = years[years.length - 1]
  const mapRows = rows
    .filter(r => r.year === latest)
    .reduce((acc, r) => {
      const name = r.region
      if (!name) return acc
      const cur = acc[name] || { name, value: 0 }
      cur.value += Number(r.expected_employment || 0)
      acc[name] = cur
      return acc
    }, {})

  return (
    <div>
      <SectionHeader
        title="Investment and industrial parks"
        subtitle="Parks, expected employment and opening years"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading FDI pipeline…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Schematic dashboard regions, not a CSA administrative map. Opening years come from park_openings().
          </DataNote>
          {rows.length === 0 ? (
            <EmptyState title="No FDI rows" description="Industrial parks and expected employment are empty." />
          ) : (
            <>
          <div className="card-grid-2" style={{ marginTop: 16 }}>
            <div className="panel">
              <p className="panel-title">Expected employment by region · {latest}</p>
              <EthiopiaRegionMap regions={Object.values(mapRows)} valueLabel="jobs" />
            </div>
            <div className="panel">
              <p className="panel-title">Timeline</p>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={timeline} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtNum} />
                  <Tooltip {...tooltipProps} />
                  <Legend />
                  <Line type="monotone" dataKey="expected_employment" name="Expected employment" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Park opening years</p>
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Park</th>
                    <th>Region</th>
                    <th>Year</th>
                    <th>Expected employment</th>
                    <th>Opening year</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.filter(r => r.opening_year).map((r, i) => (
                    <tr key={`${r.industrial_park}-${r.year}-${i}`}>
                      <td style={{ textAlign: 'left' }}>{r.industrial_park}</td>
                      <td>{r.region}</td>
                      <td className="num">{r.year}</td>
                      <td className="num">{fmtNum(r.expected_employment)}</td>
                      <td>opening</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
            </>
          )}
        </>
      )}
      <style>{`
        .table-scroll th { text-align: right; padding: 8px 12px; font-size: 11px; color: var(--text-muted); border-bottom: 1px solid var(--border); }
        .table-scroll td { padding: 9px 12px; text-align: right; border-bottom: 1px solid #F4F6FA; }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
