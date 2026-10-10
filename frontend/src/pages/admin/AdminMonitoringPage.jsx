import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import EmptyState from '../../components/EmptyState'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getDrift } from '../../api/admin'
import client from '../../api/client'
import {
  SERIES, axisProps, gridProps, tooltipProps, fmtNum,
} from '../../config/chartTheme'

const getPredictions = (n = 50) =>
  client.get('/api/monitoring/predictions', { params: { n } }).then(r => r.data)

export default function AdminMonitoringPage() {
  const { data, loading, error, refetch } = useFetch(() =>
    Promise.all([getDrift(), getPredictions(50)])
      .then(([drift, predictions]) => ({ drift, predictions }))
  )

  const drift = data?.drift
  const predictions = data?.predictions ?? []

  const series = predictions.map((p, i) => ({
    n: i + 1,
    probability: p.probability,
    latency: p.latency_ms,
  }))

  return (
    <div>
      <SectionHeader
        title="Model monitoring"
        subtitle="Ethiopia M1/M2 RMSE against seasonal-naive; leftover US placement drift is secondary"
      />
      <DataNote tone="simulated">
        Headline error is Ethiopia seasonal-naive RMSE. US LSTM, Prophet and
        placement XGBoost (baseline 0.88) are leftover tools, not Ethiopia accuracy.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading monitoring data…" height={300} />}

      {drift && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Ethiopia RMSE"
              value={drift.rmse != null ? fmtNum(drift.rmse) : '—'}
              delta={drift.mae != null ? `MAE ${fmtNum(drift.mae)} · vs naive` : 'vs seasonal-naive'}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
            <KPICard
              label="Last retrained"
              value={drift.last_retrained ? String(drift.last_retrained).slice(0, 10) : '—'}
              delta="Comparison JSON mtime"
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>}
            />
            <KPICard
              label="Predictions logged"
              value={fmtNum(drift.total_logged)}
              delta={`leftover US window of ${drift.window}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
            <KPICard
              label="Mean probability"
              value={drift.mean_probability != null ? drift.mean_probability.toFixed(3) : '—'}
              delta={`leftover US baseline ${drift.baseline}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>}
            />
            <KPICard
              label="Drift"
              value={drift.drift != null ? drift.drift.toFixed(4) : '—'}
              delta={drift.alert ? 'Above threshold' : 'Within tolerance'}
              deltaDirection={drift.alert ? 'down' : 'up'}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>}
            />
            <KPICard
              label="Status"
              value={drift.alert ? 'Retrain' : 'Stable'}
              delta={drift.alert ? 'Action needed' : 'No action needed'}
              deltaDirection={drift.alert ? 'down' : 'up'}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Recommendation</p>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              {drift.recommendation}
            </p>
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Ethiopia estimators vs naive</p>
            <p className="panel-sub">Chronological holdout RMSE / MAE. US models are not compared.</p>
            <EthiopiaTable ethiopia={drift.ethiopia} />
            {(drift.us_models_not_compared || []).length > 0 && (
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
                Not compared: {drift.us_models_not_compared.join('; ')}
              </p>
            )}
          </div>

          <div className="panel">
            <p className="panel-title">Recent prediction probabilities</p>
            <p className="panel-sub">
              Leftover US placement probabilities (most recent {series.length}),
              against training baseline {drift.baseline}. Not Ethiopia accuracy.
            </p>

            {series.length === 0 ? (
              <EmptyState
                title="No predictions logged yet"
                description="Run a placement prediction from the student evaluator to start the log."
              />
            ) : (
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={series} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="n" {...axisProps} />
                  <YAxis domain={[0, 1]} {...axisProps} width={44}
                         tickFormatter={v => v.toFixed(1)} />
                  <Tooltip {...tooltipProps}
                           formatter={v => [Number(v).toFixed(4), 'Probability']} />
                  <ReferenceLine y={drift.baseline} stroke="#94A3B8" strokeDasharray="4 4"
                                 label={{ value: 'baseline', position: 'right',
                                          fontSize: 10.5, fill: '#94A3B8' }} />
                  <Line isAnimationActive={false} type="monotone" dataKey="probability" stroke={SERIES[0]}
                        strokeWidth={2} dot={{ r: 2.5, strokeWidth: 0, fill: SERIES[0] }} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}
    </div>
  )
}

function EthiopiaTable({ ethiopia }) {
  if (!ethiopia) return null
  const blocks = [ethiopia.model1, ethiopia.model2].filter(Boolean)
  return (
    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13, marginTop: 8 }}>
      <thead>
        <tr style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>
          <th style={{ padding: '6px 8px' }}>Target</th>
          <th style={{ padding: '6px 8px' }}>Estimator</th>
          <th style={{ padding: '6px 8px' }}>RMSE</th>
          <th style={{ padding: '6px 8px' }}>MAE</th>
        </tr>
      </thead>
      <tbody>
        {blocks.flatMap(block =>
          Object.entries(block.estimators || {}).map(([name, scores]) => (
            <tr key={`${block.label}-${name}`}>
              <td style={{ padding: '6px 8px' }}>{block.label}</td>
              <td style={{ padding: '6px 8px' }}>
                {name}{name === block.selected_name ? ' (selected)' : ''}
              </td>
              <td style={{ padding: '6px 8px' }}>{scores?.rmse ?? '—'}</td>
              <td style={{ padding: '6px 8px' }}>{scores?.mae ?? '—'}</td>
            </tr>
          ))
        )}
      </tbody>
    </table>
  )
}
