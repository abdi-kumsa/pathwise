import { useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getEnrollmentSummary, getEnrollmentForecast } from '../api/enrollment'

const PROGRAMS = [
  'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
  'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
  'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
  'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

export default function EnrollmentForecastPage() {
  const [program, setProgram] = useState('MS Data Science')

  const {
    data: summary, loading: sumLoading, error: sumError, refetch: sumRefetch,
  } = useFetch(() => getEnrollmentSummary())

  const {
    data: forecast, loading: fcLoading, error: fcError, refetch: fcRefetch,
  } = useFetch(() => getEnrollmentForecast(program, 3), [program])

  // YoY change: last two years in enrollment_by_year
  const yoyChange = (() => {
    if (!summary?.enrollment_by_year) return null
    const years = Object.keys(summary.enrollment_by_year).map(Number).sort()
    const last   = summary.enrollment_by_year[years[years.length - 1]] ?? 0
    const prev   = summary.enrollment_by_year[years[years.length - 2]] ?? 0
    return last - prev
  })()

  // Merge historical + forecast with 1-point overlap to connect the lines
  const chartData = (() => {
    if (!forecast) return []
    const hist   = forecast.historical
    const fc     = forecast.forecast
    const merged = hist.map(d => ({ year: String(d.year), historical: d.predicted_count, forecast: null }))
    if (merged.length && fc.length) {
      merged[merged.length - 1].forecast = merged[merged.length - 1].historical
    }
    fc.forEach(d => merged.push({ year: String(d.year), historical: null, forecast: d.predicted_count }))
    return merged
  })()

  const summaryLoading = sumLoading

  return (
    <div>
      <SectionHeader title="Enrollment forecast" showLiveIndicator={true} />

      {sumError && <ErrorBanner message={sumError} onRetry={sumRefetch} />}
      {fcError  && <ErrorBanner message={fcError}  onRetry={fcRefetch}  />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Total enrolled"
          value={summaryLoading ? '—' : (summary?.total_students ?? '—').toLocaleString()}
          delta="All programmes"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>}
        />
        <KPICard
          label="YoY change"
          value={summaryLoading || yoyChange == null ? '—' : (yoyChange >= 0 ? '+' : '') + yoyChange}
          delta="2023 to 2024"
          deltaDirection={yoyChange != null && yoyChange >= 0 ? 'up' : 'down'}
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>}
        />
        <KPICard
          label="Top programme"
          value={summaryLoading ? '—' : (summary?.top_program ?? '—')}
          delta="Highest enrolment"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="17" y="4" width="4" height="16" rx="1"/></svg>}
        />
        <KPICard
          label="Avg placement rate"
          value={summaryLoading ? '—' : (summary?.avg_placement_rate ?? '—') + '%'}
          delta="Across all programmes"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
        />
      </div>

      <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '2px' }}>
              LSTM Enrollment Forecast
            </p>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Solid = historical (2019–2024) · Dashed = LSTM forecast (2025–2027)
            </p>
          </div>
          <select
            value={program}
            onChange={e => setProgram(e.target.value)}
            style={{ fontSize: '13px', padding: '6px 10px', borderRadius: '8px', border: '1px solid var(--border)', color: 'var(--navy)', background: 'var(--white)', cursor: 'pointer' }}
          >
            {PROGRAMS.map(p => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        {fcLoading ? (
          <LoadingSpinner message="Loading forecast…" height={320} />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="year" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip formatter={(v, name) => [v ?? '—', name]} />
              <Legend />
              <Line isAnimationActive={false} type="monotone" dataKey="historical" stroke="#2563eb" strokeWidth={2} dot={{ r: 4 }} connectNulls={false} name="Historical" />
              <Line isAnimationActive={false} type="monotone" dataKey="forecast"   stroke="#f59e0b" strokeWidth={2} strokeDasharray="6 3" dot={{ r: 4 }} connectNulls={false} name="Forecast" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
