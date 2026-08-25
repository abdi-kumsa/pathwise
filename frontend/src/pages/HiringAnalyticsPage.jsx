import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getMarketOverview, getTopHiringCompanies, getJobInternshipRatio, getHiringSourceBreakdown } from '../api/marketDemand'

export default function HiringAnalyticsPage() {
  const { data, loading, error, refetch } = useFetch(
    () => Promise.all([
      getMarketOverview(),
      getTopHiringCompanies(8),
      getJobInternshipRatio(),
      getHiringSourceBreakdown(),
    ]).then(([overview, companies, ratio, sources]) => ({ overview, companies, ratio, sources }))
  )

  const overview  = data?.overview  ?? null
  const companies = data?.companies ?? []
  const ratio     = data?.ratio     ?? null
  const sources   = data?.sources   ?? []

  const topCompany   = companies[0]?.company ?? '—'
  const ratioDisplay = ratio ? ratio.ratio.toFixed(2) : '—'
  const timeToHire   = overview ? overview.avg_time_to_hire + ' days' : '—'
  const placements   = overview ? overview.total_placements.toLocaleString() : '—'

  return (
    <div>
      <SectionHeader title="Hiring analytics" showLiveIndicator={true} />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Top hiring company"
          value={loading ? '—' : topCompany}
          delta={loading ? '' : (companies[0]?.count ?? '') + ' placements'}
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/></svg>}
        />
        <KPICard
          label="Job-to-internship ratio"
          value={loading ? '—' : ratioDisplay}
          delta="Jobs per intern slot"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>}
        />
        <KPICard
          label="Avg time to hire"
          value={loading ? '—' : timeToHire}
          delta="Days from apply to offer"
          deltaDirection="down"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>}
        />
        <KPICard
          label="Total placements"
          value={loading ? '—' : placements}
          delta="Confirmed hires"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h4"/><path d="M9 21V9a2 2 0 0 1 2-2h6l4 4v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2Z"/></svg>}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
            Top 8 Hiring Companies
          </p>
          {loading ? (
            <LoadingSpinner message="Loading hiring data…" height={260} />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={companies} margin={{ top: 4, right: 8, left: 0, bottom: 50 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis dataKey="company" tick={{ fontSize: 10, fill: '#64748b' }} angle={-35} textAnchor="end" interval={0} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip formatter={v => [v, 'Placements']} />
                <Bar isAnimationActive={false} dataKey="count" fill="#2563eb" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
            Placements by Industry Sector
          </p>
          {loading ? (
            <LoadingSpinner message="Loading sector data…" height={260} />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={sources} layout="vertical" margin={{ top: 4, right: 16, left: 80, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis type="category" dataKey="source" tick={{ fontSize: 11, fill: '#64748b' }} width={80} />
                <Tooltip formatter={v => [v, 'Placements']} />
                <Bar isAnimationActive={false} dataKey="count" fill="#6366f1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  )
}
