import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getMyInstitution } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps,
  fmtCompact, fmtPct, fmtDelta, deltaDirection, fmtNum,
} from '../../config/chartTheme'

export default function InstitutionOverviewPage() {
  const { data: p, loading, error, refetch } = useFetch(getMyInstitution)

  return (
    <div>
      <SectionHeader
        title={p ? p.institution : 'My institution'}
        subtitle={p ? `${p.type} · ${p.region || p.state}` : 'Loading…'}
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading institution data…" height={300} />}

      {p && (
        <>
          <DataNote tone="simulated">
            Enrolment, applications, capacity utilisation and year-over-year change
            for {p.institution}. Figures are simulated Ethiopian structure until
            an official SIS file is loaded.
          </DataNote>
          <div className="kpi-grid" style={{ marginTop: 16 }}>
            <KPICard
              label="Latest enrolment"
              value={fmtCompact(p.latest_enrollment ?? p.total_enrollment)}
              delta={fmtDelta(p.yoy_change_pct) + ' YoY'}
              deltaDirection={deltaDirection(p.yoy_change_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
            />
            <KPICard
              label="Applications"
              value={fmtCompact(p.total_applications)}
              delta={`CAGR ${fmtDelta(p.enrollment_cagr_pct)}`}
              deltaDirection={deltaDirection(p.enrollment_cagr_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 4h18l-7 8v7l-4 2v-9L3 4Z"/></svg>}
            />
            <KPICard
              label="Capacity utilisation"
              value={fmtPct(p.capacity_utilization_pct)}
              delta={`${p.programs} programmes`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/></svg>}
            />
            <KPICard
              label="Employment at 6 months"
              value={fmtPct(p.avg_employment_rate_pct)}
              delta={`yield ${fmtPct(p.avg_yield_rate_pct)}`}
              deltaDirection="up"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Enrolment trend</p>
            <p className="panel-sub">Total students by year, 2016–2025</p>
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
