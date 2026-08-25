import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getRoles } from '../../api/auth'

/**
 * Account roles and what each can reach.
 *
 * Read-only by design. There is no user CRUD in this build — accounts are
 * seeded from the environment at startup (backend/startup_seed.py), so
 * offering create/delete here would imply a capability the backend does not
 * have. The permission matrix below is the useful part: it documents the
 * boundaries that the API actually enforces.
 */

const ACCESS = [
  {
    area: 'Career explorer', endpoint: '/api/careers',
    roles: { ADMIN: true, STUDENT: true, MOE: false, MOL: false, UNIVERSITY: false },
  },
  {
    area: 'Labour market', endpoint: '/api/labour',
    roles: { ADMIN: true, STUDENT: false, MOE: true, MOL: true, UNIVERSITY: false },
  },
  {
    area: 'Education supply', endpoint: '/api/education',
    roles: { ADMIN: true, STUDENT: false, MOE: true, MOL: false, UNIVERSITY: false },
  },
  {
    area: 'Institution', endpoint: '/api/institution',
    roles: { ADMIN: true, STUDENT: false, MOE: false, MOL: false, UNIVERSITY: true },
  },
  {
    area: 'Market demand', endpoint: '/api/market',
    roles: { ADMIN: true, STUDENT: true, MOE: true, MOL: true, UNIVERSITY: true },
  },
  {
    area: 'Enrolment intelligence', endpoint: '/api/enrollment',
    roles: { ADMIN: true, STUDENT: true, MOE: true, MOL: false, UNIVERSITY: true },
  },
  {
    area: 'Recommendations', endpoint: '/api/recommendations',
    roles: { ADMIN: true, STUDENT: true, MOE: true, MOL: false, UNIVERSITY: true },
  },
  {
    area: 'Model monitoring', endpoint: '/api/monitoring',
    roles: { ADMIN: true, STUDENT: false, MOE: false, MOL: false, UNIVERSITY: false },
  },
  {
    area: 'Global search', endpoint: '/api/search',
    roles: { ADMIN: true, STUDENT: true, MOE: true, MOL: true, UNIVERSITY: true },
  },
]

const ROLE_ORDER = ['ADMIN', 'STUDENT', 'MOE', 'MOL', 'UNIVERSITY']

export default function AdminUsersPage() {
  const { data, loading, error, refetch } = useFetch(getRoles)
  const roles = data ?? []

  return (
    <div>
      <SectionHeader
        title="Accounts &amp; permissions"
        subtitle="The roles the platform defines and what each one can reach"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading roles…" height={240} />}

      {roles.length > 0 && (
        <>
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Roles</p>
            <p className="panel-sub">Landing page is served by the API, not hard-coded in the client</p>
            <div className="au-roles">
              {roles.map(r => (
                <div key={r.role} className="au-role">
                  <p className="au-role-label">{r.label}</p>
                  <p className="au-role-code">{r.role}</p>
                  <p className="au-role-home">{r.home}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Permission matrix</p>
            <p className="panel-sub">
              Enforced server-side. A blocked request returns 403 regardless of
              what the client shows.
            </p>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Area</th>
                    <th style={{ textAlign: 'left' }}>Endpoint</th>
                    {ROLE_ORDER.map(r => <th key={r}>{r}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {ACCESS.map(a => (
                    <tr key={a.area}>
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>{a.area}</td>
                      <td style={{ textAlign: 'left' }}>
                        <code className="au-code">{a.endpoint}</code>
                      </td>
                      {ROLE_ORDER.map(r => (
                        <td key={r}>
                          {/* Symbol + colour, never colour alone */}
                          <span style={{
                            color: a.roles[r] ? 'var(--green)' : 'var(--text-muted)',
                            fontWeight: 700,
                          }}>
                            {a.roles[r] ? '✓' : '—'}
                          </span>
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <DataNote tone="caution">
            <strong>Demo accounts.</strong> The five seeded accounts share the
            password set in <code>DEMO_PASSWORD</code> and are created only when the
            users table is empty. Rotate that value and re-seed before exposing this
            deployment to anyone. User creation and deletion are not available in
            this build — accounts are provisioned at startup.
          </DataNote>
        </>
      )}

      <style>{`
        .au-roles {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 12px;
        }
        .au-role {
          border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px;
        }
        .au-role-label { font-size: 13.5px; font-weight: 600; color: var(--navy); }
        .au-role-code {
          font-family: 'IBM Plex Mono', monospace; font-size: 11px;
          color: var(--text-muted); margin-top: 2px;
        }
        .au-role-home {
          font-family: 'IBM Plex Mono', monospace; font-size: 11px;
          color: var(--blue); margin-top: 6px;
        }
        .au-code {
          font-family: 'IBM Plex Mono', monospace; font-size: 11.5px;
          background: var(--page); border-radius: 5px; padding: 2px 6px;
          color: var(--text-secondary);
        }
        .table-scroll th {
          text-align: center; padding: 8px 12px; font-size: 10.5px; font-weight: 600;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em;
          border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 9px 12px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); text-align: center; font-size: 12.5px;
        }
      `}</style>
    </div>
  )
}
