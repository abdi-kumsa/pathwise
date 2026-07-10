import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getDemandForecast } from '../api/marketDemand'

const MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

export default function ForecastPage() {
  const { data: forecast, loading, error, refetch } = useFetch(
    () => getDemandForecast(12)
  )

  const data = forecast ?? []

  const total     = data.reduce((s, d) => s + d.predicted_postings, 0)
  const avgMonth  = data.length ? Math.round(total / data.length) : 0
  const peak      = data.reduce((p, d) => d.predicted_postings > (p?.predicted_postings ?? 0) ? d : p, null)
  const peakLabel = peak ? MONTH_NAMES[new Date(peak.month).getMonth()] + ' ' + new Date(peak.month).getFullYear() : '—'
  const avgCI     = data.length
    ? Math.round(data.reduce((s, d) => s + (d.upper_bound - d.lower_bound), 0) / data.length)
    : 0

  const chartData = data.map(d => {
    const dt = new Date(d.month)
    return {
      name:     MONTH_NAMES[dt.getMonth()],
      Forecast: d.predicted_postings,
      Lower:    d.lower_bound,
      Upper:    d.upper_bound,
    }
  })

  return (
    <div>
      <SectionHeader title="Demand forecast" showLiveIndicator={true} />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="12-month total"
          value={loading ? '—' : total.toLocaleString()}
          delta="Predicted postings"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
        />
        <KPICard
          label="Peak month"
          value={loading ? '—' : peakLabel}
          delta={loading ? '' : (peak?.predicted_postings ?? '') + ' postings'}
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>}
        />
        <KPICard
          label="Avg monthly"
          value={loading ? '—' : avgMonth.toLocaleString()}
          delta="Postings / month"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>}
        />
        <KPICard
          label="Avg confidence band"
          value={loading ? '—' : '±' + Math.round(avgCI / 2)}
          delta="Avg CI width / 2"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
        />
      </div>

      <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
        <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '4px' }}>
          Prophet Job-Demand Forecast — Next 12 Months
        </p>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Shaded band shows the 80% confidence interval. Seasonal peaks in Q1 and Aug–Sep are driven by hiring cycles.
        </p>
        {loading ? (
          <LoadingSpinner message="Loading forecast…" height={320} />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <defs>
                <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#2563eb" stopOpacity={0.15} />
                  <stop offset="95%" stopColor="#2563eb" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip formatter={(v, name) => [v.toLocaleString(), name]} />
              <Area type="monotone" dataKey="Upper"    stroke="#cbd5e1" strokeWidth={1} strokeDasharray="4 2" fill="none" name="Upper bound" />
              <Area type="monotone" dataKey="Forecast" stroke="#2563eb" strokeWidth={2} fill="url(#forecastGrad)" name="Forecast" />
              <Area type="monotone" dataKey="Lower"    stroke="#cbd5e1" strokeWidth={1} strokeDasharray="4 2" fill="none" name="Lower bound" />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
