import { useState } from 'react'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/client'
import { setToken } from '../api/client'
import './auth.css'

/**
 * Self-registration for STUDENT accounts.
 *
 * Ministry, university and admin accounts are provisioned by an administrator,
 * so there is no role picker here. The endpoint signs the student in
 * immediately rather than making them re-type credentials.
 */
export default function SignUpPage() {
  const { user, booting, setUser } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  // Already signed in: go to their home.
  if (!booting && user) {
    return <Navigate to={user.home ?? '/'} replace />
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { data } = await apiClient.post('/api/auth/signup', {
        username: username.trim().toLowerCase(),
        password,
        display_name: displayName.trim(),
      })
      setToken(data.access_token)
      setUser(data.user)
      navigate(data.user.home ?? '/', { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail ?? err?.message ?? 'Sign up failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-column">
        <header className="auth-brand">
          <span className="auth-wordmark">PathWise</span>
          <span className="auth-descriptor">Enrolment and labour-market intelligence</span>
        </header>

        <section className="auth-card" aria-labelledby="auth-title">
          <h1 id="auth-title" className="auth-title">Create a student account</h1>
          <p className="auth-sub">
            For prospective and current students. Ministry, university and administrator
            accounts are issued by an administrator.
          </p>

          <form onSubmit={submit} className="auth-form">
            <label className="auth-label" htmlFor="su-name">Your name</label>
            <input
              id="su-name"
              className="auth-input"
              value={displayName}
              onChange={e => setDisplayName(e.target.value)}
              autoComplete="name"
              autoFocus
              required
            />

            <label className="auth-label" htmlFor="su-username">Username</label>
            <p className="auth-hint">Lowercase letters, digits, dot, dash or underscore.</p>
            <input
              id="su-username"
              className="auth-input"
              value={username}
              onChange={e => setUsername(e.target.value.toLowerCase().replace(/\s+/g, ''))}
              autoComplete="username"
              required
            />

            <label className="auth-label" htmlFor="su-password">Password</label>
            <p className="auth-hint">At least 8 characters.</p>
            <input
              id="su-password"
              className="auth-input"
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />

            {error && <p className="auth-error" role="alert">{error}</p>}

            <button
              className="auth-submit"
              type="submit"
              disabled={busy || !username || !password || !displayName}
            >
              {busy ? 'Creating account…' : 'Create account'}
            </button>
          </form>
        </section>

        <p className="auth-foot">
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </main>
  )
}
