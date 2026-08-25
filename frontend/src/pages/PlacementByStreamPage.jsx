import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getPlacementByStream } from '../api/enrollment'

const SHORT = name => name.replace('MS ', '').replace('BS ', '').replace('MBA ', '').replace('Certificate ', '')

export default function PlacementByStreamPage() {
  const { data: streams, loading, error, refetch } = useFetch(() => getPlacementByStream())

  const data = streams ?? []

  const avgRate   = data.length ? (data.reduce((s, r) => s + r.placement_rate, 0) / data.length).toFixed(1) : '—'
  const topStream = data[0]?.program ?? '—'
  const lowStream = data[data.length - 1]?.program ?? '—'
  const avgSalary = data.length
    ? '$' + (data.reduce((s, r) => s + r.avg_salary, 0) / data.length / 1000).toFixed(0) + 'K'
    : '—'

  const chartData = data.map(s => ({
    name:   SHORT(s.program),
    Rate:   s.placement_rate,
    Salary: Math.round(s.avg_salary / 1000),
  }))

  return (
    <div>
      <SectionHeader title="Placement by stream" showLiveIndicator={true} />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Overall placement rate"
          value={loading ? '—' : avgRate + '%'}
          delta="Avg across all streams"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
        />
        <KPICard
          label="Top programme"
          value={loading ? '—' : topStream}
          delta={loading ? '' : data[0]?.placement_rate + '% placed'}
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="17" y="4" width="4" height="16" rx="1"/></svg>}
        />
        <KPICard
          label="Lowest programme"
          value={loading ? '—' : lowStream}
          delta={loading ? '' : data[data.length - 1]?.placement_rate + '% placed'}
          deltaDirection="down"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="17" y="4" width="4" height="16" rx="1"/></svg>}
        />
        <KPICard
          label="Avg placed salary"
          value={loading ? '—' : avgSalary}
          delta="Across all streams"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
            Placement Rate by Programme (%)
          </p>
          {loading ? (
            <LoadingSpinner message="Loading placement data…" height={300} />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 16, left: 100, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: '#64748b' }} unit="%" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} width={100} />
                <Tooltip formatter={v => [v + '%', 'Placement Rate']} />
                <Bar isAnimationActive={false} dataKey="Rate" fill="#10b981" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
            Avg Salary by Programme ($K)
          </p>
          {loading ? (
            <LoadingSpinner message="Loading salary data…" height={300} />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 16, left: 100, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} unit="K" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} width={100} />
                <Tooltip formatter={v => ['$' + v + 'K', 'Avg Salary']} />
                <Bar isAnimationActive={false} dataKey="Salary" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
