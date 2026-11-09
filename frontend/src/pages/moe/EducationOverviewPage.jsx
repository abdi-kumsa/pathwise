import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getEducationOverview, getFieldTrends } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps, RADIUS_H,
  fmtCompact, fmtPct, fmtDelta, deltaDirection, fmtNum,
} from '../../config/chartTheme'

export default function EducationOverviewPage() {
  const { data, loading, error, refetch } = useFetch(() =>
    Promise.all([getEducationOverview(), getFieldTrends()])
      .then(([overview, trends]) => ({ overview, trends }))
  )

  const o = data?.overview
  const trends = data?.trends ?? []

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
        title="National education snapshot"
        subtitle="Ethiopian HEIs, enrolment, student demand, capacity and projected intake"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading education data…" height={300} />}

      {o && (
        <>
          <div style={{ marginBottom: 16 }}>
            <DataNote tone="simulated">
              Simulated Ethiopian structure. Headline cards are HEIs, enrolment, applications and capacity — not USD net-price or 10-year ROI.
            </DataNote>
          </div>
          <div className="kpi-grid">
            <KPICard
              label="HEIs"
              value={fmtNum(o.institutions)}
              delta={`${o.programs} programmes · ${o.fields} fields`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/></svg>}
            />
            <KPICard
              label="Enrolment"
              value={fmtNum(o.enrollment_latest_year ?? o.total_enrollment)}
              delta={fmtDelta(o.enrollment_cagr_pct) + ' / yr'}
              deltaDirection={deltaDirection(o.enrollment_cagr_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
            />
            <KPICard
              label="Student demand"
              value={fmtNum(o.applications_latest_year ?? o.total_applications)}
              delta="Applications, latest year (simulated)"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8"/></svg>}
            />
            <KPICard
              label="Capacity utilisation"
              value={o.capacity_utilization_pct != null ? fmtPct(o.capacity_utilization_pct) : '—'}
              delta={o.projected_intake != null ? `Projected intake ${fmtNum(o.projected_intake)}` : 'Projected intake unavailable'}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
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
                  <Tooltip {...tooltipProps} formatter={v => fmtNum(v)} />
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
                Compound annual growth 2016–2025.
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
                  <Bar isAnimationActive={false} dataKey="enrollment_cagr_pct" fill={SERIES[0]} radius={RADIUS_H} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
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
