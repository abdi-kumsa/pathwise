import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getFieldDetail } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps, RADIUS_V,
  fmtCompact, fmtMoney, fmtPct, fmtDelta, deltaDirection, fmtNum,
} from '../../config/chartTheme'

const FIELDS = [
  'AI/ML Engineering', 'Business Intelligence', 'Cloud Infrastructure',
  'Cybersecurity', 'Data & Analytics', 'DevOps', 'Product Management',
  'Software Engineering', 'UX Design',
]

export default function FieldExplorerPage() {
  const [params, setParams] = useSearchParams()
  const [field, setField] = useState(params.get('field') || FIELDS[0])

  useEffect(() => {
    const fromUrl = params.get('field')
    if (fromUrl && fromUrl !== field) setField(fromUrl)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params])

  const { data, loading, error, refetch } = useFetch(() => getFieldDetail(field), [field])

  const pick = (f) => {
    setField(f)
    setParams({ field: f }, { replace: true })
  }

  return (
    <div>
      <SectionHeader
        title="Field explorer"
        subtitle="Enrolment, cost, outcomes and matching labour demand for one field"
      />
      <DataNote tone="simulated">
        Leftover US field vocabulary (AI/ML Engineering, and so on). Not an
        Ethiopia Model 1 or Model 2 score, and not official MoE statistics.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="fe-chips">
          {FIELDS.map(f => (
            <button
              key={f}
              className={`fe-chip${f === field ? ' active' : ''}`}
              onClick={() => pick(f)}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {loading && <LoadingSpinner message={`Loading ${field}…`} height={300} />}

      {data && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Total enrolment"
              value={fmtNum(data.total_enrollment)}
              delta={`${fmtNum(data.total_applications)} applications`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
            />
            <KPICard
              label="Employed at 6 months"
              value={fmtPct(data.employment_rate_pct)}
              delta={`median ${fmtMoney(data.median_salary)}`}
              deltaDirection="up"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
            <KPICard
              label="Net price"
              value={fmtMoney(data.avg_net_price)}
              delta={`list ${fmtMoney(data.avg_tuition)}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
            />
            <KPICard
              label="Labour demand"
              value={fmtNum(data.demand_openings)}
              delta={fmtDelta(data.demand_growth_pct) + ' growth'}
              deltaDirection={deltaDirection(data.demand_growth_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
          </div>

          {/*
            Applications run roughly ten times enrolment, so on a shared axis the
            enrolment line flattens to nothing. A second y-axis is the usual fix
            and exactly the wrong one — two scales on one plot invite false
            comparisons between unrelated magnitudes. Small multiples share the
            x-axis and let each series use its own range honestly.
          */}
          <div className="card-grid-2" style={{ marginBottom: 20 }}>
            <div className="panel">
              <p className="panel-title">Applications</p>
              <p className="panel-sub">Applications received per year</p>
              <ResponsiveContainer width="100%" height={240}>
                <ComposedChart data={data.series} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtCompact} width={52} />
                  <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), 'Applications']} />
                  <Bar isAnimationActive={false} dataKey="applications" fill={SERIES[1]}
                       radius={RADIUS_V} barSize={26} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <p className="panel-title">Enrolment</p>
              <p className="panel-sub">
                Students who actually enrolled — note the smaller scale
              </p>
              <ResponsiveContainer width="100%" height={240}>
                <ComposedChart data={data.series} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtCompact} width={52} />
                  <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), 'Enrolment']} />
                  <Line isAnimationActive={false} type="monotone" dataKey="enrollment"
                        stroke={SERIES[0]} strokeWidth={2}
                        dot={{ r: 3.5, strokeWidth: 0, fill: SERIES[0] }} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="panel">
            <p className="panel-title">Programmes in {data.field}</p>
            <p className="panel-sub">
              {data.programs.length} programme{data.programs.length === 1 ? '' : 's'}
              {data.stem_designated ? ' · STEM designated' : ''}
            </p>

            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Programme</th>
                    <th style={{ textAlign: 'left' }}>Level</th>
                    <th>Enrolment</th>
                    <th>Applications</th>
                    <th>Acceptance</th>
                    <th>Yield</th>
                    <th>Net price</th>
                    <th>Employed 6mo</th>
                    <th>10-yr ROI</th>
                  </tr>
                </thead>
                <tbody>
                  {data.programs.map(p => (
                    <tr key={p.program}>
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>{p.program}</td>
                      <td style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>{p.level}</td>
                      <td className="num">{fmtNum(p.enrollment)}</td>
                      <td className="num">{fmtNum(p.applications)}</td>
                      <td className="num">{fmtPct(p.acceptance_rate_pct)}</td>
                      <td className="num">{fmtPct(p.yield_rate_pct)}</td>
                      <td className="num">{fmtMoney(p.net_price)}</td>
                      <td className="num">{fmtPct(p.employment_rate_pct)}</td>
                      <td className="num">{fmtMoney(p.roi_10yr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <style>{`
        .fe-chips { display: flex; flex-wrap: wrap; gap: 8px; }
        .fe-chip {
          border: 1px solid var(--border); background: var(--white);
          border-radius: 999px; padding: 7px 14px; font-size: 12.5px;
          color: var(--text-secondary); cursor: pointer; font-family: inherit;
          transition: border-color .15s ease, color .15s ease;
        }
        .fe-chip:hover { border-color: var(--blue); color: var(--navy); }
        .fe-chip.active {
          background: var(--navy); border-color: var(--navy);
          color: #fff; font-weight: 500;
        }
        .table-scroll th {
          text-align: right; padding: 8px 12px; font-size: 11px; font-weight: 600;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em;
          border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 9px 12px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); text-align: right;
        }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
