import { Link } from 'react-router-dom'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import useFetch from '../../hooks/useFetch'
import client from '../../api/client'
import { getLabourOverview, getEducationOverview } from '../../api/roles'
import { fmtCompact, fmtPct } from '../../config/chartTheme'

const ROLE_CARDS = [
  {
    role: 'Student', to: '/student/careers', tone: '#2563EB',
    blurb: 'Career explorer — pick a target job, get ranked departments with the reasoning.',
  },
  {
    role: 'Ministry of Labour', to: '/mol/overview', tone: '#EA580C',
    blurb: 'Emerging occupations, workforce shortfalls, and credential mismatch.',
  },
  {
    role: 'Ministry of Education', to: '/moe/quadrant', tone: '#0E9F6E',
    blurb: 'Investment matrix — where demand growth outruns graduate supply.',
  },
  {
    role: 'University', to: '/university/overview', tone: '#D97706',
    blurb: 'Portfolio, expansion verdicts, recruitment efficiency, peer standing.',
  },
]

export default function AdminOverviewPage() {
  const { data, loading, error, refetch } = useFetch(() =>
    Promise.all([
      client.get('/health').then(r => r.data),
      getLabourOverview(),
      getEducationOverview(),
    ]).then(([health, labour, education]) => ({ health, labour, education }))
  )

  const health = data?.health
  const modelsUp = health ? Object.values(health.models).filter(Boolean).length : 0
  const modelsTotal = health ? Object.keys(health.models).length : 5

  return (
    <div>
      <SectionHeader
        title="Platform overview"
        subtitle="System health and every role's view in one place"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading platform status…" height={280} />}

      {data && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="API status"
              value={health.status === 'ok' ? 'Healthy' : 'Degraded'}
              delta={`${modelsUp}/${modelsTotal} models loaded`}
              deltaDirection={health.status === 'ok' ? 'up' : 'down'}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>}
            />
            <KPICard
              label="Labour records"
              value={fmtCompact(data.labour.total_openings)}
              delta={`${data.labour.occupations_tracked} occupations`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
            <KPICard
              label="Enrolment records"
              value={fmtCompact(data.education.total_enrollment)}
              delta={`${data.education.institutions} institutions · ${data.education.programs} programmes`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
            />
            <KPICard
              label="Employment rate"
              value={fmtPct(data.education.avg_employment_rate_pct)}
              delta="Graduates at 6 months"
              deltaDirection="up"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Model status</p>
            <p className="panel-sub">
              Loaded artefacts, read live from the API rather than a startup snapshot
            </p>
            <div className="ao-models">
              {Object.entries(health.models).map(([name, up]) => (
                <div key={name} className="ao-model">
                  <span className="ao-dot" style={{ background: up ? '#0CA30C' : '#D03B3B' }} />
                  <span className="ao-model-name">{name}</span>
                  <span className="ao-model-state" style={{ color: up ? 'var(--green)' : 'var(--red)' }}>
                    {up ? 'loaded' : 'missing'}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <p className="panel-title">Role views</p>
            <p className="panel-sub">
              As an administrator you can open any role's dashboard directly
            </p>
            <div className="ao-roles">
              {ROLE_CARDS.map(r => (
                <Link key={r.role} to={r.to} className="ao-role"
                      style={{ borderLeftColor: r.tone }}>
                  <p className="ao-role-name">{r.role}</p>
                  <p className="ao-role-blurb">{r.blurb}</p>
                </Link>
              ))}
            </div>
          </div>
        </>
      )}

      <style>{`
        .ao-models {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 10px;
        }
        .ao-model {
          display: flex; align-items: center; gap: 9px;
          border: 1px solid var(--border); border-radius: 9px; padding: 10px 12px;
        }
        .ao-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
        .ao-model-name {
          font-size: 12.5px; color: var(--navy); font-weight: 500;
          text-transform: capitalize; flex: 1;
        }
        .ao-model-state { font-size: 11px; font-weight: 600; }
        .ao-roles {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px;
        }
        .ao-role {
          display: block; text-decoration: none;
          border: 1px solid var(--border); border-left-width: 3px;
          border-radius: 10px; padding: 13px 15px; background: #FCFDFE;
          transition: box-shadow .15s ease;
        }
        .ao-role:hover { box-shadow: 0 4px 14px rgba(15,23,42,0.07); }
        .ao-role-name { font-size: 13.5px; font-weight: 600; color: var(--navy); }
        .ao-role-blurb {
          font-size: 12px; color: var(--text-secondary); margin-top: 4px; line-height: 1.5;
        }
      `}</style>
    </div>
  )
}
