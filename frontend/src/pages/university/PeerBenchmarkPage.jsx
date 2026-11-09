import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getPeerBenchmark } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps, RADIUS_V,
  fmtCompact, fmtMoney, fmtPct,
} from '../../config/chartTheme'

const METRICS = [
  { key: 'enrollment',          label: 'Total enrolment',     fmt: fmtCompact },
  { key: 'applications',        label: 'Applications',        fmt: fmtCompact },
  { key: 'acceptance_rate_pct', label: 'Acceptance rate',     fmt: v => fmtPct(v) },
  { key: 'yield_rate_pct',      label: 'Yield rate',          fmt: v => fmtPct(v) },
  { key: 'avg_tuition',         label: 'Average tuition',     fmt: fmtMoney },
  { key: 'avg_net_price',       label: 'Average net price',   fmt: fmtMoney },
  { key: 'employment_rate_pct', label: 'Employment 6mo',      fmt: v => fmtPct(v) },
  { key: 'roi_10yr',            label: '10-year ROI',         fmt: fmtMoney },
  { key: 'cost_per_enrollment', label: 'Cost per enrolment',  fmt: fmtMoney },
]

const DIRECTION_NOTE = {
  higher:  'higher is stronger',
  lower:   'lower is stronger',
  neutral: 'not ranked',
}

export default function PeerBenchmarkPage() {
  const { data, loading, error, refetch } = useFetch(getPeerBenchmark)

  const me = data?.me
  const peers = data?.peers ?? []
  const direction = data?.direction ?? {}
  const percentile = data?.percentile ?? {}

  return (
    <div>
      <SectionHeader
        title="Peer benchmark"
        subtitle={data ? `${data.institution} against ${data.peer_count} anonymised peers` : 'Loading…'}
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Comparing against peers…" height={340} />}

      {data && (
        <>
          {/* Percentile standing — a single ordered measure per metric */}
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Where you stand</p>
            <p className="panel-sub">
              Share of peers beaten on each metric, scored in the direction that
              represents strength for that metric.
            </p>

            <div className="pb-standing">
              {METRICS.filter(m => percentile[m.key] != null).map(m => {
                const v = percentile[m.key]
                const tone = v >= 67 ? '#0CA30C' : v >= 34 ? '#FAB219' : '#D03B3B'
                return (
                  <div key={m.key} className="pb-row">
                    <div className="pb-row-head">
                      <span className="pb-metric">
                        {m.label}
                        <span className="pb-dir">{DIRECTION_NOTE[direction[m.key]]}</span>
                      </span>
                      <span className="pb-value">{m.fmt(me[m.key])}</span>
                    </div>
                    <div className="pb-track">
                      <div className="pb-fill" style={{ width: `${v}%`, background: tone }} />
                    </div>
                    <span className="pb-pct">Beats {v}% of peers</span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Per-metric comparison against the anonymised peer set */}
          <div className="pb-charts">
            {METRICS.slice(0, 6).map(m => {
              const rows = [
                { label: 'You', value: me[m.key], mine: true },
                ...peers.map(p => ({ label: p.label, value: p[m.key], mine: false })),
              ]
              return (
                <div key={m.key} className="panel">
                  <p className="panel-title">{m.label}</p>
                  <p className="panel-sub">{DIRECTION_NOTE[direction[m.key]]}</p>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={rows} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                      <CartesianGrid {...gridProps} />
                      <XAxis dataKey="label" {...axisProps}
                             tick={{ fontSize: 10, fill: '#64748B' }} interval={0} />
                      <YAxis {...axisProps} width={52}
                             tickFormatter={m.key.includes('pct') ? (v => `${Math.round(v)}%`) : fmtCompact} />
                      <Tooltip {...tooltipProps} formatter={v => [m.fmt(v), m.label]} />
                      <Bar isAnimationActive={false} dataKey="value" radius={RADIUS_V} barSize={22}>
                        {rows.map((r, i) => (
                          <Cell key={i} fill={r.mine ? SERIES[0] : '#CBD5E1'} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )
            })}
          </div>

          <div style={{ marginTop: 20 }}>
            <DataNote>{data.note}</DataNote>
          </div>
        </>
      )}

      <style>{`
        .pb-standing { display: flex; flex-direction: column; gap: 16px; margin-top: 6px; }
        .pb-row-head {
          display: flex; justify-content: space-between; align-items: baseline;
          gap: 12px; margin-bottom: 6px;
        }
        .pb-metric { font-size: 13px; font-weight: 600; color: var(--navy); }
        .pb-dir {
          font-size: 11px; font-weight: 400; color: var(--text-muted); margin-left: 8px;
        }
        .pb-value {
          font-size: 13px;
          font-weight: 600; color: var(--navy);
        }
        .pb-track {
          height: 8px; background: var(--page); border-radius: 4px; overflow: hidden;
        }
        .pb-fill { height: 100%; border-radius: 4px; transition: width .3s ease; }
        .pb-pct { display: block; font-size: 11px; color: var(--text-muted); margin-top: 4px; }
        .pb-charts {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;
        }
      `}</style>
    </div>
  )
}
