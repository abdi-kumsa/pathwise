import { useState } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getWorkforceReport, downloadWorkforceReport } from '../../api/roles'
import { fmtNum } from '../../config/chartTheme'

export default function WorkforceReportPage() {
  const { data, loading, error, refetch } = useFetch(getWorkforceReport)
  const [busy, setBusy] = useState(null)
  const [dlError, setDlError] = useState(null)
  const breakdowns = data?.breakdowns || {}
  const hasRows = Object.values(breakdowns).some(rows => (rows || []).length > 0)
  const recommendations = [...(breakdowns.sector || [])]
    .sort((a, b) => Number(b.employment_demand || b.vacancies || 0) - Number(a.employment_demand || a.vacancies || 0))
    .slice(0, 5)

  async function download(format) {
    setBusy(format)
    setDlError(null)
    try {
      await downloadWorkforceReport(format)
    } catch (err) {
      setDlError(err.message)
    } finally {
      setBusy(null)
    }
  }

  return (
    <div>
      <SectionHeader
        title="Workforce planning report"
        subtitle="Exportable recommendations by sector, occupation, skill and region"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {dlError && <ErrorBanner message={dlError} />}
      {loading && <LoadingSpinner message="Building report…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            {data.note} Downloads are recorded in the audit log.{data.official_forecast ? '' : ' Not an official forecast.'}
          </DataNote>
          <ForecastAccuracyNote />
          <div className="panel" style={{ marginTop: 16 }} data-testid="report-summary">
            <p className="panel-title">Workforce planning report</p>
            <p className="panel-sub">As of {data.as_of ?? '—'} · horizon {data.horizon ?? '—'} years</p>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>
              Simulated Ethiopian structure. Not an official forecast or a ministry circular.
            </p>
            {recommendations.length > 0 && (
              <ol style={{ margin: '10px 0 0 18px', fontSize: 13 }}>
                {recommendations.map((r, i) => (
                  <li key={i}>
                    Prioritise {r.sector || r.occupation || r.region || 'this slice'}
                    {r.employment_demand != null ? ` · demand ${fmtNum(r.employment_demand)}` : ''}
                  </li>
                ))}
              </ol>
            )}
          </div>
          {Object.keys(breakdowns).length === 0 || !hasRows ? (
            <EmptyState title="No report rows" description="Sector, occupation, skill and region breakdowns are empty." />
          ) : null}
          <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
            {['csv', 'xlsx', 'pdf'].map(fmt => (
              <button key={fmt} type="button" className="export-btn" disabled={!!busy} onClick={() => download(fmt)}>
                {busy === fmt ? `Exporting ${fmt}…` : `Download ${fmt.toUpperCase()}`}
              </button>
            ))}
          </div>
          {hasRows ? Object.entries(breakdowns).map(([kind, rows]) => (
            <div key={kind} className="panel" style={{ marginTop: 16 }}>
              <p className="panel-title">{kind}</p>
              <p className="panel-sub">{(rows || []).length} rows · preview</p>
              <div className="table-scroll">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>Key</th>
                      <th>Period</th>
                      <th>Employment demand</th>
                      <th>Vacancies</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(rows || []).slice(0, 12).map((r, i) => (
                      <tr key={i}>
                        <td style={{ textAlign: 'left' }}>{r.sector || r.occupation || r.region || r.field || '—'}</td>
                        <td className="num">{r.period || r.year || '—'}</td>
                        <td className="num">{fmtNum(r.employment_demand)}</td>
                        <td className="num">{fmtNum(r.vacancies ?? r.skill_shortages)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )) : null}
        </>
      )}
      <style>{`
        .export-btn {
          border: 1px solid var(--border); background: var(--white); color: var(--navy);
          padding: 8px 14px; border-radius: 8px; font-weight: 600; cursor: pointer; font-family: inherit;
        }
        .export-btn:disabled { opacity: .6; cursor: default; }
        .table-scroll th { text-align: right; padding: 8px 12px; font-size: 11px; color: var(--text-muted); border-bottom: 1px solid var(--border); }
        .table-scroll td { padding: 8px 12px; text-align: right; border-bottom: 1px solid #F4F6FA; }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
