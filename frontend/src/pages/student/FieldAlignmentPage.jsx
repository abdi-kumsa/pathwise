import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getFieldAlignment } from '../../api/student'
import { SERIES, STATUS, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

export default function FieldAlignmentPage() {
  const { data, loading, error, refetch } = useFetch(getFieldAlignment)
  const rows = data?.rows ?? []
  const own = rows.find(r => r.is_own_field)
  const nationalTop = rows[0]
  const focus = own || nationalTop
  const factors = (focus?.factors ?? []).map(f => ({
    factor: f.factor,
    contribution: f.contribution,
    weight: Math.round(f.weight * 100),
  }))

  return (
    <div>
      <SectionHeader
        title="Field opportunity"
        subtitle="Labour demand, graduate supply and employment outcomes — with the reasons behind the score"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading alignment…" height={280} />}
      {data && focus && (
        <>
          <DataNote tone="simulated">{data.method}</DataNote>
          <div className="kpi-grid" style={{ marginTop: 16 }}>
            <KPICard
              label={own ? `Your field · ${focus.field}` : focus.field}
              value={focus.score}
              delta={`Rank ${focus.rank} of ${rows.length}`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z"/></svg>}
            />
            <KPICard label="Labour demand" value={fmtNum(focus.labour_demand)} delta={focus.status} deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 12h4v8H3zM10 8h4v12h-4zM17 4h4v16h-4z"/></svg>} />
            <KPICard label="Expected graduates" value={fmtNum(focus.expected_graduates)} delta={`severity Q${focus.severity}`} deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5Z"/></svg>} />
            <KPICard
              label="National #1"
              value={nationalTop && nationalTop !== focus ? nationalTop.field : 'This field'}
              delta={nationalTop ? `score ${nationalTop.score}` : '—'}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Why this score</p>
            <p className="panel-sub">
              Weights: {Object.entries(data.weights || {}).map(([k, v]) => `${k} ${(v * 100).toFixed(0)}%`).join(' · ')}
            </p>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={factors} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid {...gridProps} />
                <XAxis type="number" {...axisProps} />
                <YAxis type="category" dataKey="factor" width={140} {...axisProps} />
                <Tooltip {...tooltipProps} />
                <Bar dataKey="contribution" fill={SERIES[0]} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">All fields</p>
            {rows.map(r => (
              <div
                key={r.field}
                data-testid={r.is_own_field ? 'own-field' : 'field-row'}
                style={{
                  display: 'flex', justifyContent: 'space-between', padding: '8px 0',
                  borderBottom: '1px solid var(--border)',
                  fontWeight: r.is_own_field ? 700 : 400,
                  color: r.is_own_field ? SERIES[0] : 'inherit',
                }}
              >
                <span>{r.rank}. {r.field}{r.is_own_field ? ' · your field' : ''}</span>
                <span style={{ color: r.status === 'shortage' ? STATUS.serious : r.status === 'oversupply' ? STATUS.warning : STATUS.good }}>
                  {r.score} · {r.status} (Q{r.severity})
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
