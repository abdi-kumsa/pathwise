import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getPublicPipeline } from '../../api/roles'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function PublicHiringPage() {
  const { data, loading, error, refetch } = useFetch(getPublicPipeline)
  const rows = data?.rows ?? []
  const years = [...new Set(rows.map(r => r.year))].sort()
  const timeline = years.map(year => {
    const slice = rows.filter(r => r.year === year)
    return {
      year,
      civil_service: slice.reduce((s, r) => s + Number(r.civil_service_hiring_plan || 0), 0),
      megaproject: slice.reduce((s, r) => s + Number(r.megaproject_staffing_demand || 0), 0),
      freeze: slice.some(r => r.freeze),
    }
  })

  return (
    <div>
      <SectionHeader
        title="Public-sector hiring pipeline"
        subtitle="Civil-service plan, freeze flag and megaproject staffing"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading public pipeline…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">Civil-service hiring and megaproject staffing from the simulated public-hiring table (M2.C6).</DataNote>
          {rows.length === 0 ? (
            <EmptyState title="No public-hiring rows" description="Civil-service plan and megaproject staffing are empty." />
          ) : (
            <>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">National timeline</p>
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={timeline} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="year" {...axisProps} />
                <YAxis {...axisProps} tickFormatter={fmtNum} />
                <Tooltip {...tooltipProps} />
                <Legend />
                <Line type="monotone" dataKey="civil_service" name="Civil-service plan" stroke={SERIES[0]} strokeWidth={2} dot={false} />
                <Line type="monotone" dataKey="megaproject" name="Megaproject staffing" stroke={SERIES[1]} strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Freeze flag by year</p>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Year</th>
                    <th>Civil-service plan</th>
                    <th>Megaproject staffing</th>
                    <th>Freeze</th>
                  </tr>
                </thead>
                <tbody>
                  {timeline.map(r => (
                    <tr key={r.year}>
                      <td style={{ textAlign: 'left' }}>{r.year}</td>
                      <td className="num">{fmtNum(r.civil_service)}</td>
                      <td className="num">{fmtNum(r.megaproject)}</td>
                      <td>{r.freeze ? 'freeze' : 'open'}</td>
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
