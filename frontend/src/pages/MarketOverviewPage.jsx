import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getMarketOverview, getTopHiringCompanies } from '../api/marketDemand'

const fmtSalary = v => v != null ? '$' + (v / 1000).toFixed(0) + 'K' : '—'
const fmtNum    = v => v != null ? v.toLocaleString() : '—'

export default function MarketOverviewPage() {
  const { data, loading, error, refetch } = useFetch(
    () => Promise.all([getMarketOverview(), getTopHiringCompanies(10)])
         .then(([overview, companies]) => ({ overview, companies }))
  )

  const overview  = data?.overview  ?? null
  const companies = data?.companies ?? []

  return (
    <div>
      <SectionHeader title="Market demand overview" showLiveIndicator={true} />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Total companies"
          value={loading ? '—' : fmtNum(overview?.total_companies)}
          delta="Active hirers"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/></svg>}
        />
        <KPICard
          label="Total placements"
          value={loading ? '—' : fmtNum(overview?.total_placements)}
          delta="Graduates placed"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h4"/><path d="M9 21V9a2 2 0 0 1 2-2h6l4 4v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2Z"/></svg>}
        />
        <KPICard
          label="Avg salary"
          value={loading ? '—' : fmtSalary(overview?.avg_salary)}
          delta="Placed graduates"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
        />
        <KPICard
          label="Top role"
          value={loading ? '—' : (overview?.top_role ?? '—')}
          delta="Most in demand"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>}
        />
      </div>

      <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
        <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
          Top 10 Hiring Companies
        </p>
        {loading ? (
          <LoadingSpinner message="Loading market data…" />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={companies} margin={{ top: 4, right: 16, left: 0, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="company" tick={{ fontSize: 11, fill: '#64748b' }} angle={-35} textAnchor="end" interval={0} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
              <Tooltip formatter={v => [v + ' placements', 'Count']} />
              <Bar isAnimationActive={false} dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
