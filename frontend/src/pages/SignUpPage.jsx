import { useState } from 'react'
import { useNavigate, Navigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import apiClient from '../api/client'
import { setToken } from '../api/client'
import { User, Lock, Mail, ArrowRight, Loader2, Info, X } from 'lucide-react'

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
  const [infoNotice, setInfoNotice] = useState(null)
  const [busy, setBusy] = useState(false)

  // Already signed in — go to their home.
  if (!booting && user) {
    return <Navigate to={user.home ?? '/'} replace />
  }

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setInfoNotice(null)
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

  const handleGoogleSignUp = () => {
    setInfoNotice('Google Single Sign-On (SSO) is scheduled for an upcoming release. Please create your student account using the form.')
  }

  return (
    <div className="login-page">
      <div className="login-bg" aria-hidden="true">
        <span className="orb orb-1" />
        <span className="orb orb-2" />
        <span className="orb orb-3" />
        <span className="orb orb-4" />
        <span className="orb orb-5" />
        <span className="dots dots-tr" />
        <span className="dots dots-bl" />
        <svg className="waves" viewBox="0 0 520 420" preserveAspectRatio="none">
          {[0, 1, 2, 3, 4, 5].map(i => (
            <path
              key={i}
              d={`M ${520 - i * 28} 420
                  C ${480 - i * 30} ${280 - i * 18},
                    ${360 - i * 26} ${160 - i * 16},
                    ${210 - i * 24} ${70 - i * 10}`}
              fill="none"
              stroke="rgba(147, 197, 253, 0.18)"
              strokeWidth="1.2"
            />
          ))}
        </svg>
      </div>

      <div className="login-card">
        <div className="login-left">
          <div className="login-brand">
            <div className="login-mark">P</div>
            <div>
              <div className="login-wordmark">PathWise</div>
              <div className="login-tagline">Market &amp; Enrolment Intelligence</div>
            </div>
          </div>

          <h1 className="login-title">Create your account 👋</h1>
          <p className="login-sub">Join PathWise and explore career pathways</p>

          {infoNotice && (
            <div className="login-info-notice" role="status">
              <Info size={16} className="login-info-icon" />
              <span>{infoNotice}</span>
              <button
                type="button"
                className="login-info-close"
                onClick={() => setInfoNotice(null)}
                aria-label="Dismiss notice"
              >
                <X size={14} />
              </button>
            </div>
          )}

          <form onSubmit={submit} className="login-form">
            <label className="login-label" htmlFor="su-name">Your name</label>
            <div className="login-input-wrap">
              <User className="login-input-icon" size={18} strokeWidth={1.8} />
              <input
                id="su-name"
                className="login-input"
                value={displayName}
                onChange={e => setDisplayName(e.target.value)}
                placeholder="How should we address you?"
                autoFocus
                required
              />
            </div>

            <label className="login-label" htmlFor="su-username">Username</label>
            <div className="login-input-wrap">
              <Mail className="login-input-icon" size={18} strokeWidth={1.8} />
              <input
                id="su-username"
                className="login-input"
                value={username}
                onChange={e => setUsername(e.target.value.toLowerCase().replace(/\s+/g, ''))}
                placeholder="Lowercase letters, digits, dot, dash or underscore"
                autoComplete="username"
                required
              />
            </div>

            <label className="login-label" htmlFor="su-password">Password</label>
            <div className="login-input-wrap">
              <Lock className="login-input-icon" size={18} strokeWidth={1.8} />
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
            </div>

            {error && <p className="login-error" role="alert">{error}</p>}

            <button
              className="login-submit"
              type="submit"
              disabled={busy || !username || !password || !displayName}
            >
              {busy ? (
                <>
                  <Loader2 className="login-submit-spinner" size={18} />
                  <span>Creating account…</span>
                </>
              ) : (
                <>
                  <span>Sign up</span>
                  <ArrowRight className="login-submit-arrow" size={18} strokeWidth={2.2} />
                </>
              )}
            </button>
          </form>

          <div className="login-divider">
            <span>or</span>
          </div>

          <button className="login-google" type="button" onClick={handleGoogleSignUp}>
            <svg className="login-google-icon" viewBox="0 0 24 24" width="20" height="20">
              <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Sign up with Google
          </button>

          <p className="login-foot">
            Already have an account? <Link to="/login" className="login-link">Sign in</Link>
          </p>
        </div>

        <div className="login-right" aria-hidden="true">
          <div className="login-illustration">
            <img
              src="/login-illustration.png"
              alt=""
              className="login-illustration-img"
            />
          </div>

          <div className="login-security">
            <svg className="login-shield" viewBox="0 0 24 24" width="22" height="22">
              <path
                fill="#2563EB"
                d="M12 2.1 20 5.4v6.2c0 5.1-3.4 9.6-8 10.8-4.6-1.2-8-5.7-8-10.8V5.4L12 2.1Z"
              />
              <path
                fill="none"
                stroke="#fff"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M8.6 12.1 11 14.5l4.6-4.8"
              />
            </svg>
            <span>Your data is secure and encrypted</span>
          </div>
        </div>
      </div>

      <style>{`
        .login-page {
          position: relative;
          min-height: 100dvh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 32px 20px;
          overflow: hidden;
          background:
            radial-gradient(1100px 760px at 78% 64%, #163A73 0%, rgba(22,58,115,0) 60%),
            radial-gradient(820px 640px at 10% 16%, #12325F 0%, rgba(18,50,95,0) 58%),
            linear-gradient(135deg, #06101F 0%, #0A1B38 46%, #0C214C 100%);
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
          width: 480px; height: 480px;
          left: -200px; top: -180px;
          background: radial-gradient(circle at 34% 30%,
            rgba(59,130,246,0.32) 0%, rgba(37,99,235,0.16) 44%, rgba(30,64,175,0) 72%);
          animation: drift-a 22s ease-in-out infinite;
        }

        .orb-2 {
          width: 32px; height: 32px;
          left: 9%; top: 11%;
          background: linear-gradient(150deg, #5B9BF8 0%, #2563EB 55%, #1D4ED8 100%);
          box-shadow: 0 8px 24px rgba(37,99,235,0.5);
          animation: drift-b 13s ease-in-out infinite;
        }

        .orb-3 {
          width: 96px; height: 96px;
          right: 8%; top: 38%;
          background: linear-gradient(155deg, #4F8DF5 0%, #2563EB 48%, #16337A 100%);
          box-shadow: 0 18px 50px rgba(29,78,216,0.42);
          animation: drift-c 18s ease-in-out infinite;
        }

        .orb-4 {
          width: 360px; height: 360px;
          left: -110px; bottom: -150px;
          background: radial-gradient(circle at 60% 40%,
            rgba(37,99,235,0.24) 0%, rgba(30,58,138,0.1) 48%, rgba(15,23,42,0) 74%);
          animation: drift-d 26s ease-in-out infinite;
        }

        .orb-5 {
          width: 16px; height: 16px;
          right: 22%; bottom: 15%;
          background: linear-gradient(150deg, #7CB0FA 0%, #3B82F6 100%);
          box-shadow: 0 6px 16px rgba(59,130,246,0.48);
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
          background-image: radial-gradient(rgba(147,197,253,0.4) 1.35px, transparent 1.35px);
          background-size: 18px 18px;
        }
        .dots-tr { width: 180px; height: 140px; right: 5%; top: 5%; }
        .dots-bl { width: 170px; height: 140px; left: 3.5%; bottom: 8%; }

        .waves {
          position: absolute;
          right: 0; bottom: 0;
          width: 460px; height: 380px;
        }

        .login-card {
          position: relative;
          z-index: 1;
          width: 100%;
          max-width: 1020px;
          background: #FFFFFF;
          border-radius: 24px;
          display: grid;
          grid-template-columns: 1fr 1fr;
          min-height: 640px;
          box-shadow:
            0 28px 64px rgba(3, 12, 30, 0.38),
            0 2px 6px rgba(3, 12, 30, 0.16);
          overflow: hidden;
        }

        .login-left {
          padding: 44px 48px 36px;
          display: flex;
          flex-direction: column;
        }

        .login-right {
          background: #F3F5FA;
          padding: 36px 36px 28px;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .login-brand {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 36px;
        }
        .login-mark {
          width: 44px; height: 44px;
          border-radius: 12px;
          background: linear-gradient(155deg, #3B82F6, #1D4ED8);
          display: flex; align-items: center; justify-content: center;
          font-family: 'Sora', sans-serif;
          font-weight: 700; font-size: 20px; color: #fff;
          flex-shrink: 0;
          box-shadow: 0 6px 16px rgba(37,99,235,0.28);
        }
        .login-wordmark {
          font-family: 'Sora', sans-serif;
          font-weight: 700; font-size: 18px;
          color: #0F172A; letter-spacing: -0.02em;
          line-height: 1.15;
        }
        .login-tagline {
          font-size: 10px; font-weight: 700;
          color: #3B82F6;
          letter-spacing: 0.08em; text-transform: uppercase;
          margin-top: 3px;
        }

        .login-title {
          font-family: 'Sora', sans-serif;
          font-size: 32px; font-weight: 700;
          color: #0F172A; letter-spacing: -0.03em;
          line-height: 1.1;
        }
        .login-sub {
          font-size: 14.5px; color: #64748B;
          margin: 8px 0 26px;
        }

        .login-info-notice {
          display: flex;
          align-items: flex-start;
          gap: 8px;
          font-size: 12.5px;
          color: #1E40AF;
          background: #EFF6FF;
          border: 1px solid #BFDBFE;
          border-radius: 9px;
          padding: 10px 12px;
          margin-bottom: 16px;
          line-height: 1.4;
        }
        .login-info-icon { flex-shrink: 0; margin-top: 1px; color: #3B82F6; }
        .login-info-close {
          background: none; border: none; padding: 2px;
          color: #60A5FA; cursor: pointer; margin-left: auto;
          display: flex; align-items: center; justify-content: center;
        }
        .login-info-close:hover { color: #1E40AF; }

        .login-form { display: flex; flex-direction: column; }

        .login-label {
          display: block; font-size: 13px; font-weight: 600;
          color: #0F172A; margin-bottom: 8px;
        }

        .login-input-wrap {
          position: relative;
          margin-bottom: 18px;
        }

        .login-input-icon {
          position: absolute;
          left: 14px; top: 50%;
          transform: translateY(-50%);
          color: #94A3B8;
          pointer-events: none;
        }

        .login-input {
          width: 100%; font-size: 14px;
          padding: 13px 44px 13px 44px;
          border: 1px solid #E5E7EB; border-radius: 10px;
          color: #0F172A; background: #FFFFFF;
          font-family: inherit;
          transition: border-color .15s ease, box-shadow .15s ease;
        }
        .login-input::placeholder { color: #94A3B8; }
        .login-input:focus {
          outline: none; border-color: #2563EB;
          box-shadow: 0 0 0 3px rgba(37,99,235,0.14);
        }

        .login-error {
          font-size: 12.5px;
          color: #B91C1C;
          background: #FEF2F2;
          border: 1px solid #FECACA;
          border-radius: 8px;
          padding: 8px 12px;
          margin-bottom: 12px;
        }

        .login-submit {
          position: relative;
          width: 100%; padding: 14px 48px;
          border-radius: 10px; border: none;
          background: #2563EB;
          color: #fff; font-size: 15px; font-weight: 600;
          font-family: 'Sora', sans-serif; cursor: pointer;
          transition: background .15s ease, transform .1s ease, box-shadow .15s ease;
          box-shadow: 0 8px 20px rgba(37,99,235,0.28);
          display: flex; align-items: center; justify-content: center;
          gap: 8px;
        }
        .login-submit-arrow {
          position: absolute;
          right: 18px; top: 50%;
          transform: translateY(-50%);
        }
        .login-submit-spinner {
          animation: spin 1s linear infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        .login-submit:hover:not(:disabled) {
          background: #1D4ED8;
          box-shadow: 0 10px 24px rgba(37,99,235,0.34);
        }
        .login-submit:active:not(:disabled) { transform: translateY(1px); }
        .login-submit:disabled {
          background: #93C5FD;
          box-shadow: none;
          cursor: not-allowed;
        }

        .login-divider {
          margin: 22px 0;
          text-align: center;
          position: relative;
        }
        .login-divider::before {
          content: '';
          position: absolute;
          left: 0; right: 0; top: 50%;
          height: 1px;
          background: #E5E7EB;
        }
        .login-divider span {
          display: inline-block;
          background: #fff;
          padding: 0 12px;
          font-size: 13px;
          color: #94A3B8;
          position: relative;
        }

        .login-google {
          width: 100%; padding: 12px 20px;
          border: 1px solid #E5E7EB;
          border-radius: 10px;
          background: #FFFFFF;
          color: #0F172A;
          font-size: 14.5px; font-weight: 600;
          font-family: inherit;
          cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          gap: 12px;
          transition: background .15s ease, border-color .15s ease;
        }
        .login-google:hover {
          background: #F8FAFC;
          border-color: #D1D5DB;
        }

        .login-google-icon { flex-shrink: 0; }

        .login-foot {
          font-size: 13px; color: #94A3B8;
          text-align: center; margin-top: auto;
          padding-top: 22px;
        }
        .login-link {
          color: #2563EB; font-weight: 700; text-decoration: none;
        }
        .login-link:hover { text-decoration: underline; }

        .login-illustration {
          flex: 1;
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 0;
        }

        .login-illustration-img {
          width: 108%;
          max-width: 520px;
          height: auto;
          object-fit: contain;
          animation: float-ill 7s ease-in-out infinite;
        }

        @keyframes float-ill {
          0%, 100% { transform: translateY(0); }
          50%      { transform: translateY(-8px); }
        }

        .login-security {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-top: 8px;
          font-size: 13px;
          color: #94A3B8;
          font-weight: 500;
        }

        .login-shield { flex-shrink: 0; display: block; }

        @media (max-width: 900px) {
          .login-card {
            grid-template-columns: 1fr;
            max-width: 460px;
            min-height: 0;
          }
          .login-right { display: none; }
          .login-left { padding: 36px 32px 32px; }
          .login-foot { margin-top: 24px; padding-top: 0; }
        }

        @media (max-width: 560px) {
          .login-left { padding: 28px 22px 24px; }
          .login-title { font-size: 28px; }
          .waves { width: 240px; height: 220px; }
          .dots-tr, .dots-bl { display: none; }
          .orb-3 { width: 72px; height: 72px; right: 4%; }
        }

        @media (prefers-reduced-motion: reduce) {
          .orb, .login-illustration-img { animation: none !important; }
          .login-submit, .login-google { transition: none; }
        }
      `}</style>
    </div>
  )
}
