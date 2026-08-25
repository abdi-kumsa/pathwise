import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import useFetch from '../../hooks/useFetch'
import { getMyInstitution, getExpansion } from '../../api/roles'
import {
  SERIES, VERDICT_COLOR, axisProps, gridProps, tooltipProps, RADIUS_H,
  fmtCompact, fmtMoney, fmtPct, fmtDelta, deltaDirection, fmtNum,
} from '../../config/chartTheme'

export default function InstitutionOverviewPage() {
  const { data, loading, error, refetch } = useFetch(() =>
    Promise.all([getMyInstitution(), getExpansion()])
      .then(([profile, expansion]) => ({ profile, expansion }))
  )

  const p = data?.profile
  const programs = data?.expansion?.programs ?? []
  const expand = programs.filter(x => x.recommendation === 'Expand')
  const consolidate = programs.filter(x => x.recommendation === 'Consolidate')

  return (
    <div>
      <SectionHeader
        title={p ? p.institution : 'My institution'}
        subtitle={p ? `${p.type} · ${p.state} · ${p.campus_setting} campus` : 'Loading…'}
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading institution data…" height={300} />}

      {p && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Total enrolment"
              value={fmtCompact(p.total_enrollment)}
              delta={fmtDelta(p.enrollment_cagr_pct) + ' / yr'}
              deltaDirection={deltaDirection(p.enrollment_cagr_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
            />
            <KPICard
              label="Acceptance rate"
              value={fmtPct(p.avg_acceptance_rate_pct)}
              delta={`yield ${fmtPct(p.avg_yield_rate_pct)}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 4h18l-7 8v7l-4 2v-9L3 4Z"/></svg>}
            />
            <KPICard
              label="Net price"
              value={fmtMoney(p.avg_net_price)}
              delta={`list ${fmtMoney(p.avg_tuition)}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
            />
            <KPICard
              label="Employment at 6 months"
              value={fmtPct(p.avg_employment_rate_pct)}
              delta={`${p.programs} programmes`}
              deltaDirection="up"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
          </div>

          <div className="card-grid-2" style={{ marginBottom: 20 }}>
            <div className="panel">
              <p className="panel-title">Enrolment trend</p>
              <p className="panel-sub">Total students by year, 2020–2025</p>
              <ResponsiveContainer width="100%" height={260}>
                <AreaChart data={p.series} margin={{ top: 4, right: 16, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="instEnrol" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={SERIES[0]} stopOpacity={0.26} />
                      <stop offset="100%" stopColor={SERIES[0]} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtCompact} width={50} />
                  <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), 'Enrolment']} />
                  <Area isAnimationActive={false} type="monotone" dataKey="enrollment" stroke={SERIES[0]}
                        strokeWidth={2} fill="url(#instEnrol)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <p className="panel-title">Programme verdicts</p>
              <p className="panel-sub">
                Expansion score out of 100. Colour marks the verdict; the verdict
                is listed beside each bar in the table.
              </p>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={programs} layout="vertical"
                          margin={{ top: 4, right: 28, left: 8, bottom: 0 }}>
                  <CartesianGrid {...gridProps} horizontal={false} vertical />
                  <XAxis type="number" domain={[0, 100]} {...axisProps} />
                  <YAxis type="category" dataKey="program" {...axisProps} width={148}
                         tick={{ fontSize: 9.5, fill: '#64748B' }} />
                  <Tooltip {...tooltipProps}
                           formatter={(v, _n, x) => [`${v} — ${x.payload.recommendation}`, 'Score']} />
                  <Bar isAnimationActive={false} dataKey="score" radius={RADIUS_H} barSize={13}>
                    {programs.map(x => (
                      <Cell key={x.program} fill={VERDICT_COLOR[x.recommendation] ?? SERIES[0]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="io-legend">
                {['Expand', 'Hold', 'Consolidate'].map(v => (
                  <span key={v}><i style={{ background: VERDICT_COLOR[v] }} /> {v}</span>
                ))}
              </div>
            </div>
          </div>

          <div className="card-grid-2">
            <div className="panel">
              <p className="panel-title" style={{ color: 'var(--green)' }}>
                Expand ({expand.length})
              </p>
              <p className="panel-sub">Demand is outpacing what you currently offer</p>
              {expand.length === 0
                ? <p className="io-empty">No programmes currently score above the expansion threshold.</p>
                : expand.map(x => (
                  <div key={x.program} className="io-item">
                    <p className="io-prog">{x.program}</p>
                    <p className="io-why">{x.rationale}</p>
                  </div>
                ))}
            </div>

            <div className="panel">
              <p className="panel-title" style={{ color: 'var(--red)' }}>
                Review ({consolidate.length})
              </p>
              <p className="panel-sub">Weak momentum against a crowded field</p>
              {consolidate.length === 0
                ? <p className="io-empty">No programmes fall below the consolidation threshold.</p>
                : consolidate.map(x => (
                  <div key={x.program} className="io-item">
                    <p className="io-prog">{x.program}</p>
                    <p className="io-why">{x.rationale}</p>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}

      <style>{`
        .io-legend {
          display: flex; flex-wrap: wrap; gap: 8px 16px; margin-top: 12px;
          padding-top: 12px; border-top: 1px solid var(--border);
          font-size: 11.5px; color: var(--text-secondary);
        }
        .io-legend span { display: flex; align-items: center; gap: 6px; }
        .io-legend i { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
        .io-item { padding: 10px 0; border-top: 1px solid #F4F6FA; }
        .io-item:first-of-type { border-top: none; }
        .io-prog { font-size: 13.5px; font-weight: 600; color: var(--navy); }
        .io-why { font-size: 12px; color: var(--text-secondary); margin-top: 3px; line-height: 1.5; }
        .io-empty { font-size: 12.5px; color: var(--text-muted); }
      `}</style>
    </div>
  )
}
