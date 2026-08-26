import { useState } from 'react'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/client'
import { setToken } from '../api/client'

/**
 * Self-registration for STUDENT accounts.
 *
 * Ministry, university and admin accounts are provisioned by an administrator —
 * no role picker here, students only. The endpoint signs them in immediately
 * rather than making them re-type credentials.
 */
export default function SignUpPage() {
  const { user, booting, setUser } = useAuth()
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  // Already signed in — go to their home.
  if (!booting && user) {
    return <Navigate to={user.home ?? '/'} replace />
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const { data } = await apiClient.post('/api/auth/signup', {
        username: username.trim(),
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
    <div className="login-page">
      {/* Same animated background as login */}
      <div className="login-bg" aria-hidden="true">
        <span className="orb orb-1" />
        <span className="orb orb-2" />
        <span className="orb orb-3" />
        <span className="orb orb-4" />
        <span className="orb orb-5" />
        <span className="dots dots-tr" />
        <span className="dots dots-bl" />
        <svg className="arcs" viewBox="0 0 400 400" preserveAspectRatio="none">
          {[0, 1, 2, 3, 4].map(i => (
            <path
              key={i}
              d={`M ${400 - i * 34} 400 Q ${400 - i * 34} ${210 - i * 26} ${170 - i * 30} ${118 - i * 22}`}
              fill="none"
              stroke="rgba(147, 197, 253, 0.16)"
              strokeWidth="1"
            />
          ))}
        </svg>
      </div>

      <div className="login-card">
        <div className="login-brand">
          <div className="login-mark">P</div>
          <div>
            <div className="login-wordmark">PathWise</div>
            <div className="login-tagline">Market &amp; Enrolment Intelligence</div>
          </div>
        </div>

        <h1 className="login-title">Create your account 👋</h1>
        <p className="login-sub">Join PathWise and explore career pathways</p>

        <form onSubmit={submit}>
          <label className="login-label" htmlFor="su-name">Your name</label>
          <input
            id="su-name"
            className="login-input"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            placeholder="How should we address you?"
            autoFocus
            required
          />

          <label className="login-label" htmlFor="su-username">Username</label>
          <input
            id="su-username"
            className="login-input"
            value={username}
            onChange={e => setUsername(e.target.value.toLowerCase())}
            placeholder="Lowercase letters, digits, dot, dash or underscore"
            autoComplete="username"
            required
          />

          <label className="login-label" htmlFor="su-password">Password</label>
          <input
            id="su-password"
            className="login-input"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="At least 8 characters"
            autoComplete="new-password"
            required
          />

          {error && <p className="login-error" role="alert">{error}</p>}

          <button
            className="login-submit"
            type="submit"
            disabled={busy || !username || !password || !displayName}
          >
            {busy ? 'Creating account…' : 'Sign up'}
          </button>
        </form>

        <p className="login-foot">
          Already have an account? <Link to="/login" className="login-link">Sign in</Link>
        </p>
      </div>

      {/* Reuse the login page styles — same background, same card, same inputs */}
      <style>{`
        .login-page {
          position: relative;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 32px 20px;
          overflow: hidden;
          background:
            radial-gradient(1200px 800px at 78% 62%, #14356B 0%, rgba(20,53,107,0) 62%),
            radial-gradient(900px 700px at 12% 18%, #12305F 0%, rgba(18,48,95,0) 58%),
            linear-gradient(135deg, #060F21 0%, #0A1B37 45%, #0C214A 100%);
          background-color: #08172E;
        }

        .login-bg {
          position: absolute;
          inset: 0;
          pointer-events: none;
          overflow: hidden;
        }

        .orb {
          position: absolute;
          border-radius: 50%;
          will-change: transform;
        }

        .orb-1 {
          width: 460px; height: 460px;
          left: -190px; top: -170px;
          background: radial-gradient(circle at 34% 30%,
            rgba(59,130,246,0.30) 0%, rgba(37,99,235,0.16) 45%, rgba(30,64,175,0) 72%);
          animation: drift-a 22s ease-in-out infinite;
        }

        .orb-2 {
          width: 34px; height: 34px;
          left: 9.5%; top: 12%;
          background: linear-gradient(150deg, #5B9BF8 0%, #2563EB 55%, #1D4ED8 100%);
          box-shadow: 0 8px 26px rgba(37,99,235,0.55);
          animation: drift-b 13s ease-in-out infinite;
        }

        .orb-3 {
          width: 108px; height: 108px;
          right: 9%; top: 40%;
          background: linear-gradient(155deg, #4F8DF5 0%, #2563EB 48%, #16337A 100%);
          box-shadow: 0 20px 60px rgba(29,78,216,0.45);
          animation: drift-c 18s ease-in-out infinite;
        }

        .orb-4 {
          width: 380px; height: 380px;
          left: -120px; bottom: -160px;
          background: radial-gradient(circle at 60% 40%,
            rgba(37,99,235,0.26) 0%, rgba(30,58,138,0.12) 48%, rgba(15,23,42,0) 74%);
          animation: drift-d 26s ease-in-out infinite;
        }

        .orb-5 {
          width: 18px; height: 18px;
          right: 22%; bottom: 16%;
          background: linear-gradient(150deg, #7CB0FA 0%, #3B82F6 100%);
          box-shadow: 0 6px 18px rgba(59,130,246,0.5);
          animation: drift-b 16s ease-in-out infinite reverse;
        }

        @keyframes drift-a {
          0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
          50%      { transform: translate3d(26px, 34px, 0) scale(1.05); }
        }
        @keyframes drift-b {
          0%, 100% { transform: translate3d(0, 0, 0); }
          33%      { transform: translate3d(16px, -22px, 0); }
          66%      { transform: translate3d(-12px, -10px, 0); }
        }
        @keyframes drift-c {
          0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
          50%      { transform: translate3d(-22px, 28px, 0) scale(1.04); }
        }
        @keyframes drift-d {
          0%, 100% { transform: translate3d(0, 0, 0); }
          50%      { transform: translate3d(30px, -24px, 0); }
        }

        .dots {
          position: absolute;
          background-image: radial-gradient(rgba(147,197,253,0.42) 1.4px, transparent 1.4px);
          background-size: 19px 19px;
        }
        .dots-tr { width: 190px; height: 150px; right: 5.5%; top: 5%; }
        .dots-bl { width: 165px; height: 130px; left: 4%;  bottom: 9%; }

        .arcs {
          position: absolute;
          right: 0; bottom: 0;
          width: 420px; height: 420px;
          opacity: 0.9;
        }

        .login-card {
          position: relative;
          z-index: 1;
          width: 100%;
          max-width: 430px;
          background: #FFFFFF;
          border-radius: 18px;
          padding: 40px 42px 34px;
          box-shadow:
            0 30px 70px rgba(3, 12, 30, 0.42),
            0 2px 6px rgba(3, 12, 30, 0.20);
        }

        .login-brand {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 30px;
        }
        .login-mark {
          width: 46px; height: 46px;
          border-radius: 12px;
          background: linear-gradient(155deg, #3B82F6, #1D4ED8);
          display: flex; align-items: center; justify-content: center;
          font-family: 'Sora', sans-serif;
          font-weight: 700; font-size: 21px; color: #fff;
          flex-shrink: 0;
          box-shadow: 0 6px 18px rgba(37,99,235,0.32);
        }
        .login-wordmark {
          font-family: 'Sora', sans-serif;
          font-weight: 700; font-size: 19px;
          color: var(--navy); letter-spacing: -0.015em;
          line-height: 1.15;
        }
        .login-tagline {
          font-size: 10.5px; font-weight: 700;
          color: var(--blue);
          letter-spacing: 0.075em; text-transform: uppercase;
          margin-top: 2px;
        }

        .login-title {
          font-family: 'Sora', sans-serif;
          font-size: 30px; font-weight: 700;
          color: var(--navy); letter-spacing: -0.025em;
          line-height: 1.1;
        }
        .login-sub {
          font-size: 14px; color: var(--text-secondary);
          margin: 8px 0 26px;
        }

        .login-label {
          display: block; font-size: 13px; font-weight: 600;
          color: var(--navy); margin-bottom: 8px;
        }
        .login-input {
          width: 100%; font-size: 14px; padding: 13px 14px;
          border: 1px solid #E2E8F0; border-radius: 10px;
          margin-bottom: 20px; color: var(--navy); background: #FFFFFF;
          font-family: inherit;
          transition: border-color .15s ease, box-shadow .15s ease;
        }
        .login-input::placeholder { color: #94A3B8; }
        .login-input:focus {
          outline: none; border-color: var(--blue);
          box-shadow: 0 0 0 3px rgba(59,130,246,0.16);
        }

        .login-error { font-size: 13px; color: var(--red); margin-bottom: 14px; }

        .login-submit {
          width: 100%; padding: 14px; border-radius: 10px; border: none;
          background: linear-gradient(135deg, #3B82F6, #2563EB);
          color: #fff; font-size: 15px; font-weight: 600;
          font-family: 'Sora', sans-serif; cursor: pointer;
          transition: filter .15s ease, transform .1s ease, box-shadow .15s ease;
          box-shadow: 0 8px 22px rgba(37,99,235,0.30);
        }
        .login-submit:hover:not(:disabled) {
          filter: brightness(1.07);
          box-shadow: 0 10px 26px rgba(37,99,235,0.38);
        }
        .login-submit:active:not(:disabled) { transform: translateY(1px); }
        .login-submit:disabled {
          background: #94A3B8; box-shadow: none; cursor: not-allowed;
        }

        .login-foot {
          font-size: 12px; color: var(--text-muted);
          text-align: center; margin-top: 22px;
        }
        .login-link {
          color: var(--blue); font-weight: 600; text-decoration: none;
        }
        .login-link:hover { text-decoration: underline; }

        @media (max-width: 560px) {
          .login-card { padding: 30px 24px 26px; border-radius: 16px; }
          .login-title { font-size: 26px; }
          .arcs { width: 260px; height: 260px; }
          .dots-tr, .dots-bl { display: none; }
          .orb-3 { width: 76px; height: 76px; right: 4%; }
        }

        @media (prefers-reduced-motion: reduce) {
          .orb { animation: none !important; }
          .login-submit { transition: none; }
        }
      `}</style>
    </div>
  )
}
