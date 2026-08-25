import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import useFetch from '../hooks/useFetch'
import { getSkillGapData } from '../api/marketDemand'

const SHORT_NAMES = {
  'Academic Performance (GPA)': 'GPA',
  'Industry Experience':        'Experience',
  'Communication Skills':       'Communication',
  'Project Portfolio':          'Projects',
}

export default function SkillGapPage() {
  const { data: skillGap, loading, error, refetch } = useFetch(() => getSkillGapData())

  const skills    = skillGap?.skills ?? []
  const topSkill  = skillGap?.top_gap_skill ?? '—'
  const avgCov    = skills.length ? (skills.reduce((s, x) => s + x.curriculum_coverage, 0) / skills.length).toFixed(1) + '%' : '—'
  const topDemand = skills.length ? skills[0].skill : '—'
  const avgGap    = skillGap?.avg_gap_score != null ? skillGap.avg_gap_score.toFixed(1) : '—'

  const chartData = skills.map(s => ({
    name:     SHORT_NAMES[s.skill] ?? s.skill,
    Demand:   s.demand_score,
    Coverage: s.curriculum_coverage,
    Gap:      s.gap_score,
  }))

  return (
    <div>
      <SectionHeader title="Skill gap analysis" showLiveIndicator={true} />

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Top gap skill"
          value={loading ? '—' : topSkill.split(' (')[0]}
          delta="Highest unmet demand"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>}
        />
        <KPICard
          label="Avg curriculum coverage"
          value={loading ? '—' : avgCov}
          delta="Across all skills"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
        />
        <KPICard
          label="Top demand driver"
          value={loading ? '—' : topDemand.split(' (')[0]}
          delta="Highest SHAP score"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="17" y="4" width="4" height="16" rx="1"/></svg>}
        />
        <KPICard
          label="Avg gap score"
          value={loading ? '—' : avgGap}
          delta="Demand minus coverage"
          deltaDirection="down"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
        />
      </div>

      <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
        <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '4px' }}>
          Demand vs Curriculum Coverage
        </p>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
          Scores are normalised 0–100. Demand is derived from SHAP feature importance; Coverage from average student performance.
        </p>
        {loading ? (
          <LoadingSpinner message="Loading skill gap data…" />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
              <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 11, fill: '#64748b' }} domain={[0, 110]} />
              <Tooltip formatter={(v, name) => [v.toFixed(1), name]} />
              <Legend />
              <Bar isAnimationActive={false} dataKey="Demand"   fill="#2563eb" radius={[4, 4, 0, 0]} />
              <Bar isAnimationActive={false} dataKey="Coverage" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar isAnimationActive={false} dataKey="Gap"      fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
