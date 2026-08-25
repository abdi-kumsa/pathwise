import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import useFetch from '../../hooks/useFetch'
import { getLabourOverview, getEmerging, getSupplyDemand } from '../../api/roles'
import {
  SERIES, SEVERITY_COLOR, axisProps, gridProps, tooltipProps, RADIUS_V, RADIUS_H,
  fmtCompact, fmtNum, fmtDelta, deltaDirection,
} from '../../config/chartTheme'

export default function LabourOverviewPage() {
  const { data, loading, error, refetch } = useFetch(() =>
    Promise.all([getLabourOverview(), getEmerging('family', 9), getSupplyDemand()])
      .then(([overview, emerging, gap]) => ({ overview, emerging, gap }))
  )

  const o = data?.overview
  const emerging = data?.emerging ?? []
  const gap = data?.gap

  return (
    <div>
      <SectionHeader
        title="Labour market overview"
        subtitle="Where demand is growing and where the workforce falls short"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading labour market data…" height={300} />}

      {o && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Total openings"
              value={fmtCompact(o.total_openings)}
              delta={fmtDelta(o.openings_cagr_pct) + ' / yr'}
              deltaDirection={deltaDirection(o.openings_cagr_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
            <KPICard
              label="Undersupplied fields"
              value={`${o.undersupplied_fields} of ${o.fields_tracked}`}
              delta="More openings than graduates"
              deltaDirection="down"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>}
            />
            <KPICard
              label="Supply / demand ratio"
              value={o.avg_supply_demand_ratio.toFixed(2)}
              delta={o.avg_supply_demand_ratio < 1 ? 'Below 1 — shortage' : 'At or above 1'}
              deltaDirection={o.avg_supply_demand_ratio < 1 ? 'down' : 'up'}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3v18M7 7l-4 7h8ZM17 7l-4 7h8Z"/></svg>}
            />
            <KPICard
              label="Average time to fill"
              value={`${o.avg_time_to_fill_days} days`}
              delta={`${o.occupations_tracked} occupations tracked`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>}
            />
          </div>

          <div className="card-grid-2" style={{ marginBottom: 20 }}>
            <div className="panel">
              <p className="panel-title">Demand growth by field</p>
              <p className="panel-sub">Compound annual growth in openings, 2020–2025</p>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={emerging} layout="vertical"
                          margin={{ top: 4, right: 24, left: 8, bottom: 0 }}>
                  <CartesianGrid {...gridProps} horizontal={false} vertical />
                  <XAxis type="number" {...axisProps} tickFormatter={v => `${v}%`} />
                  <YAxis type="category" dataKey="job_family" {...axisProps} width={132}
                         tick={{ fontSize: 10.5, fill: '#64748B' }} />
                  <Tooltip {...tooltipProps}
                           formatter={(v, _n, p) => [`${v}% / yr · ${fmtCompact(p.payload.total_openings)} openings`, 'Growth']} />
                  <Bar isAnimationActive={false} dataKey="openings_cagr_pct" fill={SERIES[0]} radius={RADIUS_H} barSize={17} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <p className="panel-title">Unfilled openings by field</p>
              <p className="panel-sub">
                Demand minus graduate and bootcamp supply. Colour marks severity;
                the label carries it too.
              </p>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={gap?.fields ?? []}
                          margin={{ top: 4, right: 12, left: 0, bottom: 52 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="field" {...axisProps} angle={-35} textAnchor="end"
                         interval={0} tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis {...axisProps} tickFormatter={fmtCompact} width={46} />
                  <Tooltip {...tooltipProps}
                           formatter={(v, _n, p) => [`${fmtNum(v)} unfilled · ${p.payload.severity}`, 'Gap']} />
                  <Bar isAnimationActive={false} dataKey="gap" radius={RADIUS_V} barSize={26}>
                    {(gap?.fields ?? []).map(f => (
                      <Cell key={f.field} fill={SEVERITY_COLOR[f.severity] ?? SERIES[0]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              <div className="legend-row">
                {['critical', 'high', 'moderate', 'low'].map(s => (
                  <span key={s} className="legend-item">
                    <span className="legend-swatch" style={{ background: SEVERITY_COLOR[s] }} />
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            {gap?.severity_basis}
          </p>
        </>
      )}

      <style>{`
        .legend-row {
          display: flex; flex-wrap: wrap; gap: 14px;
          margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border);
        }
        .legend-item {
          display: flex; align-items: center; gap: 6px;
          font-size: 11.5px; color: var(--text-secondary); text-transform: capitalize;
        }
        .legend-swatch { width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }
      `}</style>
    </div>
  )
}
