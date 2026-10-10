import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getRegionalDemand } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps, RADIUS_H, RADIUS_V,
  fmtCompact, fmtNum, fmtMoney, fmtPct, shortMetro,
} from '../../config/chartTheme'

const FIELDS = [
  'AI/ML Engineering', 'Business Intelligence', 'Cloud Infrastructure',
  'Cybersecurity', 'Data & Analytics', 'DevOps', 'Product Management',
  'Software Engineering', 'UX Design',
]

export default function RegionalDemandPage() {
  const [field, setField] = useState('')

  const { data, loading, error, refetch } = useFetch(
    () => getRegionalDemand(field || null, 15),
    [field]
  )

  const metros = data?.metros ?? []
  const states = (data?.states ?? []).slice(0, 12)
  const totalOpenings = metros.reduce((a, m) => a + m.openings, 0)

  return (
    <div>
      <SectionHeader
        title="Regional demand"
        subtitle="Where in the country the openings actually are"
      />
      <DataNote tone="simulated">
        Leftover US metro / field vocabulary. Not an Ethiopia Model 1 or Model 2
        score, and not official MoLS statistics.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="panel" style={{ marginBottom: 20 }}>
        <label className="rd-label" htmlFor="field-filter">Filter by field</label>
        <select
          id="field-filter"
          className="rd-select"
          value={field}
          onChange={e => setField(e.target.value)}
        >
          <option value="">All fields</option>
          {FIELDS.map(f => <option key={f} value={f}>{f}</option>)}
        </select>
      </div>

      {loading && <LoadingSpinner message="Loading regional demand…" height={300} />}

      {data && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Openings in view"
              value={fmtCompact(totalOpenings)}
              delta={field || 'All fields'}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z"/><circle cx="12" cy="10" r="3"/></svg>}
            />
            <KPICard
              label="Top metro"
              value={metros[0]?.metro?.split('-')[0] ?? '—'}
              delta={metros[0] ? fmtNum(metros[0].openings) + ' openings' : ''}
              deltaDirection="up"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4"/></svg>}
            />
            <KPICard
              label="Remote-friendly"
              value={fmtPct(data.remote_share_pct)}
              delta="of openings allow remote"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 21h8M12 18v3"/></svg>}
            />
            <KPICard
              label="States covered"
              value={fmtNum(data.states?.length ?? 0)}
              delta="with recorded demand"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 6l6-3 6 3 6-3v15l-6 3-6-3-6 3zM9 3v15M15 6v15"/></svg>}
            />
          </div>

          <div className="card-grid-2">
            <div className="panel">
              <p className="panel-title">Top metro areas</p>
              <p className="panel-sub">
                Openings{field ? ` in ${field}` : ' across all fields'}
              </p>
              <ResponsiveContainer width="100%" height={420}>
                <BarChart data={metros} layout="vertical"
                          margin={{ top: 4, right: 24, left: 8, bottom: 0 }}>
                  <CartesianGrid {...gridProps} horizontal={false} vertical />
                  <XAxis type="number" {...axisProps} tickFormatter={fmtCompact} />
                  <YAxis type="category" dataKey="metro" {...axisProps} width={112}
                         tickFormatter={shortMetro}
                         tick={{ fontSize: 10.5, fill: '#64748B' }} />
                  <Tooltip
                    {...tooltipProps}
                    formatter={(v, _n, p) => [
                      `${fmtNum(v)} openings · ${fmtMoney(p.payload.avg_salary)} avg`,
                      'Demand',
                    ]}
                  />
                  <Bar isAnimationActive={false} dataKey="openings" fill={SERIES[0]} radius={RADIUS_H} barSize={15} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="panel">
              <p className="panel-title">By state</p>
              <p className="panel-sub">Top 12 states by openings</p>
              <ResponsiveContainer width="100%" height={420}>
                <BarChart data={states} margin={{ top: 4, right: 12, left: 0, bottom: 68 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="state" {...axisProps} angle={-40} textAnchor="end"
                         interval={0} tick={{ fontSize: 10, fill: '#64748B' }} />
                  <YAxis {...axisProps} tickFormatter={fmtCompact} width={46} />
                  <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), 'Openings']} />
                  <Bar isAnimationActive={false} dataKey="openings" fill={SERIES[0]} radius={RADIUS_V} barSize={22} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      <style>{`
        .rd-label {
          display: block; font-size: 12px; font-weight: 600;
          color: var(--navy); margin-bottom: 6px;
        }
        .rd-select {
          font-size: 13.5px; padding: 9px 12px; border-radius: 9px;
          border: 1px solid var(--border); color: var(--navy);
          background: var(--white); cursor: pointer; min-width: 240px;
          font-family: inherit;
        }
      `}</style>
    </div>
  )
}
