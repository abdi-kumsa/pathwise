import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import useFetch from '../../hooks/useFetch'
import { getResourceEfficiency } from '../../api/roles'
import {
  SERIES, ORDINAL_BLUE, axisProps, gridProps, tooltipProps, RADIUS_H,
  fmtCompact, fmtMoney, fmtPct, fmtNum,
} from '../../config/chartTheme'

export default function ResourceEfficiencyPage() {
  const { data, loading, error, refetch } = useFetch(getResourceEfficiency)

  const funnel = data?.funnel ?? []
  const programs = data?.programs ?? []
  const maxStage = funnel[0]?.count ?? 1

  return (
    <div>
      <SectionHeader
        title="Resource efficiency"
        subtitle={data ? `What recruitment costs ${data.institution}, and where it converts` : 'Loading…'}
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading funnel data…" height={320} />}

      {data && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Marketing spend"
              value={fmtMoney(data.total_marketing_spend)}
              delta="Across all programmes"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
            />
            <KPICard
              label="Cost per enrolment"
              value={fmtMoney(data.cost_per_enrollment)}
              delta="Spend ÷ students enrolled"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 4h18l-7 8v7l-4 2v-9L3 4Z"/></svg>}
            />
            <KPICard
              label="Inquiry → application"
              value={fmtPct(data.inquiry_to_app_pct)}
              delta="Conversion at stage 1"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>}
            />
            <KPICard
              label="Application → enrolment"
              value={fmtPct(data.app_to_enroll_pct)}
              delta="Conversion at stage 2"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
          </div>

          <div className="card-grid-2" style={{ marginBottom: 20 }}>
            <div className="panel">
              <p className="panel-title">Recruitment funnel</p>
              <p className="panel-sub">
                One ordered measure, so the stages use a single hue stepped
                light to dark rather than four unrelated colours.
              </p>

              <div className="funnel">
                {funnel.map((s, i) => {
                  const pct = (s.count / maxStage) * 100
                  const prev = i > 0 ? funnel[i - 1].count : null
                  return (
                    <div key={s.stage} className="funnel-row">
                      <div className="funnel-labels">
                        <span className="funnel-stage">{s.stage}</span>
                        <span className="funnel-count">{fmtNum(s.count)}</span>
                      </div>
                      <div className="funnel-track">
                        <div className="funnel-fill" style={{
                          width: `${Math.max(pct, 1.5)}%`,
                          background: ORDINAL_BLUE[i] ?? ORDINAL_BLUE[ORDINAL_BLUE.length - 1],
                        }} />
                      </div>
                      {prev != null && (
                        <span className="funnel-drop">
                          {fmtPct(s.count / prev * 100, 1)} of previous stage
                        </span>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            <div className="panel">
              <p className="panel-title">Cost per enrolment by programme</p>
              <p className="panel-sub">
                Lowest is most efficient. Best: {data.most_efficient_program ?? '—'}.
              </p>
              <ResponsiveContainer width="100%" height={340}>
                <BarChart data={programs} layout="vertical"
                          margin={{ top: 4, right: 40, left: 8, bottom: 0 }}>
                  <CartesianGrid {...gridProps} horizontal={false} vertical />
                  <XAxis type="number" {...axisProps} tickFormatter={fmtMoney} />
                  <YAxis type="category" dataKey="program" {...axisProps} width={150}
                         tick={{ fontSize: 9.5, fill: '#64748B' }} />
                  <Tooltip {...tooltipProps}
                           formatter={(v, _n, p) => [
                             `${fmtMoney(v)} · ${fmtNum(p.payload.enrollment)} enrolled`,
                             'Cost per enrolment',
                           ]} />
                  <Bar isAnimationActive={false} dataKey="cost_per_enrollment" radius={RADIUS_H} barSize={13}>
                    {programs.map(p => (
                      <Cell
                        key={p.program}
                        fill={
                          p.program === data.most_efficient_program ? '#0CA30C'
                          : p.program === data.least_efficient_program ? '#D03B3B'
                          : SERIES[0]
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="re-legend">
                <span><i style={{ background: '#0CA30C' }} /> Most efficient</span>
                <span><i style={{ background: '#D03B3B' }} /> Least efficient</span>
              </p>
            </div>
          </div>

          <div className="panel">
            <p className="panel-title">Programme funnel detail</p>
            <p className="panel-sub">Where each programme loses candidates</p>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Programme</th>
                    <th>Spend</th>
                    <th>Inquiries</th>
                    <th>Applications</th>
                    <th>Enrolment</th>
                    <th>Cost / inquiry</th>
                    <th>Cost / enrolment</th>
                    <th>Inq → app</th>
                    <th>App → enrol</th>
                  </tr>
                </thead>
                <tbody>
                  {programs.map(p => (
                    <tr key={p.program}>
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>{p.program}</td>
                      <td className="num">{fmtCompact(p.marketing_spend)}</td>
                      <td className="num">{fmtNum(p.inquiries)}</td>
                      <td className="num">{fmtNum(p.applications)}</td>
                      <td className="num">{fmtNum(p.enrollment)}</td>
                      <td className="num">{fmtMoney(p.cost_per_inquiry)}</td>
                      <td className="num" style={{ fontWeight: 600 }}>{fmtMoney(p.cost_per_enrollment)}</td>
                      <td className="num">{fmtPct(p.inquiry_to_app_pct)}</td>
                      <td className="num">{fmtPct(p.app_to_enroll_pct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <style>{`
        .funnel { display: flex; flex-direction: column; gap: 18px; margin-top: 8px; }
        .funnel-labels {
          display: flex; justify-content: space-between; align-items: baseline;
          margin-bottom: 6px;
        }
        .funnel-stage { font-size: 13px; font-weight: 600; color: var(--navy); }
        .funnel-count {
          font-family: 'IBM Plex Mono', monospace; font-size: 13px;
          font-weight: 600; color: var(--navy);
        }
        .funnel-track {
          height: 26px; background: var(--page); border-radius: 6px; overflow: hidden;
        }
        .funnel-fill { height: 100%; border-radius: 6px; transition: width .3s ease; }
        .funnel-drop { display: block; font-size: 11px; color: var(--text-muted); margin-top: 5px; }
        .re-legend {
          display: flex; gap: 16px; margin-top: 12px; padding-top: 12px;
          border-top: 1px solid var(--border); font-size: 11.5px; color: var(--text-secondary);
        }
        .re-legend span { display: flex; align-items: center; gap: 6px; }
        .re-legend i { width: 10px; height: 10px; border-radius: 3px; }
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
