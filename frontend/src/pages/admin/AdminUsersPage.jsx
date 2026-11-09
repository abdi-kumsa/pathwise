import { useState, useEffect, useCallback } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import Modal from '../../components/Modal'
import { useAuth } from '../../context/AuthContext'
import {
  listUsers, createUser, updateUser, resetPassword,
  deactivateUser, reactivateUser, getInstitutionOptions,
} from '../../api/users'
import { getRoles } from '../../api/auth'

/**
 * Account administration.
 *
 * The guards that matter (self-lockout, last-admin, institution pairing) are
 * enforced by the API, not here — this layer disables the controls that would
 * fail so the reason is visible before the click, rather than surfacing as an
 * error afterwards.
 */

const ROLE_TONE = {
  ADMIN:      { bg: '#EDE9FE', fg: '#6D28D9' },
  STUDENT:    { bg: '#EAF1FE', fg: '#2563EB' },
  MOE:        { bg: '#E7F7F0', fg: '#0E9F6E' },
  MOL:        { bg: '#FEF3C7', fg: '#B45309' },
  UNIVERSITY: { bg: '#FEE9DC', fg: '#C2410C' },
}

const ACCESS = [
  { area: 'Career explorer',       endpoint: '/api/careers',         roles: { ADMIN: 1, STUDENT: 1 } },
  { area: 'Labour market',         endpoint: '/api/labour',          roles: { ADMIN: 1, MOE: 1, MOL: 1 } },
  { area: 'Education supply',      endpoint: '/api/education',       roles: { ADMIN: 1, MOE: 1 } },
  { area: 'Institution',           endpoint: '/api/institution',     roles: { ADMIN: 1, UNIVERSITY: 1 } },
  { area: 'Market demand',         endpoint: '/api/market',          roles: { ADMIN: 1, STUDENT: 1, MOE: 1, MOL: 1, UNIVERSITY: 1 } },
  { area: 'Enrolment intelligence',endpoint: '/api/enrollment',      roles: { ADMIN: 1, STUDENT: 1, MOE: 1, UNIVERSITY: 1 } },
  { area: 'Recommendations',       endpoint: '/api/recommendations', roles: { ADMIN: 1, STUDENT: 1, MOE: 1, UNIVERSITY: 1 } },
  { area: 'Model monitoring',      endpoint: '/api/monitoring',      roles: { ADMIN: 1 } },
  { area: 'User management',       endpoint: '/api/users',           roles: { ADMIN: 1 } },
  { area: 'Global search',         endpoint: '/api/search',          roles: { ADMIN: 1, STUDENT: 1, MOE: 1, MOL: 1, UNIVERSITY: 1 } },
]

const ROLE_ORDER = ['ADMIN', 'STUDENT', 'MOE', 'MOL', 'UNIVERSITY']

const fmtDate = (iso) => {
  if (!iso) return '—'
  try { return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) }
  catch { return '—' }
}

function RoleBadge({ role }) {
  const t = ROLE_TONE[role] ?? { bg: '#F1F5F9', fg: '#475569' }
  return <span className="u-role" style={{ background: t.bg, color: t.fg }}>{role}</span>
}

// ── Create / edit form ────────────────────────────────────────────────────────

function UserForm({ mode, initial, roles, institutions, onSubmit, onCancel, busy, error }) {
  const editing = mode === 'edit'
  const [form, setForm] = useState({
    username:     initial?.username ?? '',
    password:     '',
    role:         initial?.role ?? 'STUDENT',
    displayName:  initial?.display_name ?? '',
    institution:  initial?.institution_name ?? '',
  })

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))
  const needsInstitution = form.role === 'UNIVERSITY'

  const invalid =
    (!editing && (!/^[a-z0-9_.-]{3,64}$/.test(form.username) || form.password.length < 8)) ||
    !form.displayName.trim() ||
    (needsInstitution && !form.institution)

  return (
    <form onSubmit={e => { e.preventDefault(); if (!invalid) onSubmit(form) }}>
      {error && <p className="mf-error">{error}</p>}

      <label className="mf-label" htmlFor="uf-username">Username</label>
      <input
        id="uf-username"
        className="mf-input"
        value={form.username}
        onChange={e => set('username', e.target.value.toLowerCase())}
        disabled={editing}
        autoComplete="off"
        required
      />
      <p className="mf-hint">
        {editing
          ? 'Usernames cannot be changed — the sign-in token is bound to it.'
          : 'Lowercase letters, digits, dot, dash or underscore. 3–64 characters.'}
      </p>

      {!editing && (
        <>
          <label className="mf-label" htmlFor="uf-password">Initial password</label>
          <input
            id="uf-password"
            className="mf-input"
            type="password"
            value={form.password}
            onChange={e => set('password', e.target.value)}
            autoComplete="new-password"
            required
          />
          <p className="mf-hint">
            At least 8 characters. Share it with the user and ask them to change
            it from their account page.
          </p>
        </>
      )}

      <label className="mf-label" htmlFor="uf-name">Display name</label>
      <input
        id="uf-name"
        className="mf-input"
        value={form.displayName}
        onChange={e => set('displayName', e.target.value)}
        required
      />

      <label className="mf-label" htmlFor="uf-role">Role</label>
      <select
        id="uf-role"
        className="mf-select"
        value={form.role}
        onChange={e => set('role', e.target.value)}
      >
        {roles.map(r => <option key={r.role} value={r.role}>{r.label}</option>)}
      </select>

      {needsInstitution && (
        <>
          <label className="mf-label" htmlFor="uf-inst">Institution</label>
          <select
            id="uf-inst"
            className="mf-select"
            value={form.institution}
            onChange={e => set('institution', e.target.value)}
            required
          >
            <option value="">Select an institution…</option>
            {institutions.map(i => (
              <option key={i.name} value={i.name}>{i.name} · {i.type}, {i.state}</option>
            ))}
          </select>
          <p className="mf-hint">
            A University account only ever sees this institution's data.
          </p>
        </>
      )}

      <div className="mf-actions">
        <button type="button" className="mf-btn" onClick={onCancel} disabled={busy}>Cancel</button>
        <button type="submit" className="mf-btn mf-btn-primary" disabled={busy || invalid}>
          {busy ? 'Saving…' : editing ? 'Save changes' : 'Create account'}
        </button>
      </div>
    </form>
  )
}

// ── Reset password form ───────────────────────────────────────────────────────

function ResetForm({ username, onSubmit, onCancel, busy, error }) {
  const [pw, setPw] = useState('')
  const [confirm, setConfirm] = useState('')
  const mismatch = confirm.length > 0 && pw !== confirm
  const invalid = pw.length < 8 || mismatch

  return (
    <form onSubmit={e => { e.preventDefault(); if (!invalid) onSubmit(pw) }}>
      {error && <p className="mf-error">{error}</p>}

      <label className="mf-label" htmlFor="rp-new">New password</label>
      <input id="rp-new" className="mf-input" type="password" value={pw}
             onChange={e => setPw(e.target.value)} autoComplete="new-password" required />

      <label className="mf-label" htmlFor="rp-confirm">Confirm</label>
      <input id="rp-confirm" className="mf-input" type="password" value={confirm}
             onChange={e => setConfirm(e.target.value)} autoComplete="new-password" required />
      {mismatch && <p className="mf-hint" style={{ color: 'var(--red)' }}>Passwords do not match.</p>}

      <p className="mf-hint">
        {username} will be signed out on their next request and must use this
        password. Share it through a channel you trust.
      </p>

      <div className="mf-actions">
        <button type="button" className="mf-btn" onClick={onCancel} disabled={busy}>Cancel</button>
        <button type="submit" className="mf-btn mf-btn-primary" disabled={busy || invalid}>
          {busy ? 'Saving…' : 'Set password'}
        </button>
      </div>
    </form>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AdminUsersPage() {
  const { user: me } = useAuth()

  const [users, setUsers] = useState([])
  const [roles, setRoles] = useState([])
  const [institutions, setInstitutions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const [dialog, setDialog] = useState(null)   // {kind:'create'|'edit'|'reset', user?}
  const [busy, setBusy] = useState(false)
  const [formError, setFormError] = useState(null)
  const [notice, setNotice] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [u, r, i] = await Promise.all([listUsers(), getRoles(), getInstitutionOptions()])
      setUsers(u); setRoles(r); setInstitutions(i)
    } catch (e) {
      setError(e?.message ?? 'Could not load accounts')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const close = () => { setDialog(null); setFormError(null) }

  const run = async (fn, successMessage) => {
    setBusy(true)
    setFormError(null)
    try {
      await fn()
      await load()
      close()
      if (successMessage) {
        setNotice(successMessage)
        setTimeout(() => setNotice(null), 4000)
      }
    } catch (e) {
      setFormError(e?.message ?? 'That did not work')
    } finally {
      setBusy(false)
    }
  }

  const activeAdmins = users.filter(u => u.role === 'ADMIN' && u.is_active).length

  /** Why a row's destructive actions are unavailable, or null if they are fine. */
  const blockedReason = (u) => {
    if (u.username === me?.username) return 'You cannot deactivate or demote your own account.'
    if (u.role === 'ADMIN' && u.is_active && activeAdmins <= 1) {
      return 'This is the only active administrator. Promote another account first.'
    }
    return null
  }

  return (
    <div>
      <SectionHeader
        title="Accounts &amp; permissions"
        subtitle="Create accounts, set roles, reset passwords and revoke access"
      />

      {error && <ErrorBanner message={error} onRetry={load} />}
      {notice && <div className="u-notice">{notice}</div>}

      {loading ? (
        <LoadingSpinner message="Loading accounts…" height={260} />
      ) : (
        <>
          <div className="panel" style={{ marginBottom: 20 }}>
            <div className="u-head">
              <div>
                <p className="panel-title">Accounts</p>
                <p className="panel-sub">
                  {users.filter(u => u.is_active).length} active
                  {users.some(u => !u.is_active) &&
                    ` · ${users.filter(u => !u.is_active).length} deactivated`}
                </p>
              </div>
              <button className="mf-btn mf-btn-primary" onClick={() => setDialog({ kind: 'create' })}>
                Add account
              </button>
            </div>

            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Username</th>
                    <th style={{ textAlign: 'left' }}>Name</th>
                    <th style={{ textAlign: 'left' }}>Role</th>
                    <th style={{ textAlign: 'left' }}>Institution</th>
                    <th style={{ textAlign: 'left' }}>Status</th>
                    <th style={{ textAlign: 'left' }}>Created</th>
                    <th style={{ textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map(u => {
                    const isMe = u.username === me?.username
                    const reason = blockedReason(u)
                    return (
                      <tr key={u.username} className={u.is_active ? '' : 'u-inactive'}>
                        <td style={{ textAlign: 'left' }}>
                          <span className="u-name">{u.username}</span>
                          {isMe && <span className="u-you">you</span>}
                        </td>
                        <td style={{ textAlign: 'left' }}>{u.display_name}</td>
                        <td style={{ textAlign: 'left' }}><RoleBadge role={u.role} /></td>
                        <td style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>
                          {u.institution_name ?? '—'}
                          {u.cross_institution && (
                            <span className="u-you" title="May read other institutions' data; every read is audited">
                              cross-institution
                            </span>
                          )}
                        </td>
                        <td style={{ textAlign: 'left' }}>
                          {/* Colour plus the word — status never reads by colour alone */}
                          <span className="u-status" style={{
                            color: u.is_active ? 'var(--green)' : 'var(--text-muted)',
                            background: u.is_active ? 'var(--green-bg)' : '#F1F5F9',
                          }}>
                            {u.is_active ? 'Active' : 'Deactivated'}
                          </span>
                        </td>
                        <td style={{ textAlign: 'left', color: 'var(--text-muted)' }}>
                          {fmtDate(u.created_at)}
                        </td>
                        <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                          <button className="u-act" onClick={() => setDialog({ kind: 'edit', user: u })}>
                            Edit
                          </button>
                          <button className="u-act" onClick={() => setDialog({ kind: 'reset', user: u })}>
                            Reset password
                          </button>
                          {u.role === 'UNIVERSITY' && (
                            <button
                              className="u-act"
                              title="SCOPE.UNI.R2: allow this account to read other institutions. Audited."
                              onClick={() => {
                                const grant = !u.cross_institution
                                if (grant && !window.confirm(
                                  `Allow ${u.username} to read every other institution's data? Each read is audited.`
                                )) return
                                run(
                                  () => updateUser(u.username, { crossInstitution: grant }),
                                  grant ? `Cross-institution access granted to ${u.username}.`
                                        : `Cross-institution access revoked for ${u.username}.`,
                                )
                              }}
                            >
                              {u.cross_institution ? 'Revoke cross-access' : 'Grant cross-access'}
                            </button>
                          )}
                          {u.is_active ? (
                            <button
                              className="u-act u-act-danger"
                              disabled={!!reason}
                              title={reason ?? 'Deactivate this account'}
                              onClick={() => run(
                                () => deactivateUser(u.username),
                                `${u.username} deactivated.`,
                              )}
                            >
                              Deactivate
                            </button>
                          ) : (
                            <button
                              className="u-act"
                              onClick={() => run(
                                () => reactivateUser(u.username),
                                `${u.username} reactivated.`,
                              )}
                            >
                              Reactivate
                            </button>
                          )}
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Permission matrix</p>
            <p className="panel-sub">
              Enforced server-side. A blocked request returns 403 regardless of
              what the interface shows.
            </p>

            <div className="table-scroll">
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Area</th>
                    <th style={{ textAlign: 'left' }}>Endpoint</th>
                    {ROLE_ORDER.map(r => <th key={r} style={{ textAlign: 'center' }}>{r}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {ACCESS.map(a => (
                    <tr key={a.area}>
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>{a.area}</td>
                      <td style={{ textAlign: 'left' }}><code className="u-code">{a.endpoint}</code></td>
                      {ROLE_ORDER.map(r => (
                        <td key={r} style={{ textAlign: 'center' }}>
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
            <strong>Retire the demo accounts before this is used for real.</strong>{' '}
            The five seeded accounts share the password from <code>DEMO_PASSWORD</code>.
            Create your own administrator, sign in as them, then deactivate the
            seeded ones — the platform keeps at least one active administrator at
            all times, so do it in that order. This list is a stamped JSON object
            (not a bare array).
          </DataNote>
        </>
      )}

      {/* ── Dialogs ─────────────────────────────────────────────────────── */}

      <Modal
        open={dialog?.kind === 'create'}
        title="Add account"
        subtitle="The new user can change their own password once they sign in."
        onClose={close}
      >
        <UserForm
          mode="create"
          roles={roles}
          institutions={institutions}
          busy={busy}
          error={formError}
          onCancel={close}
          onSubmit={(f) => run(
            () => createUser({
              username: f.username, password: f.password, role: f.role,
              displayName: f.displayName, institution: f.institution,
            }),
            `${f.username} created.`,
          )}
        />
      </Modal>

      <Modal
        open={dialog?.kind === 'edit'}
        title={`Edit ${dialog?.user?.username ?? ''}`}
        onClose={close}
      >
        <UserForm
          mode="edit"
          initial={dialog?.user}
          roles={roles}
          institutions={institutions}
          busy={busy}
          error={formError}
          onCancel={close}
          onSubmit={(f) => run(
            () => updateUser(dialog.user.username, {
              role: f.role, displayName: f.displayName, institution: f.institution,
            }),
            `${dialog.user.username} updated.`,
          )}
        />
      </Modal>

      <Modal
        open={dialog?.kind === 'reset'}
        title={`Reset password for ${dialog?.user?.username ?? ''}`}
        onClose={close}
        width={420}
      >
        <ResetForm
          username={dialog?.user?.username}
          busy={busy}
          error={formError}
          onCancel={close}
          onSubmit={(pw) => run(
            () => resetPassword(dialog.user.username, pw),
            `Password reset for ${dialog.user.username}.`,
          )}
        />
      </Modal>

      <style>{`
        .u-head {
          display: flex; align-items: flex-start; justify-content: space-between;
          gap: 16px; flex-wrap: wrap; margin-bottom: 10px;
        }
        .u-notice {
          font-size: 13px; color: var(--green); background: var(--green-bg);
          border: 1px solid #BFE9D6; border-radius: 10px;
          padding: 10px 13px; margin-bottom: 16px;
        }
        .u-name { font-weight: 600; color: var(--navy); }
        .u-you {
          font-size: 10px; font-weight: 700; text-transform: uppercase;
          letter-spacing: .04em; color: var(--blue); background: var(--blue-light);
          border-radius: 4px; padding: 1px 5px; margin-left: 7px;
        }
        .u-role {
          display: inline-block; border-radius: 5px; padding: 2px 8px;
          font-size: 10.5px; font-weight: 700; letter-spacing: .03em;
        }
        .u-status {
          display: inline-block; border-radius: 5px; padding: 2px 9px;
          font-size: 11px; font-weight: 600;
        }
        .u-inactive td { opacity: .55; }
        .u-inactive .u-status { opacity: 1; }
        .u-act {
          background: none; border: none; font-family: inherit; font-size: 12px;
          color: var(--blue); cursor: pointer; padding: 4px 7px; border-radius: 6px;
          font-weight: 500;
        }
        .u-act:hover:not(:disabled) { background: var(--blue-light); }
        .u-act-danger { color: var(--red); }
        .u-act-danger:hover:not(:disabled) { background: var(--red-bg); }
        .u-act:disabled { color: var(--text-muted); cursor: not-allowed; }
        .u-code {
          font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 11.5px;
          background: var(--page); border-radius: 5px; padding: 2px 6px;
          color: var(--text-secondary);
        }
        .table-scroll th {
          padding: 8px 12px; font-size: 10.5px; font-weight: 600;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em;
          border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 10px 12px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); font-size: 12.5px;
        }
      `}</style>
    </div>
  )
}
