import { NavLink } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { navFor } from '../config/navConfig'

function Icon({ d }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
         strokeLinecap="round" strokeLinejoin="round">
      <path d={d} />
    </svg>
  )
}

function NavSection({ title, links, onNavigate }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
      <div className="nav-section-title">{title}</div>
      {links.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          onClick={onNavigate}
          className={({ isActive }) => (isActive ? 'nav-item active' : 'nav-item')}
        >
          <span className="nav-icon"><Icon d={icon} /></span>
          {label}
        </NavLink>
      ))}
    </div>
  )
}

function initials(name = '') {
  return name.trim().split(/\s+/).slice(0, 2).map(w => w[0] ?? '').join('').toUpperCase() || '?'
}

export default function Sidebar({ open = false, onClose = () => {} }) {
  const { user, logout } = useAuth()
  const sections = navFor(user?.role)

  return (
    <>
      {/* Scrim — only rendered on small screens, where the sidebar is a drawer */}
      <div
        className={`sidebar-scrim${open ? ' visible' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      <aside className={`sidebar${open ? ' open' : ''}`}>
        <div className="brand">
          <div className="brand-mark">P</div>
          <div>
            <div className="brand-name">PathWise</div>
            <div className="brand-tag">{user?.role_label ?? 'Analytics'}</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {sections.map(section => (
            <NavSection
              key={section.title}
              title={section.title}
              links={section.links}
              onNavigate={onClose}
            />
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sf-row">
            {/* The name is the way into your own account — password, identity */}
            <NavLink to="/account" onClick={onClose} className="sf-identity" title="Your account">
              <div className="sf-avatar">{initials(user?.display_name)}</div>
              <div style={{ minWidth: 0 }}>
                <div className="sf-name">{user?.display_name ?? 'Not signed in'}</div>
                <div className="sf-role">{user?.institution ?? user?.role_label ?? ''}</div>
              </div>
            </NavLink>
            <button onClick={logout} className="sf-logout" title="Sign out" aria-label="Sign out">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                   strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4M16 17l5-5-5-5M21 12H9" />
              </svg>
            </button>
          </div>
        </div>
      </aside>
    </>
  )
}
