import { useState } from 'react'

import SectionHeader from '../components/SectionHeader'
import { useAuth } from '../context/AuthContext'
import { changeOwnPassword } from '../api/users'

/**
 * Your own account — available to every role.
 *
 * This is what makes the seeded demo passwords rotatable by the person who
 * actually holds them, rather than only by an administrator.
 */
export default function AccountPage() {
  const { user, logout } = useAuth()

  const [current, setCurrent] = useState('')
  const [next, setNext] = useState('')
  const [confirm, setConfirm] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [done, setDone] = useState(false)

  const tooShort = next.length > 0 && next.length < 8
  const mismatch = confirm.length > 0 && next !== confirm
  const sameAsOld = next.length > 0 && next === current
  const invalid = !current || next.length < 8 || next !== confirm || sameAsOld

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      await changeOwnPassword(current, next)
      setDone(true)
      setCurrent(''); setNext(''); setConfirm('')
    } catch (err) {
      setError(err?.message ?? 'Could not change your password')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <SectionHeader title="Your account" subtitle="Your identity and sign-in details" />

      <div className="card-grid-2">
        <div className="panel">
          <p className="panel-title">Identity</p>
          <p className="panel-sub">Ask an administrator if any of this needs to change</p>

          <dl className="acct-list">
            <div><dt>Username</dt><dd>{user?.username}</dd></div>
            <div><dt>Display name</dt><dd>{user?.display_name}</dd></div>
            <div><dt>Role</dt><dd>{user?.role_label ?? user?.role}</dd></div>
            {user?.institution && (
              <div><dt>Institution</dt><dd>{user.institution}</dd></div>
            )}
          </dl>

          <button className="acct-signout" onClick={logout}>Sign out</button>
        </div>

        <div className="panel">
          <p className="panel-title">Change password</p>
          <p className="panel-sub">
            You will stay signed in on this device. Other sessions keep working
            until they expire.
          </p>

          {done ? (
            <div>
              <p className="mf-ok">
                Password changed. Use the new one next time you sign in.
              </p>
              <button className="mf-btn" onClick={() => setDone(false)}>
                Change it again
              </button>
            </div>
          ) : (
            <form onSubmit={submit}>
              {error && <p className="mf-error">{error}</p>}

              <label className="mf-label" htmlFor="ac-current">Current password</label>
              <input id="ac-current" className="mf-input" type="password"
                     value={current} onChange={e => setCurrent(e.target.value)}
                     autoComplete="current-password" required />

              <label className="mf-label" htmlFor="ac-new">New password</label>
              <input id="ac-new" className="mf-input" type="password"
                     value={next} onChange={e => setNext(e.target.value)}
                     autoComplete="new-password" required />
              {tooShort && <p className="acct-warn">At least 8 characters.</p>}
              {sameAsOld && <p className="acct-warn">Must be different from your current password.</p>}

              <label className="mf-label" htmlFor="ac-confirm">Confirm new password</label>
              <input id="ac-confirm" className="mf-input" type="password"
                     value={confirm} onChange={e => setConfirm(e.target.value)}
                     autoComplete="new-password" required />
              {mismatch && <p className="acct-warn">Passwords do not match.</p>}

              <div className="mf-actions">
                <button type="submit" className="mf-btn mf-btn-primary" disabled={busy || invalid}>
                  {busy ? 'Saving…' : 'Change password'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>

      <style>{`
        .acct-list { display: flex; flex-direction: column; gap: 10px; }
        .acct-list div {
          display: flex; justify-content: space-between; gap: 12px;
          padding-bottom: 10px; border-bottom: 1px solid #F4F6FA;
        }
        .acct-list dt { font-size: 12.5px; color: var(--text-muted); }
        .acct-list dd { font-size: 13px; color: var(--navy); font-weight: 600; }
        .acct-signout {
          margin-top: 16px; background: none; border: 1px solid var(--border);
          border-radius: 9px; padding: 9px 16px; font-size: 13px;
          font-family: inherit; color: var(--navy); cursor: pointer;
        }
        .acct-signout:hover { background: var(--page); }
        .acct-warn { font-size: 11.5px; color: var(--red); margin: -10px 0 14px; }

        /* The .mf-* classes come from components/Modal.jsx, which is always
           mounted in the admin console but not here — restate the few used. */
        .mf-label {
          display: block; font-size: 12px; font-weight: 600;
          color: var(--navy); margin-bottom: 6px;
        }
        .mf-input {
          width: 100%; font-size: 13.5px; padding: 9px 11px;
          border: 1px solid var(--border); border-radius: 9px;
          color: var(--navy); background: var(--white);
          font-family: inherit; margin-bottom: 14px;
        }
        .mf-input:focus {
          outline: none; border-color: var(--blue);
          box-shadow: 0 0 0 3px var(--blue-light);
        }
        .mf-error {
          font-size: 12.5px; color: var(--red); background: var(--red-bg);
          border-radius: 8px; padding: 9px 11px; margin-bottom: 14px; line-height: 1.5;
        }
        .mf-ok {
          font-size: 12.5px; color: var(--green); background: var(--green-bg);
          border-radius: 8px; padding: 9px 11px; margin-bottom: 14px;
        }
        .mf-actions { display: flex; gap: 9px; justify-content: flex-end; padding-top: 4px; }
        .mf-btn {
          padding: 9px 16px; border-radius: 9px; font-size: 13.5px;
          font-weight: 600; font-family: 'Sora', sans-serif; cursor: pointer;
          border: 1px solid var(--border); background: var(--white); color: var(--navy);
        }
        .mf-btn-primary { background: var(--blue); border-color: var(--blue); color: #fff; }
        .mf-btn:disabled { opacity: .55; cursor: not-allowed; }
      `}</style>
    </div>
  )
}
