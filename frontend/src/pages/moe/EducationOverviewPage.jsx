import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import useFetch from '../../hooks/useFetch'
import { getEducationOverview, getFieldTrends, getInvestmentQuadrant } from '../../api/roles'
import {
  SERIES, VERDICT_COLOR, axisProps, gridProps, tooltipProps, RADIUS_H,
  fmtCompact, fmtMoney, fmtPct, fmtDelta, deltaDirection,
} from '../../config/chartTheme'

export default function EducationOverviewPage() {
  const { data, loading, error, refetch } = useFetch(() =>
    Promise.all([getEducationOverview(), getFieldTrends(), getInvestmentQuadrant()])
      .then(([overview, trends, quadrant]) => ({ overview, trends, quadrant }))
  )

  const o = data?.overview
  const trends = data?.trends ?? []
  const quadrant = data?.quadrant

  // National enrolment by year, summed across fields.
  const years = [...new Set(trends.flatMap(t => t.series.map(s => s.year)))].sort()
  const national = years.map(year => ({
    year,
    enrollment: trends.reduce(
      (a, t) => a + (t.series.find(s => s.year === year)?.enrollment ?? 0), 0),
    applications: trends.reduce(
      (a, t) => a + (t.series.find(s => s.year === year)?.applications ?? 0), 0),
  }))

  return (
    <div>
      <SectionHeader
        title="Education supply overview"
        subtitle="National enrolment, outcomes and where capacity should go next"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading education data…" height={300} />}

      {o && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Total enrolment"
              value={fmtCompact(o.total_enrollment)}
              delta={fmtDelta(o.enrollment_cagr_pct) + ' / yr'}
              deltaDirection={deltaDirection(o.enrollment_cagr_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
            />
            <KPICard
              label="Employment at 6 months"
              value={fmtPct(o.avg_employment_rate_pct)}
              delta={`${o.programs} programmes · ${o.fields} fields`}
              deltaDirection="up"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
            <KPICard
              label="Average net price"
              value={fmtMoney(o.avg_net_price)}
              delta={`list ${fmtMoney(o.avg_tuition)}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
            />
            <KPICard
              label="10-year ROI"
              value={fmtMoney(o.avg_roi_10yr)}
              delta={`${fmtPct(o.stem_share_pct, 0)} STEM designated`}
              deltaDirection="up"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
          </div>

          <div className="card-grid-2" style={{ marginBottom: 20 }}>
            <div className="panel">
              <p className="panel-title">National enrolment and applications</p>
              <p className="panel-sub">
                Two series on one axis — both are counts of people, so they are
                directly comparable.
              </p>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={national} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtCompact} width={50} />
                  <Tooltip {...tooltipProps} formatter={v => fmtCompact(v)} />
                  <Line isAnimationActive={false} name="Applications" type="monotone" dataKey="applications"
                        stroke={SERIES[1]} strokeWidth={2}
                        dot={{ r: 3, strokeWidth: 0, fill: SERIES[1] }} />
                  <Line isAnimationActive={false} name="Enrolment" type="monotone" dataKey="enrollment"
                        stroke={SERIES[0]} strokeWidth={2}
                        dot={{ r: 3, strokeWidth: 0, fill: SERIES[0] }} />
                </LineChart>
              </ResponsiveContainer>
              <div className="ov-legend">
                <span><i style={{ background: SERIES[1] }} /> Applications</span>
                <span><i style={{ background: SERIES[0] }} /> Enrolment</span>
              </div>
            </div>

            <div className="panel">
              <p className="panel-title">Enrolment growth by field</p>
              <p className="panel-sub">
                Compound annual growth 2020–2025. Colour marks the investment
                verdict; the verdict is also written out below.
              </p>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart
                  data={[...trends].sort((a, b) => b.enrollment_cagr_pct - a.enrollment_cagr_pct)}
                  layout="vertical"
                  margin={{ top: 4, right: 24, left: 8, bottom: 0 }}
                >
                  <CartesianGrid {...gridProps} horizontal={false} vertical />
                  <XAxis type="number" {...axisProps} tickFormatter={v => `${v}%`} />
                  <YAxis type="category" dataKey="field" {...axisProps} width={130}
                         tick={{ fontSize: 10, fill: '#64748B' }} />
                  <Tooltip {...tooltipProps} formatter={v => [`${v}% / yr`, 'Enrolment growth']} />
                  <Bar isAnimationActive={false} dataKey="enrollment_cagr_pct" radius={RADIUS_H} barSize={16}>
                    {[...trends]
                      .sort((a, b) => b.enrollment_cagr_pct - a.enrollment_cagr_pct)
                      .map(t => {
                        const q = quadrant?.points?.find(p => p.field === t.field)?.quadrant
                        return <Cell key={t.field} fill={VERDICT_COLOR[q] ?? SERIES[0]} />
                      })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="ov-legend">
                {['Invest', 'Sustain', 'Oversupply risk', 'Review'].map(q => (
                  <span key={q}><i style={{ background: VERDICT_COLOR[q] }} /> {q}</span>
                ))}
              </div>
            </div>
          </div>

          {quadrant?.invest_fields?.length > 0 && (
            <div className="panel">
              <p className="panel-title">Priority for new capacity</p>
              <p className="panel-sub">
                Fields where labour demand is growing faster than the graduates
                being produced for it
              </p>
              <div className="ov-invest">
                {quadrant.invest_fields.map(f => {
                  const p = quadrant.points.find(x => x.field === f)
                  return (
                    <div key={f} className="ov-invest-item">
                      <p className="ov-invest-field">{f}</p>
                      <p className="ov-invest-nums">
                        demand {fmtDelta(p.demand_growth_pct)}/yr · supply {fmtDelta(p.supply_growth_pct)}/yr
                      </p>
                      <p className="ov-invest-progs">{p.programs.join(', ')}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </>
      )}

      <style>{`
        .ov-legend {
          display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 12px;
          padding-top: 12px; border-top: 1px solid var(--border);
          font-size: 11.5px; color: var(--text-secondary);
        }
        .ov-legend span { display: flex; align-items: center; gap: 6px; }
        .ov-legend i { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
        .ov-invest {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
          gap: 12px; margin-top: 14px;
        }
        .ov-invest-item {
          border: 1px solid var(--border); border-left: 3px solid var(--green);
          border-radius: 10px; padding: 12px 14px; background: #FCFDFE;
        }
        .ov-invest-field { font-size: 13.5px; font-weight: 600; color: var(--navy); }
        .ov-invest-nums {
          font-size: 11.5px; color: var(--text-secondary); margin-top: 3px;
          font-variant-numeric: tabular-nums;
        }
        .ov-invest-progs { font-size: 11.5px; color: var(--text-muted); margin-top: 5px; line-height: 1.45; }
      `}</style>
    </div>
  )
}
