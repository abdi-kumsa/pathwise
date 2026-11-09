import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getSupplyDemand } from '../../api/roles'
import {
  SERIES, SEVERITY_COLOR, axisProps, gridProps, tooltipProps, RADIUS_V,
  fmtCompact, fmtNum, fmtMoney, fmtPct,
} from '../../config/chartTheme'

/**
 * The workforce shortfall per field — demand against the people qualified to
 * meet it. This is the mismatch signal with genuine between-field variance,
 * which is why it leads the MoL section rather than the fit classification.
 */
export default function SupplyDemandPage() {
  const { data, loading, error, refetch } = useFetch(getSupplyDemand)
  const fields = data?.fields ?? []

  const worst = fields[0]
  const totalDemand = fields.reduce((a, f) => a + f.demand_openings, 0)
  const totalSupply = fields.reduce((a, f) => a + f.supply_total, 0)

  return (
    <div>
      <SectionHeader
        title="Supply &amp; demand gap"
        subtitle="Openings against the graduates and bootcamp completers available to fill them"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Computing workforce gaps…" height={300} />}

      {data && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Total demand"
              value={fmtNum(totalDemand)}
              delta="Openings 2016–2025"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 7h-9M14 17H5M17 3l3 4-3 4M7 13l-3 4 3 4"/></svg>}
            />
            <KPICard
              label="Total supply"
              value={fmtNum(totalSupply)}
              delta="Graduates + bootcamps"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
            />
            <KPICard
              label="Unfilled openings"
              value={fmtNum(data.total_gap)}
              delta={fmtPct(data.total_gap / totalDemand * 100, 1) + ' of demand'}
              deltaDirection="down"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>}
            />
            <KPICard
              label="Largest shortfall"
              value={worst?.field ?? '—'}
              delta={worst ? fmtNum(worst.gap) + ' unfilled' : ''}
              deltaDirection="down"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>}
            />
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Demand against supply, by field</p>
            <p className="panel-sub">
              Two measures on the same scale (people), so they share one axis.
            </p>
            <ResponsiveContainer width="100%" height={330}>
              <BarChart data={fields} margin={{ top: 4, right: 12, left: 0, bottom: 56 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="field" {...axisProps} angle={-32} textAnchor="end"
                       interval={0} tick={{ fontSize: 10, fill: '#64748B' }} />
                <YAxis {...axisProps} tickFormatter={fmtCompact} width={48} />
                <Tooltip {...tooltipProps} formatter={v => fmtNum(v)} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 8 }} />
                <Bar isAnimationActive={false} name="Demand (openings)" dataKey="demand_openings"
                     fill={SERIES[0]} radius={RADIUS_V} barSize={15} />
                <Bar isAnimationActive={false} name="Supply (graduates + bootcamps)" dataKey="supply_total"
                     fill={SERIES[1]} radius={RADIUS_V} barSize={15} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="panel" style={{ marginBottom: 16 }}>
            <p className="panel-title">Field detail</p>
            <p className="panel-sub">Ranked by unfilled openings</p>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Field</th>
                    <th>Severity</th>
                    <th>Demand</th>
                    <th>Graduates</th>
                    <th>Bootcamps</th>
                    <th>Gap</th>
                    <th>Coverage</th>
                    <th>Time to fill</th>
                    <th>Avg salary</th>
                  </tr>
                </thead>
                <tbody>
                  {fields.map(f => (
                    <tr key={f.field}>
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>{f.field}</td>
                      <td>
                        {/* Colour plus the word — severity never reads by colour alone */}
                        <span className="sev" style={{
                          color: SEVERITY_COLOR[f.severity],
                          background: SEVERITY_COLOR[f.severity] + '1A',
                        }}>
                          {f.severity}
                        </span>
                      </td>
                      <td className="num">{fmtNum(f.demand_openings)}</td>
                      <td className="num">{fmtNum(f.supply_graduates)}</td>
                      <td className="num">{fmtNum(f.supply_bootcamp)}</td>
                      <td className="num" style={{ fontWeight: 600 }}>{fmtNum(f.gap)}</td>
                      <td className="num">{fmtPct(f.coverage_pct)}</td>
                      <td className="num">{f.time_to_fill_days}d</td>
                      <td className="num">{fmtMoney(f.avg_salary)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <DataNote>{data.severity_basis}</DataNote>
        </>
      )}

      <style>{`
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
        .sev {
          display: inline-block; border-radius: 5px; padding: 2px 9px;
          font-size: 11px; font-weight: 700; text-transform: capitalize;
        }
      `}</style>
    </div>
  )
}
