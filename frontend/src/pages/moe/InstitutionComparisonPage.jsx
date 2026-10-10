import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getInstitutionComparison } from '../../api/roles'
import { STATUS, ORDINAL_BLUE, fmtNum, fmtPct } from '../../config/chartTheme'

const ALIGN = {
  shortage: STATUS.serious,
  balanced: STATUS.good,
  oversupply: STATUS.warning,
}

function heat(value, max) {
  if (!max) return ORDINAL_BLUE[0]
  const t = Number(value || 0) / max
  if (t < 0.34) return ORDINAL_BLUE[0]
  if (t < 0.67) return ORDINAL_BLUE[1]
  return ORDINAL_BLUE[2]
}

export default function InstitutionComparisonPage() {
  const { data, loading, error, refetch } = useFetch(getInstitutionComparison)
  const rows = data?.rows ?? []
  const maxCap = Math.max(0, ...rows.map(r => Number(r.capacity || 0)))

  return (
    <div>
      <SectionHeader
        title="Institution comparison"
        subtitle="Capacity, forecast accuracy, graduate outcomes and alignment across registered HEIs"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading institutions…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Reading this table writes an institution_drilldown audit row. Alignment status is labelled in words as well as colour.
          </DataNote>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">{rows.length} HEIs · {data.year}</p>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Institution</th>
                    <th>Region</th>
                    <th>Enrolment</th>
                    <th>Capacity</th>
                    <th>Utilisation</th>
                    <th>Forecast accuracy</th>
                    <th>Employment</th>
                    <th>Alignment</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(r => (
                    <tr key={r.institution}>
                      <td style={{ textAlign: 'left', fontWeight: 600 }}>{r.institution}</td>
                      <td>{r.region}</td>
                      <td className="num">{fmtNum(r.enrollment)}</td>
                      <td className="num" style={{ background: heat(r.capacity, maxCap) + '33' }}>{fmtNum(r.capacity)}</td>
                      <td className="num">{r.capacity_utilization_pct != null ? fmtPct(r.capacity_utilization_pct) : '—'}</td>
                      <td className="num">{r.forecast_accuracy != null ? r.forecast_accuracy.toFixed(2) : '—'}</td>
                      <td className="num">{fmtPct(r.employment_rate_pct)}</td>
                      <td>
                        <span style={{
                          color: ALIGN[r.alignment_status] || STATUS.warning,
                          fontWeight: 700, textTransform: 'capitalize',
                        }}>{r.alignment_status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      <style>{`
        .table-scroll th { text-align: right; padding: 8px 10px; font-size: 11px; color: var(--text-muted); border-bottom: 1px solid var(--border); white-space: nowrap; }
        .table-scroll td { padding: 8px 10px; text-align: right; border-bottom: 1px solid #F4F6FA; font-size: 12.5px; }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
