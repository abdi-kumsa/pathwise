import { useState } from 'react'
import { useNavigate, useLocation, Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

// Shown on the page so the platform is demonstrable without a credentials
// handout. These are seeded demo accounts, not production users — see
// backend/startup_seed.py and the warning in SETUP_GUIDE.md.
const DEMO_ACCOUNTS = [
  { username: 'student',    label: 'Student',              blurb: 'Find which department leads to a target job' },
  { username: 'mol',        label: 'Ministry of Labour',   blurb: 'Emerging occupations and workforce shortfalls' },
  { username: 'moe',        label: 'Ministry of Education', blurb: 'Where to invest in new education capacity' },
  { username: 'university', label: 'University',           blurb: 'Portfolio, expansion and resource efficiency' },
  { username: 'admin',      label: 'Administrator',        blurb: 'Everything, plus model monitoring' },
]

const DEMO_PASSWORD = 'pathwise123'

export default function LoginPage() {
  const { login, user, booting } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const expired = new URLSearchParams(location.search).get('expired') === '1'

  // Already signed in — go straight to the role's home.
  if (!booting && user) {
    return <Navigate to={user.home ?? '/'} replace />
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const me = await login(username.trim(), password)
      navigate(location.state?.from ?? me.home ?? '/', { replace: true })
    } catch (err) {
      setError(err?.message ?? 'Sign in failed')
    } finally {
      setBusy(false)
    }
  }

  const fillDemo = (name) => {
    setUsername(name)
    setPassword(DEMO_PASSWORD)
    setError(null)
  }

  return (
    <div className="login-page">
      <div className="login-card">
        {/* ── Form ───────────────────────────────────────────────────────── */}
        <div className="login-form-side">
          <div className="brand" style={{ border: 'none', padding: '0 0 24px' }}>
            <div className="brand-mark">P</div>
            <div>
              <div className="brand-name" style={{ color: 'var(--navy)' }}>PathWise</div>
              <div className="brand-tag">Market &amp; Enrolment Intelligence</div>
            </div>
          </div>

          <h1 className="login-title">Sign in</h1>
          <p className="login-sub">Your dashboard is built from your role.</p>

          {expired && (
            <div className="login-note">Your session expired. Please sign in again.</div>
          )}

          <form onSubmit={submit}>
            <label className="login-label" htmlFor="username">Username</label>
            <input
              id="username"
              className="login-input"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
              required
            />

            <label className="login-label" htmlFor="password">Password</label>
            <input
              id="password"
              className="login-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />

            {error && <p className="login-error" role="alert">{error}</p>}

            <button className="login-submit" type="submit" disabled={busy || !username || !password}>
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        {/* ── Demo accounts ──────────────────────────────────────────────── */}
        <div className="login-demo-side">
          <p className="login-demo-title">Demo accounts</p>
          <p className="login-demo-sub">
            Select one to fill the form. Password is <code>{DEMO_PASSWORD}</code> for all.
          </p>

          <div className="login-demo-list">
            {DEMO_ACCOUNTS.map(a => (
              <button
                key={a.username}
                type="button"
                className={`login-demo-item${username === a.username ? ' selected' : ''}`}
                onClick={() => fillDemo(a.username)}
              >
                <span className="login-demo-role">{a.label}</span>
                <span className="login-demo-blurb">{a.blurb}</span>
              </button>
            ))}
          </div>

          <p className="login-demo-foot">
            Demo credentials only — rotate <code>DEMO_PASSWORD</code> before any real deployment.
          </p>
        </div>
      </div>

      <style>{`
        .login-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(150deg, #0F172A 0%, #1E293B 55%, #24365C 100%);
          padding: 24px;
        }
        .login-card {
          width: 100%;
          max-width: 940px;
          background: var(--white);
          border-radius: 18px;
          box-shadow: var(--shadow-pop);
          display: grid;
          grid-template-columns: 1fr 1fr;
          overflow: hidden;
        }
        .login-form-side { padding: 40px 44px 44px; }
        .login-title {
          font-family: 'Sora', sans-serif;
          font-size: 24px; font-weight: 600; color: var(--navy);
          letter-spacing: -0.015em;
        }
        .login-sub { font-size: 13.5px; color: var(--text-secondary); margin: 6px 0 22px; }
        .login-note {
          font-size: 12.5px; color: var(--amber);
          background: var(--amber-bg); border-radius: 8px;
          padding: 9px 12px; margin-bottom: 16px;
        }
        .login-label {
          display: block; font-size: 12.5px; font-weight: 600;
          color: var(--navy); margin-bottom: 6px;
        }
        .login-input {
          width: 100%; font-size: 14px; padding: 11px 13px;
          border: 1px solid var(--border); border-radius: 9px;
          margin-bottom: 16px; color: var(--navy); background: var(--white);
          font-family: inherit;
        }
        .login-input:focus {
          outline: none; border-color: var(--blue);
          box-shadow: 0 0 0 3px var(--blue-light);
        }
        .login-error { font-size: 13px; color: var(--red); margin-bottom: 12px; }
        .login-submit {
          width: 100%; padding: 12px; border-radius: 10px; border: none;
          background: var(--blue); color: #fff; font-size: 14px; font-weight: 600;
          font-family: 'Sora', sans-serif; cursor: pointer; transition: background .15s ease;
        }
        .login-submit:hover:not(:disabled) { background: #2563EB; }
        .login-submit:disabled { background: #94A3B8; cursor: not-allowed; }

        .login-demo-side {
          background: var(--page);
          border-left: 1px solid var(--border);
          padding: 40px 36px 44px;
          display: flex; flex-direction: column;
        }
        .login-demo-title {
          font-family: 'Sora', sans-serif; font-size: 14px;
          font-weight: 600; color: var(--navy);
        }
        .login-demo-sub { font-size: 12.5px; color: var(--text-secondary); margin: 6px 0 16px; }
        .login-demo-sub code, .login-demo-foot code {
          font-family: 'IBM Plex Mono', monospace; font-size: 11.5px;
          background: var(--white); border: 1px solid var(--border);
          border-radius: 5px; padding: 1px 5px;
        }
        .login-demo-list { display: flex; flex-direction: column; gap: 8px; }
        .login-demo-item {
          text-align: left; background: var(--white);
          border: 1px solid var(--border); border-radius: 10px;
          padding: 10px 13px; cursor: pointer; display: flex;
          flex-direction: column; gap: 2px; font-family: inherit;
          transition: border-color .15s ease, box-shadow .15s ease;
        }
        .login-demo-item:hover { border-color: var(--blue); }
        .login-demo-item.selected {
          border-color: var(--blue); box-shadow: 0 0 0 3px var(--blue-light);
        }
        .login-demo-role { font-size: 13px; font-weight: 600; color: var(--navy); }
        .login-demo-blurb { font-size: 11.5px; color: var(--text-muted); }
        .login-demo-foot {
          margin-top: auto; padding-top: 18px;
          font-size: 11.5px; color: var(--text-muted); line-height: 1.5;
        }

        @media (max-width: 820px) {
          .login-card { grid-template-columns: 1fr; max-width: 460px; }
          .login-form-side { padding: 32px 28px 24px; }
          .login-demo-side { border-left: none; border-top: 1px solid var(--border); padding: 24px 28px 32px; }
        }
      `}</style>
    </div>
  )
}
