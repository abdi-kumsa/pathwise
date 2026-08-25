import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getInvestmentPriority } from '../../api/roles'
import {
  SERIES, VERDICT_COLOR, axisProps, gridProps, tooltipProps, RADIUS_H, stackGap,
  fmtMoney, fmtPct, fmtDelta,
} from '../../config/chartTheme'

const FACTOR_LABEL = {
  demand_growth:    'Demand growth',
  supply_shortfall: 'Supply shortfall',
  employment_rate:  'Employment rate',
  roi:              'Student ROI',
}

const FACTOR_ORDER = ['demand_growth', 'supply_shortfall', 'employment_rate', 'roi']

/**
 * Fields ranked for investment, with the arithmetic on show.
 *
 * The stacked bar is the score decomposed into its four weighted factors, so a
 * reader can see not just the ranking but what produced it — and can disagree
 * with the weights rather than with an opaque number.
 */
export default function InvestmentPriorityPage() {
  const { data, loading, error, refetch } = useFetch(getInvestmentPriority)

  const fields = data?.fields ?? []
  const weights = data?.weights ?? {}

  // Flatten each field's factor contributions into columns for the stack.
  const chartData = fields.map(f => ({
    field: f.field,
    score: f.score,
    ...Object.fromEntries(f.factors.map(x => [x.factor, x.contribution])),
  }))

  return (
    <div>
      <SectionHeader
        title="Investment priority"
        subtitle="Which fields warrant new education capacity, and the reasoning behind each score"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Scoring fields…" height={380} />}

      {data && (
        <>
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Priority score, decomposed</p>
            <p className="panel-sub">
              Each segment is one factor's contribution in points. Segments sum
              to the field's total score out of 100.
            </p>

            <ResponsiveContainer width="100%" height={Math.max(320, fields.length * 42)}>
              <BarChart data={chartData} layout="vertical"
                        margin={{ top: 4, right: 40, left: 8, bottom: 0 }}>
                <CartesianGrid {...gridProps} horizontal={false} vertical />
                <XAxis type="number" domain={[0, 100]} {...axisProps} />
                <YAxis type="category" dataKey="field" {...axisProps} width={140}
                       tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip
                  {...tooltipProps}
                  formatter={(v, name) => [`${v} pts`, FACTOR_LABEL[name] ?? name]}
                />
                <Legend
                  wrapperStyle={{ fontSize: 12, paddingTop: 10 }}
                  formatter={v => `${FACTOR_LABEL[v]} (${(weights[v] * 100).toFixed(0)}%)`}
                />
                {FACTOR_ORDER.map((f, i) => (
                  <Bar isAnimationActive={false}
                    key={f}
                    dataKey={f}
                    stackId="score"
                    fill={SERIES[i]}
                    barSize={20}
                    radius={i === FACTOR_ORDER.length - 1 ? RADIUS_H : 0}
                    {...stackGap}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="panel" style={{ marginBottom: 16 }}>
            <p className="panel-title">Ranked fields</p>
            <p className="panel-sub">With the underlying figures behind each score</p>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', width: 40 }}>#</th>
                    <th style={{ textAlign: 'left' }}>Field</th>
                    <th>Score</th>
                    <th>Verdict</th>
                    <th>Demand growth</th>
                    <th>Supply growth</th>
                    <th>Coverage</th>
                    <th>Employed 6mo</th>
                    <th>10-yr ROI</th>
                  </tr>
                </thead>
                <tbody>
                  {fields.map(f => (
                    <tr key={f.field}>
                      <td style={{ textAlign: 'left', color: 'var(--text-muted)' }}>{f.rank}</td>
                      <td style={{ textAlign: 'left' }}>
                        <span style={{ fontWeight: 600 }}>{f.field}</span>
                        <span className="ip-progs">{f.programs.join(', ')}</span>
                      </td>
                      <td className="num" style={{ fontWeight: 700 }}>{f.score.toFixed(1)}</td>
                      <td>
                        <span className="ip-verdict" style={{
                          color: VERDICT_COLOR[f.quadrant],
                          background: VERDICT_COLOR[f.quadrant] + '1A',
                        }}>{f.quadrant}</span>
                      </td>
                      <td className="num" style={{ color: f.demand_growth_pct > 0 ? 'var(--green)' : 'var(--red)' }}>
                        {fmtDelta(f.demand_growth_pct)}
                      </td>
                      <td className="num" style={{ color: f.supply_growth_pct > 0 ? 'var(--green)' : 'var(--red)' }}>
                        {fmtDelta(f.supply_growth_pct)}
                      </td>
                      <td className="num">{f.coverage_pct != null ? fmtPct(f.coverage_pct) : '—'}</td>
                      <td className="num">{fmtPct(f.employment_rate_pct)}</td>
                      <td className="num">{fmtMoney(f.roi_10yr)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <DataNote>
            <strong>How the score is built.</strong> {data.method} Weights are{' '}
            {Object.entries(weights).map(([k, v], i, arr) => (
              <span key={k}>
                {FACTOR_LABEL[k]} {(v * 100).toFixed(0)}%{i < arr.length - 1 ? ', ' : '. '}
              </span>
            ))}
            Because every factor is scaled across these nine fields, a score is a
            position within this cohort, not a measure on an absolute scale.
          </DataNote>
        </>
      )}

      <style>{`
        .ip-progs {
          display: block; font-size: 11px; color: var(--text-muted);
          margin-top: 2px; line-height: 1.4;
        }
        .ip-verdict {
          display: inline-block; border-radius: 5px; padding: 2px 8px;
          font-size: 11px; font-weight: 700; white-space: nowrap;
        }
        .table-scroll th {
          text-align: right; padding: 8px 12px; font-size: 11px; font-weight: 600;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em;
          border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 10px 12px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); text-align: right; vertical-align: top;
        }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
