import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
  ScatterChart, Scatter, ZAxis,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getPolicyPriority } from '../../api/roles'
import {
  SERIES, STATUS, axisProps, gridProps, tooltipProps, RADIUS_H, stackGap, fmtNum,
} from '../../config/chartTheme'

const FACTOR_ORDER = ['labour_shortage', 'national_priority', 'student_demand', 'feasibility']
const FACTOR_LABEL = {
  labour_shortage: 'Labour shortage',
  national_priority: 'National priority',
  student_demand: 'Student demand',
  feasibility: 'Feasibility',
}

/**
 * W.MOE.05 — ranks on Model 3 policy weights, not the old ROI ranker.
 */
export default function InvestmentPriorityPage() {
  const { data, loading, error, refetch } = useFetch(getPolicyPriority)
  const rows = data?.rows ?? []
  const weights = data?.weights ?? {}
  const chartData = rows.map(f => ({
    field: f.field,
    score: f.score,
    ...Object.fromEntries((f.factors || []).map(x => [x.factor, x.contribution])),
  }))
  const matrix = rows.map(f => ({
    field: f.field,
    labour_shortage: Number(f.signed_gap || 0),
    student_demand: Number(f.unconstrained_demand || 0),
    feasibility: Number(f.feasibility || 0.5),
    score: Number(f.score || 0),
  }))

  return (
    <div>
      <SectionHeader
        title="Which fields to grow first"
        subtitle="Labour shortage, national priority, student demand and feasibility"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Scoring fields…" height={380} />}
      {data && (
        <>
          <DataNote tone="simulated">
            {data.method} Fit classification is not used.
          </DataNote>
          <p style={{ fontSize: 12, color: STATUS.good, margin: '12px 0' }}>
            Ranking factors: {(data.ranking_factors || FACTOR_ORDER).join(', ')}
            {data.fit_classification_used === false ? ' · fit_classification_used: false' : ''}
          </p>
          <div className="panel" style={{ marginBottom: 20 }} data-testid="priority-matrix">
            <p className="panel-title">Priority matrix</p>
            <p className="panel-sub">Labour shortage (x) × student demand (y). Mark size is feasibility.</p>
            <ResponsiveContainer width="100%" height={320}>
              <ScatterChart margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="labour_shortage" name="Labour shortage" {...axisProps} />
                <YAxis dataKey="student_demand" name="Student demand" {...axisProps} />
                <ZAxis dataKey="feasibility" range={[40, 200]} />
                <Tooltip {...tooltipProps} cursor={{ strokeDasharray: '3 3' }} />
                <Scatter name="Fields" data={matrix} fill={SERIES[0]} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Priority score, decomposed</p>
            <p className="panel-sub">Each segment is one published weight. Segments sum to the field score.</p>
            <ResponsiveContainer width="100%" height={Math.max(320, rows.length * 42)}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 40, left: 8, bottom: 0 }}>
                <CartesianGrid {...gridProps} horizontal={false} vertical />
                <XAxis type="number" domain={[0, 100]} {...axisProps} />
                <YAxis type="category" dataKey="field" {...axisProps} width={160} tick={{ fontSize: 11, fill: '#64748B' }} />
                <Tooltip {...tooltipProps} formatter={(v, name) => [`${v} pts`, FACTOR_LABEL[name] ?? name]} />
                <Legend
                  wrapperStyle={{ fontSize: 12, paddingTop: 10 }}
                  formatter={v => `${FACTOR_LABEL[v] ?? v} (${((weights[v] || 0) * 100).toFixed(0)}%)`}
                />
                {FACTOR_ORDER.map((f, i) => (
                  <Bar isAnimationActive={false} key={f} dataKey={f} stackId="score"
                       fill={SERIES[i]} barSize={20}
                       radius={i === FACTOR_ORDER.length - 1 ? RADIUS_H : 0} {...stackGap} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="panel">
            <p className="panel-title">Ranked fields</p>
            {(rows[0]?.factors || []).map(f => (
              <span key={f.factor} data-testid="factor" style={{
                display: 'inline-block', fontSize: 12, padding: '4px 8px', margin: '0 8px 8px 0',
                borderRadius: 8, background: 'var(--page)',
              }}>
                {f.factor} {(f.weight * 100).toFixed(0)}%
              </span>
            ))}
            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', width: 40 }}>#</th>
                    <th style={{ textAlign: 'left' }}>Field</th>
                    <th>Score</th>
                    <th>Status</th>
                    <th>Labour shortage</th>
                    <th>Student demand</th>
                    <th>Feasibility</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(f => (
                    <tr key={f.field} data-testid="priority-row">
                      <td style={{ textAlign: 'left', color: 'var(--text-muted)' }}>{f.rank}</td>
                      <td style={{ textAlign: 'left', fontWeight: 600 }}>{f.field}</td>
                      <td className="num">{fmtNum(f.score)}</td>
                      <td>{f.status}</td>
                      <td className="num">{fmtNum(f.signed_gap)}</td>
                      <td className="num">{fmtNum(f.unconstrained_demand)}</td>
                      <td className="num">{f.feasibility != null ? Number(f.feasibility).toFixed(2) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
      <style>{`
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
