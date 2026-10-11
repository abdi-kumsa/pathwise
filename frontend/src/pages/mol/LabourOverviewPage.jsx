import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getLabourOverview } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps, RADIUS_H,
  fmtCompact, fmtPct, fmtDelta, deltaDirection,
} from '../../config/chartTheme'

export default function LabourOverviewPage() {
  const { data: o, loading, error, refetch } = useFetch(getLabourOverview)
  const fields = o?.field_openings ?? []

  return (
    <div>
      <SectionHeader
        title="Labour pulse"
        subtitle="Employment, unemployment, underemployment, vacancies and participation"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading labour market data…" height={300} />}

      {o && (
        <>
          <div style={{ marginBottom: 16 }}>
            <DataNote tone="simulated">
              Pulse cards come from labour-history, formal/informal structure and vacancies — not US job-board copy as the headline.
            </DataNote>
          </div>
          <div className="kpi-grid">
            <KPICard
              label="Employment"
              value={fmtCompact(o.employment_level)}
              delta={o.labour_force_participation_pct != null ? `${fmtPct(o.labour_force_participation_pct)} participation` : 'Participation unavailable'}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8"/></svg>}
            />
            <KPICard
              label="Unemployment"
              value={o.unemployment_rate_pct != null ? fmtPct(o.unemployment_rate_pct) : '—'}
              delta={`${o.undersupplied_fields} of ${o.fields_tracked} fields undersupplied`}
              deltaDirection="down"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>}
            />
            <KPICard
              label="Underemployment"
              value={fmtCompact(o.underemployment)}
              delta="Labour-force structure, not job-board copy"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3v18M7 7l-4 7h8ZM17 7l-4 7h8Z"/></svg>}
            />
            <KPICard
              label="Vacancies"
              value={fmtCompact(o.vacancies ?? o.openings_latest_year)}
              delta={fmtDelta(o.openings_cagr_pct) + ' openings / yr'}
              deltaDirection={deltaDirection(o.openings_cagr_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Vacancies by field</p>
            <p className="panel-sub">Latest-year openings from the labour overview, not the leftover emerging list</p>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={fields} layout="vertical"
                        margin={{ top: 4, right: 24, left: 8, bottom: 0 }}>
                <CartesianGrid {...gridProps} horizontal={false} vertical />
                <XAxis type="number" {...axisProps} tickFormatter={fmtCompact} />
                <YAxis type="category" dataKey="field" {...axisProps} width={132}
                       tick={{ fontSize: 10.5, fill: '#64748B' }} />
                <Tooltip {...tooltipProps}
                         formatter={(v) => [fmtCompact(v), 'Openings']} />
                <Bar isAnimationActive={false} dataKey="openings" fill={SERIES[0]} radius={RADIUS_H} barSize={17} />
              </BarChart>
            </ResponsiveContainer>
          </div>
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
