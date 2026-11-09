import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getExpansion } from '../../api/roles'
import {
  SERIES, VERDICT_COLOR, axisProps, gridProps, tooltipProps, RADIUS_H, stackGap,
  fmtMoney, fmtDelta, fmtNum,
} from '../../config/chartTheme'

const FACTOR_LABEL = {
  demand_growth:    'National demand growth',
  own_momentum:     'Own enrolment momentum',
  competitive_room: 'Room vs competitors',
  yield_strength:   'Yield strength',
}
const FACTOR_ORDER = ['demand_growth', 'own_momentum', 'competitive_room', 'yield_strength']

const PRICE_LABEL = {
  premium:  'Priced above competitors',
  parity:   'Priced in line with competitors',
  discount: 'Priced below competitors',
  unknown:  'No competitor pricing',
}

/**
 * "University also can see fields for their resources management and expansion."
 *
 * Each programme is scored on four factors and given a verdict. The score
 * decomposition is on the chart so the verdict can be argued with rather than
 * simply accepted.
 */
export default function ExpansionPage() {
  const { data, loading, error, refetch } = useFetch(getExpansion)

  const programs = data?.programs ?? []
  const weights = data?.weights ?? {}
  const thresholds = data?.thresholds ?? {}

  const chartData = programs.map(p => ({
    program: p.program,
    ...Object.fromEntries(p.factors.map(f => [f.factor, f.contribution])),
  }))

  return (
    <div>
      <SectionHeader
        title="Expansion opportunities"
        subtitle={data ? `Where ${data.institution} should add, hold or consolidate capacity` : 'Loading…'}
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Scoring programmes…" height={380} />}

      {data && (
        <>
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Expansion score, decomposed</p>
            <p className="panel-sub">
              Each segment is one factor's weighted contribution in points.
              Expand at {thresholds.expand}+, consolidate at {thresholds.consolidate} or below.
            </p>

            <ResponsiveContainer width="100%" height={Math.max(340, programs.length * 34)}>
              <BarChart data={chartData} layout="vertical"
                        margin={{ top: 4, right: 36, left: 8, bottom: 0 }}>
                <CartesianGrid {...gridProps} horizontal={false} vertical />
                <XAxis type="number" domain={[0, 100]} {...axisProps} />
                <YAxis type="category" dataKey="program" {...axisProps} width={152}
                       tick={{ fontSize: 10, fill: '#64748B' }} />
                <Tooltip {...tooltipProps}
                         formatter={(v, name) => [`${v} pts`, FACTOR_LABEL[name] ?? name]} />
                <Legend wrapperStyle={{ fontSize: 11.5, paddingTop: 10 }}
                        formatter={v => `${FACTOR_LABEL[v]} (${(weights[v] * 100).toFixed(0)}%)`} />
                {FACTOR_ORDER.map((f, i) => (
                  <Bar isAnimationActive={false} key={f} dataKey={f} stackId="s" fill={SERIES[i]} barSize={16}
                       radius={i === FACTOR_ORDER.length - 1 ? RADIUS_H : 0} {...stackGap} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="ex-cards">
            {programs.map(p => (
              <article key={p.program} className="panel ex-card">
                <header className="ex-head">
                  <div style={{ minWidth: 0, flex: 1 }}>
                    <p className="ex-prog">{p.program}</p>
                    <p className="ex-field">{p.field}</p>
                  </div>
                  <span className="ex-verdict" style={{
                    color: VERDICT_COLOR[p.recommendation],
                    background: VERDICT_COLOR[p.recommendation] + '1A',
                  }}>
                    {p.recommendation}
                  </span>
                </header>

                <p className="ex-score">
                  {p.score.toFixed(0)}<span>/100</span>
                </p>

                <p className="ex-why">{p.rationale}</p>

                <dl className="ex-stats">
                  <div><dt>National demand</dt><dd>{fmtDelta(p.demand_growth_pct)}/yr</dd></div>
                  <div><dt>Own enrolment</dt><dd>{fmtDelta(p.own_growth_pct)}/yr</dd></div>
                  <div><dt>Students</dt><dd>{fmtNum(p.enrollment)}</dd></div>
                  <div><dt>Yield</dt><dd>{p.yield_rate_pct}%</dd></div>
                  <div><dt>Competitors</dt><dd>{p.competitor_programs}</dd></div>
                  <div><dt>Your tuition</dt><dd>{fmtMoney(p.tuition)}</dd></div>
                </dl>

                <p className="ex-price">{PRICE_LABEL[p.price_position]}</p>
              </article>
            ))}
          </div>

          <div style={{ marginTop: 20 }}>
            <DataNote>{data.method}</DataNote>
          </div>
        </>
      )}

      <style>{`
        .ex-cards {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px;
        }
        .ex-card { padding: 16px 18px 18px; }
        .ex-head { display: flex; align-items: flex-start; gap: 10px; }
        .ex-prog { font-size: 13.5px; font-weight: 600; color: var(--navy); }
        .ex-field { font-size: 11.5px; color: var(--text-muted); margin-top: 2px; }
        .ex-verdict {
          border-radius: 6px; padding: 3px 9px; font-size: 10.5px;
          font-weight: 700; text-transform: uppercase; letter-spacing: .03em;
          flex-shrink: 0; white-space: nowrap;
        }
        .ex-score {
          font-size: 26px;
          font-weight: 700; color: var(--navy); margin: 12px 0 8px; line-height: 1;
        }
        .ex-score span { font-size: 12px; color: var(--text-muted); font-weight: 500; }
        .ex-why { font-size: 12px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px; }
        .ex-stats {
          display: grid; grid-template-columns: 1fr 1fr; gap: 6px 14px;
          border-top: 1px solid var(--border); padding-top: 11px;
        }
        .ex-stats div { display: flex; justify-content: space-between; gap: 8px; }
        .ex-stats dt { font-size: 11px; color: var(--text-muted); }
        .ex-stats dd {
          font-size: 11px; color: var(--navy); font-weight: 600;
          font-variant-numeric: tabular-nums;
        }
        .ex-price { font-size: 11px; color: var(--text-muted); margin-top: 10px; }
      `}</style>
    </div>
  )
}
