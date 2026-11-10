import { Link } from 'react-router-dom'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getPlatformHealth } from '../../api/admin'
import { STATUS } from '../../config/chartTheme'

const ROLE_CARDS = [
  {
    role: 'Student', to: '/student/profile',
    blurb: 'Eligibility, the jobs outlook for a field, and where it has room.',
  },
  {
    role: 'Ministry of Labour', to: '/mol/overview',
    blurb: 'The labour market today, where demand is heading, where skills fall short.',
  },
  {
    role: 'Ministry of Education', to: '/moe/gap',
    blurb: 'Where demand outruns graduates, which fields to grow first, which regions are misaligned.',
  },
  {
    role: 'University', to: '/university/overview',
    blurb: 'Which programmes are healthy, how many will apply, where applicants drop out.',
  },
]

export default function AdminOverviewPage() {
  const { data, loading, error, refetch } = useFetch(getPlatformHealth)
  const modelsUp = data ? data.models_loaded : 0
  const modelsTotal = data ? data.models_total : 5
  const apiOk = data?.api_status === 'ok' || data?.status === 'ok'
  // Ethiopia Models 1–3 are computed from parquet per request and have no
  // artefact to load. Only the leftover US models do, and they are off by default.
  const legacyOff = data?.legacy_us_models === false

  return (
    <div>
      <SectionHeader
        title="Platform health"
        subtitle="Users, API status, models loaded and process uptime"
      />

      <DataNote tone="simulated">
        Counts from this API process. Figures elsewhere on the console remain
        simulated until official files replace them.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading platform status…" height={280} />}

      {data && (
        <>
          <div className="kpi-grid" style={{ marginTop: 16 }}>
            <KPICard
              label="Users"
              value={data.users?.total ?? '—'}
              delta={`${data.users?.active ?? 0} active`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8"/></svg>}
            />
            <KPICard
              label="API status"
              value={apiOk ? 'Healthy' : 'Degraded'}
              delta={legacyOff ? 'Ethiopia models computed on request' : `${modelsUp}/${modelsTotal} models loaded`}
              deltaDirection={apiOk ? 'up' : 'down'}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>}
            />
            <KPICard
              label="Models loaded"
              value={legacyOff ? 'n/a' : `${modelsUp}/${modelsTotal}`}
              delta={legacyOff ? 'Leftover US artefacts switched off' : apiOk ? 'All artefacts resident' : 'One or more missing'}
              deltaDirection={apiOk ? 'up' : 'down'}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z"/></svg>}
            />
            <KPICard
              label="Uptime"
              value={data.uptime || '—'}
              delta={`${data.uptime_seconds ?? 0} seconds`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>}
            />
          </div>

          <div className="panel" style={{ margin: '20px 0' }}>
            <p className="panel-title">Model status</p>
            <p className="panel-sub">Loaded artefacts, read live from the API</p>
            {legacyOff && (
              <p className="panel-sub">
                No artefacts to load: Ethiopia Models 1–3 are fitted from the parquet tables on
                request, and the leftover US models are switched off (LEGACY_US_MODELS).
              </p>
            )}
            <div className="ao-models">
              {Object.entries(data.models || {}).map(([name, up]) => (
                <div key={name} className="ao-model">
                  <span className="ao-dot" style={{ background: up ? STATUS.good : STATUS.critical }} />
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
              As an administrator you can open any role&apos;s dashboard directly
            </p>
            <div className="ao-roles">
              {ROLE_CARDS.map(r => (
                <Link key={r.role} to={r.to} className="ao-role">
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
