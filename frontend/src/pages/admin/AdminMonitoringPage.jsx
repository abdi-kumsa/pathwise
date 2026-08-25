import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import client from '../../api/client'
import {
  SERIES, axisProps, gridProps, tooltipProps, fmtNum,
} from '../../config/chartTheme'

const getDrift = () => client.get('/api/monitoring/drift').then(r => r.data)
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
        subtitle="Prediction drift against the training-time baseline"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading monitoring data…" height={300} />}

      {drift && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Predictions logged"
              value={fmtNum(drift.total_logged)}
              delta={`window of ${drift.window}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
            <KPICard
              label="Mean probability"
              value={drift.mean_probability != null ? drift.mean_probability.toFixed(3) : '—'}
              delta={`baseline ${drift.baseline}`}
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

          <div className="panel">
            <p className="panel-title">Recent prediction probabilities</p>
            <p className="panel-sub">
              Most recent {series.length} placement predictions, against the
              training baseline of {drift.baseline}
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
