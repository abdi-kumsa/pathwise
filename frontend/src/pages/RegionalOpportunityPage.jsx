import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getRegionalHiringData } from '../api/marketDemand'

export default function RegionalOpportunityPage() {
  const { data, loading, error, refetch } = useFetch(getRegionalHiringData)

  const regions = data ?? []
  const total   = regions.reduce((s, r) => s + r.count, 0)

  const topRegion  = regions[0]?.location ?? '—'
  const topCount   = regions[0]?.count ?? 0
  const topShare   = total ? ((topCount / total) * 100).toFixed(1) + '%' : '—'
  const concentrat = total
    ? (regions.slice(0, 3).reduce((s, r) => s + r.count, 0) / total * 100).toFixed(0) + '%'
    : '—'

  return (
    <div>
      <SectionHeader title="Regional opportunity map" showLiveIndicator={true} />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Regions with hiring"
          value={loading ? '—' : regions.length}
          delta="Distinct metro areas"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z"/><circle cx="12" cy="10" r="3"/></svg>}
        />
        <KPICard
          label="Strongest region"
          value={loading ? '—' : topRegion}
          delta={loading ? '' : topCount + ' placements'}
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 21h18"/><path d="M5 21V7l8-4v18"/><path d="M19 21V11l-6-4"/></svg>}
        />
        <KPICard
          label="Top region share"
          value={loading ? '—' : topShare}
          delta="Of all placements"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10Z"/></svg>}
        />
        <KPICard
          label="Top-3 concentration"
          value={loading ? '—' : concentrat}
          delta="Higher = less geographic spread"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
            Placements by Region
          </p>
          {loading ? (
            <LoadingSpinner message="Loading regional data…" height={300} />
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={regions} layout="vertical" margin={{ top: 4, right: 16, left: 80, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis type="category" dataKey="location" tick={{ fontSize: 11, fill: '#64748b' }} width={80} />
                <Tooltip formatter={v => [v, 'Placements']} />
                <Bar dataKey="count" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '2px' }}>
            Regional Breakdown
          </p>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Share of total confirmed placements by employer region.
          </p>
          {loading ? (
            <LoadingSpinner message="Loading breakdown…" height={260} />
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border)' }}>
                  {['Region', 'Placements', 'Share'].map(h => (
                    <th key={h} style={{ textAlign: h === 'Region' ? 'left' : 'center', padding: '8px 12px', color: 'var(--text-muted)', fontWeight: '600', fontSize: '12px' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {regions.map((r, i) => (
                  <tr key={r.location} style={{ borderBottom: '1px solid #f8fafc', background: i % 2 === 0 ? 'transparent' : '#fafafa' }}>
                    <td style={{ padding: '10px 12px', color: 'var(--navy)', fontWeight: '500' }}>{r.location}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'center', color: 'var(--text-secondary)' }}>{r.count}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'center', fontWeight: '600', color: 'var(--navy)' }}>
                      {total ? ((r.count / total) * 100).toFixed(1) + '%' : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  )
}
