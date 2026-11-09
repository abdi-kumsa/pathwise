import { useState } from 'react'
import { useNavigate, useLocation, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './auth.css'

// Demo quick-fill is a development convenience only. `import.meta.env.DEV` is
// statically false in `vite build`, so the minifier drops the password literal
// and the whole picker from production bundles. Never ship a shared password to
// the browser: anyone who can load the login page could read it.
const DEMO_PASSWORD = import.meta.env.DEV
  ? (import.meta.env.VITE_DEMO_PASSWORD || 'pathwise123')
  : null

const DEMO_ACCOUNTS = [
  { role: 'Student', username: 'student', label: 'Student' },
  { role: 'Administrator', username: 'admin', label: 'Admin' },
  { role: 'Ministry of Education', username: 'moe', label: 'MoE' },
  { role: 'Ministry of Labour', username: 'mol', label: 'MoL' },
  { role: 'University', username: 'university', label: 'University' },
]

/** Sign in: one card, username and password, nothing the page cannot deliver. */
export default function LoginPage() {
  const { login, user, booting } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [rememberMe, setRememberMe] = useState(() => {
    try {
      return !!localStorage.getItem('pathwise.remembered_username')
    } catch {
      return false
    }
  })
  const [username, setUsername] = useState(() => {
    try {
      return localStorage.getItem('pathwise.remembered_username') || ''
    } catch {
      return ''
    }
  })
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState(null)
  const [showResetHelp, setShowResetHelp] = useState(false)
  const [busy, setBusy] = useState(false)

  const expired = new URLSearchParams(location.search).get('expired') === '1'

  if (!booting && user) {
    return <Navigate to={user.home ?? '/'} replace />
  }

  const submit = async (e) => {
    if (e) e.preventDefault()
    setBusy(true)
    setError(null)
    const cleanUser = username.trim().toLowerCase()
    try {
      const me = await login(cleanUser, password)
      try {
        if (rememberMe) {
          localStorage.setItem('pathwise.remembered_username', cleanUser)
        } else {
          localStorage.removeItem('pathwise.remembered_username')
        }
      } catch {
        // Ignore storage access errors
      }
      navigate(location.state?.from ?? me.home ?? '/', { replace: true })
    } catch (err) {
      setError(err?.message ?? 'Sign in failed. Check your username and password.')
    } finally {
      setBusy(false)
    }
  }

  const fill = (acc) => {
    setUsername(acc.username)
    setPassword(DEMO_PASSWORD ?? '')
    setError(null)
  }

  return (
    <main className="auth-page">
      <div className="auth-column">
        <header className="auth-brand">
          <span className="auth-wordmark">PathWise</span>
          <span className="auth-descriptor">Enrolment and labour-market intelligence</span>
        </header>

        <section className="auth-card" aria-labelledby="auth-title">
          <h1 id="auth-title" className="auth-title">Sign in</h1>

          {expired && (
            <p className="auth-notice" role="status">Your session expired. Sign in again to continue.</p>
          )}

          <form onSubmit={submit} className="auth-form">
            <label className="auth-label" htmlFor="username">Username</label>
            <input
              id="username"
              className="auth-input"
              value={username}
              onChange={e => setUsername(e.target.value.toLowerCase().replace(/\s+/g, ''))}
              autoComplete="username"
              autoFocus={!username}
              required
              aria-invalid={!!error}
            />

            <label className="auth-label" htmlFor="password">Password</label>
            <div className="auth-password">
              <input
                id="password"
                className="auth-input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                autoComplete="current-password"
                required
                aria-invalid={!!error}
              />
              <button
                type="button"
                className="auth-toggle"
                onClick={() => setShowPassword(v => !v)}
                aria-pressed={showPassword}
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? 'Hide' : 'Show'}
              </button>
            </div>

            <div className="auth-row">
              <label className="auth-check">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={e => setRememberMe(e.target.checked)}
                />
                <span>Remember my username</span>
              </label>
              <button
                type="button"
                className="auth-link-button"
                onClick={() => setShowResetHelp(v => !v)}
                aria-expanded={showResetHelp}
              >
                Forgot password?
              </button>
            </div>

            {showResetHelp && (
              <p className="auth-help" role="note">
                Password resets are handled by your administrator. Once signed in, you can change
                your password from your account page.
                {DEMO_PASSWORD && (
                  <> In this development build the demo accounts use <code>{DEMO_PASSWORD}</code>.</>
                )}
              </p>
            )}

            {error && <p className="auth-error" role="alert">{error}</p>}

            <button className="auth-submit" type="submit" disabled={busy || !username || !password}>
              {busy ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          {DEMO_PASSWORD && (
            <div className="auth-dev" role="group" aria-label="Development accounts">
              <span className="auth-dev-label">Development accounts</span>
              {DEMO_ACCOUNTS.map(acc => (
                <button
                  key={acc.username}
                  type="button"
                  className={`auth-dev-chip${username === acc.username ? ' active' : ''}`}
                  onClick={() => fill(acc)}
                  title={`Fill the ${acc.role} account`}
                >
                  {acc.label}
                </button>
              ))}
            </div>
          )}
        </section>

        <p className="auth-foot">
          Students can <Link to="/signup">create an account</Link>. Ministry, university and
          administrator accounts are issued by an administrator.
        </p>
      </div>
    </main>
  )
}
