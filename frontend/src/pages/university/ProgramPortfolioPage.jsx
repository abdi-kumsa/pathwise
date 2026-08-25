import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import useFetch from '../../hooks/useFetch'
import { getPortfolio } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps, RADIUS_H,
  fmtCompact, fmtMoney, fmtPct, fmtNum,
} from '../../config/chartTheme'

const SORTS = [
  { key: 'enrollment',          label: 'Enrolment' },
  { key: 'applications',        label: 'Applications' },
  { key: 'yield_rate_pct',      label: 'Yield rate' },
  { key: 'cost_per_enrollment', label: 'Cost per enrolment', asc: true },
  { key: 'roi_10yr',            label: 'Student ROI' },
]

export default function ProgramPortfolioPage() {
  const [sort, setSort] = useState(SORTS[0])
  const { data, loading, error, refetch } = useFetch(getPortfolio)

  const programs = [...(data?.programs ?? [])].sort((a, b) =>
    sort.asc ? a[sort.key] - b[sort.key] : b[sort.key] - a[sort.key]
  )

  return (
    <div>
      <SectionHeader
        title="Programme portfolio"
        subtitle={data ? `All ${data.programs.length} programmes at ${data.institution}` : 'Loading…'}
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading portfolio…" height={320} />}

      {data && (
        <>
          <div className="panel" style={{ marginBottom: 20 }}>
            <div className="pp-head">
              <div>
                <p className="panel-title">{sort.label} by programme</p>
                <p className="panel-sub">
                  {sort.asc ? 'Lowest first — lower is better here.' : 'Highest first.'}
                </p>
              </div>
              <div className="pp-sorts">
                {SORTS.map(s => (
                  <button key={s.key}
                          className={`pp-sort${s.key === sort.key ? ' active' : ''}`}
                          onClick={() => setSort(s)}>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <ResponsiveContainer width="100%" height={380}>
              <BarChart data={programs} layout="vertical"
                        margin={{ top: 8, right: 32, left: 8, bottom: 0 }}>
                <CartesianGrid {...gridProps} horizontal={false} vertical />
                <XAxis type="number" {...axisProps}
                       tickFormatter={sort.key.includes('pct') ? (v => `${v}%`) : fmtCompact} />
                <YAxis type="category" dataKey="program" {...axisProps} width={152}
                       tick={{ fontSize: 10, fill: '#64748B' }} />
                <Tooltip {...tooltipProps}
                         formatter={v => [
                           sort.key.includes('pct') ? fmtPct(v)
                             : sort.key.includes('cost') || sort.key.includes('roi') ? fmtMoney(v)
                             : fmtNum(v),
                           sort.label,
                         ]} />
                <Bar isAnimationActive={false} dataKey={sort.key} fill={SERIES[0]} radius={RADIUS_H} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <p className="panel-title">Full detail</p>
            <p className="panel-sub">Enrolment funnel, price position and outcomes</p>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Programme</th>
                    <th style={{ textAlign: 'left' }}>Field</th>
                    <th style={{ textAlign: 'left' }}>Mode</th>
                    <th>Inquiries</th>
                    <th>Applications</th>
                    <th>Enrolment</th>
                    <th>Accept</th>
                    <th>Yield</th>
                    <th>Net price</th>
                    <th>Cost / enrol</th>
                    <th>Employed</th>
                  </tr>
                </thead>
                <tbody>
                  {programs.map(p => (
                    <tr key={p.program}>
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>
                        {p.program}
                        <span className="pp-level">{p.level}</span>
                      </td>
                      <td style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>{p.field}</td>
                      <td style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>{p.delivery_mode}</td>
                      <td className="num">{fmtNum(p.inquiries)}</td>
                      <td className="num">{fmtNum(p.applications)}</td>
                      <td className="num" style={{ fontWeight: 600 }}>{fmtNum(p.enrollment)}</td>
                      <td className="num">{fmtPct(p.acceptance_rate_pct, 0)}</td>
                      <td className="num">{fmtPct(p.yield_rate_pct, 0)}</td>
                      <td className="num">{fmtMoney(p.net_price)}</td>
                      <td className="num">{fmtMoney(p.cost_per_enrollment)}</td>
                      <td className="num">{fmtPct(p.employment_rate_pct, 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <style>{`
        .pp-head {
          display: flex; align-items: flex-start; justify-content: space-between;
          gap: 16px; flex-wrap: wrap; margin-bottom: 8px;
        }
        .pp-sorts { display: flex; flex-wrap: wrap; gap: 6px; }
        .pp-sort {
          border: 1px solid var(--border); background: var(--white);
          border-radius: 999px; padding: 6px 12px; font-size: 12px;
          color: var(--text-secondary); cursor: pointer; font-family: inherit;
        }
        .pp-sort:hover { border-color: var(--blue); }
        .pp-sort.active {
          background: var(--navy); border-color: var(--navy); color: #fff; font-weight: 500;
        }
        .pp-level {
          display: block; font-size: 10.5px; color: var(--text-muted); margin-top: 1px;
        }
        .table-scroll th {
          text-align: right; padding: 8px 10px; font-size: 10.5px; font-weight: 600;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em;
          border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 9px 10px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); text-align: right; font-size: 12.5px;
        }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
