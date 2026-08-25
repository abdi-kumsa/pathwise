import { NavLink } from 'react-router-dom'

const module1Links = [
  {
    to: '/market/overview',
    label: 'Overview',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="17" y="4" width="4" height="16" rx="1"/></svg>
  },
  {
    to: '/market/hiring',
    label: 'Hiring analytics',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
  },
  {
    to: '/market/skill-gap',
    label: 'Skill gap',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
  },
  {
    to: '/market/regional',
    label: 'Regional map',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z"/><circle cx="12" cy="10" r="3"/></svg>
  },
  {
    to: '/market/forecast',
    label: 'Forecast',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>
  },
]

const module2Links = [
  {
    to: '/enrollment/trends',
    label: 'Enrollment trends',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
  },
  {
    to: '/enrollment/risk',
    label: 'Admission risk',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v4"/><path d="M12 17h.01"/><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z"/></svg>
  },
  {
    to: '/enrollment/placements',
    label: 'Placements',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>
  },
  {
    to: '/enrollment/student',
    label: 'Student evaluator',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h4"/><path d="M9 21V9a2 2 0 0 1 2-2h6l4 4v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2Z"/></svg>
  },
  {
    to: '/enrollment/skill-roadmap',
    label: 'Skill roadmap',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg>
  },
]

function NavSection({ title, links }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <div style={{
        fontSize: '11px',
        fontWeight: '600',
        letterSpacing: '0.07em',
        color: '#64748B',
        textTransform: 'uppercase',
        padding: '10px 12px 8px'
      }}>
        {title}
      </div>
      {links.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => isActive ? 'nav-item active' : 'nav-item'}
        >
          <span className="nav-icon">{icon}</span>
          {label}
        </NavLink>
      ))}
    </div>
  )
}

const module3Links = [
  {
    to: '/recommendations/salary',
    label: 'Salary forecast',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
  },
  {
    to: '/recommendations/escape',
    label: 'Escape routes',
    icon: <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M9 18l6-6-6-6"/></svg>
  },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">P</div>
        <div>
          <div className="brand-name">PathWise</div>
          <div className="brand-tag">Analytics</div>
        </div>
      </div>

      <nav style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
        <NavSection title="Module 1 — Market demand" links={module1Links} />
        <NavSection title="Module 2 — Enrollment intel" links={module2Links} />
        <NavSection title="Module 3 — Recommendations" links={module3Links} />
      </nav>

      <div className="sidebar-footer">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="sf-avatar">AB</div>
          <div>
            <div className="sf-name">Abdi Kumsa</div>
            <div className="sf-role">Program Director</div>
          </div>
        </div>
      </div>

      <style>{`
        .sidebar {
          width: 264px;
          flex-shrink: 0;
          background: var(--navy);
          padding: 28px 16px 24px;
          display: flex;
          flex-direction: column;
          gap: 28px;
          height: 100vh;
          position: fixed;
          left: 0;
          top: 0;
        }
        .brand {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 0 8px 20px;
          border-bottom: 1px solid rgba(255,255,255,0.08);
        }
        .brand-mark {
          width: 34px;
          height: 34px;
          border-radius: 9px;
          background: linear-gradient(155deg, var(--blue), #1D4ED8);
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'Sora', sans-serif;
          font-weight: 700;
          font-size: 15px;
          color: var(--white);
        }
        .brand-name {
          font-family: 'Sora', sans-serif;
          font-weight: 600;
          font-size: 16px;
          color: var(--white);
          letter-spacing: -0.01em;
        }
        .brand-tag {
          font-size: 11px;
          color: var(--blue);
          font-weight: 600;
          letter-spacing: 0.04em;
          text-transform: uppercase;
        }
        .nav-item {
          display: flex;
          align-items: center;
          gap: 11px;
          padding: 10px 12px;
          border-radius: 8px;
          color: #B6C0D4;
          font-size: 14px;
          font-weight: 500;
          text-decoration: none;
          position: relative;
          transition: background .15s ease, color .15s ease;
        }
        .nav-item:hover {
          background: rgba(255,255,255,0.05);
          color: var(--white);
        }
        .nav-icon {
          width: 17px;
          height: 17px;
          flex-shrink: 0;
          opacity: 0.85;
          display: flex;
          align-items: center;
        }
        .nav-item.active {
          background: var(--navy-700);
          color: var(--white);
        }
        .nav-item.active::before {
          content: "";
          position: absolute;
          left: -16px;
          top: 6px;
          bottom: 6px;
          width: 3px;
          background: var(--blue);
          border-radius: 0 3px 3px 0;
        }
        .nav-item.active .nav-icon {
          opacity: 1;
          color: var(--blue);
        }
        .sidebar-footer {
          margin-top: auto;
          padding: 12px;
          border-radius: 10px;
          background: rgba(255,255,255,0.04);
          border: 1px solid rgba(255,255,255,0.06);
        }
        .sf-avatar {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          background: var(--blue);
          color: #fff;
          font-family: 'Sora', sans-serif;
          font-weight: 600;
          font-size: 13px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .sf-name {
          font-size: 13px;
          color: var(--white);
          font-weight: 500;
        }
        .sf-role {
          font-size: 11.5px;
          color: #7C8AA5;
        }
      `}</style>
    </aside>
  )
}
