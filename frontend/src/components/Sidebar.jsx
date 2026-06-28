import { NavLink } from 'react-router-dom'

const module1Links = [
  { to: '/market/overview',    label: 'Overview' },
  { to: '/market/hiring',      label: 'Hiring Analytics' },
  { to: '/market/skill-gap',   label: 'Skill Gap' },
  { to: '/market/forecast',    label: 'Forecast' },
]

const module2Links = [
  { to: '/enrollment/trends',     label: 'Enrollment Trends' },
  { to: '/enrollment/risk',       label: 'Admission Risk' },
  { to: '/enrollment/placements', label: 'Placements' },
  { to: '/enrollment/student',    label: 'Student Evaluator' },
]

function NavSection({ title, links }) {
  return (
    <div className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-widest text-slate-400 px-4 mb-2">
        {title}
      </p>
      <ul>
        {links.map(({ to, label }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `block px-4 py-2 text-sm rounded-md mx-2 mb-0.5 transition-colors ${
                  isActive
                    ? 'bg-indigo-600 text-white font-medium'
                    : 'text-slate-300 hover:bg-slate-700 hover:text-white'
                }`
              }
            >
              {label}
            </NavLink>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Sidebar() {
  return (
    <aside className="fixed top-0 left-0 h-screen w-60 bg-slate-900 flex flex-col overflow-y-auto z-10">
      <div className="px-4 py-5 border-b border-slate-700">
        <span className="text-white font-bold text-lg tracking-tight">PathWise</span>
        <span className="ml-2 text-xs text-indigo-400 font-medium">Analytics</span>
      </div>

      <nav className="flex-1 pt-5">
        <NavSection title="Module 1 — Market Demand" links={module1Links} />
        <NavSection title="Module 2 — Enrollment Intel" links={module2Links} />
      </nav>

      <div className="px-4 py-4 border-t border-slate-700">
        <p className="text-xs text-slate-500">PathWise v0.1.0</p>
      </div>
    </aside>
  )
}
