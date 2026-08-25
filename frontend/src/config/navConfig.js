/**
 * Role -> sidebar sections.
 *
 * Replaces the three hard-coded link arrays that used to live in Sidebar.jsx.
 * The sidebar now renders whatever the signed-in user's role maps to here, so
 * adding a page for one role never touches another role's navigation.
 *
 * Route paths must stay in step with the route table in App.jsx and with
 * ROLE_HOME in backend/services/auth_service.py, which decides where each role
 * lands after login.
 */

// Icons are plain path data so this file stays JS, not JSX — the Sidebar wraps
// each one in an <svg>. Keeps the config importable from tests without JSX.
export const ICONS = {
  compass:    'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm4.2 5.8-2.5 6-6 2.5 2.5-6 6-2.5Z',
  bars:       'M3 12h4v8H3zM10 8h4v12h-4zM17 4h4v16h-4z',
  trend:      'M3 3v18h18M18.7 8 13 13.7l-3-3L4 16.5',
  scales:     'M12 3v18M7 7l-4 7h8ZM17 7l-4 7h8ZM6 21h12',
  gap:        'M22 12h-4l-3 9L9 3l-3 9H2',
  map:        'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0ZM12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z',
  grid:       'M3 3h8v8H3zM13 3h8v8h-8zM3 13h8v8H3zM13 13h8v8h-8z',
  building:   'M3 21h18M5 21V7l8-4v18M19 21V11l-6-4',
  funnel:     'M3 4h18l-7 8v7l-4 2v-9L3 4Z',
  users:      'M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8',
  student:    'M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5',
  target:     'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20ZM12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12ZM12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z',
  money:      'M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6',
  route:      'M9 18l6-6-6-6',
  check:      'M20 6 9 17l-5-5',
  shield:     'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z',
  activity:   'M22 12h-4l-3 9L9 3l-3 9H2',
  alert:      'M12 9v4M12 17h.01M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z',
}

const STUDENT = [
  {
    title: 'Plan your path',
    links: [
      { to: '/student/careers',       label: 'Career explorer',   icon: ICONS.compass },
      { to: '/student/evaluator',     label: 'Placement odds',    icon: ICONS.student },
      { to: '/student/skill-roadmap', label: 'Skill roadmap',     icon: ICONS.target },
    ],
  },
  {
    title: 'Explore options',
    links: [
      { to: '/student/alternatives',  label: 'Alternative paths', icon: ICONS.route },
      { to: '/student/salary',        label: 'Salary outlook',    icon: ICONS.money },
      { to: '/student/market',        label: 'Job market',        icon: ICONS.bars },
    ],
  },
]

const MOL = [
  {
    title: 'Labour market',
    links: [
      { to: '/mol/overview',      label: 'Overview',             icon: ICONS.bars },
      { to: '/mol/emerging',      label: 'Emerging occupations', icon: ICONS.trend },
      { to: '/mol/supply-demand', label: 'Supply & demand gap',  icon: ICONS.scales },
    ],
  },
  {
    title: 'Workforce quality',
    links: [
      { to: '/mol/mismatch', label: 'Skills mismatch',  icon: ICONS.gap },
      { to: '/mol/regional', label: 'Regional demand',  icon: ICONS.map },
    ],
  },
]

const MOE = [
  {
    title: 'Education supply',
    links: [
      { to: '/moe/overview',     label: 'Overview',        icon: ICONS.bars },
      { to: '/moe/fields',       label: 'Field explorer',  icon: ICONS.grid },
    ],
  },
  {
    title: 'Investment planning',
    links: [
      { to: '/moe/quadrant',   label: 'Investment matrix',   icon: ICONS.target },
      { to: '/moe/priorities', label: 'Investment priority', icon: ICONS.trend },
      { to: '/moe/labour',     label: 'Labour demand',       icon: ICONS.scales },
    ],
  },
]

const UNIVERSITY = [
  {
    title: 'My institution',
    links: [
      { to: '/university/overview',  label: 'Overview',           icon: ICONS.building },
      { to: '/university/portfolio', label: 'Programme portfolio', icon: ICONS.grid },
    ],
  },
  {
    title: 'Planning',
    links: [
      { to: '/university/expansion', label: 'Expansion',        icon: ICONS.trend },
      { to: '/university/resources', label: 'Resource efficiency', icon: ICONS.funnel },
      { to: '/university/benchmark', label: 'Peer benchmark',   icon: ICONS.scales },
      { to: '/university/enrollment', label: 'Enrolment forecast', icon: ICONS.activity },
    ],
  },
]

const ADMIN = [
  {
    title: 'Platform',
    links: [
      { to: '/admin/overview',   label: 'Overview',      icon: ICONS.grid },
      { to: '/admin/monitoring', label: 'Model monitoring', icon: ICONS.alert },
      { to: '/admin/users',      label: 'Accounts',      icon: ICONS.users },
    ],
  },
  {
    title: 'Ministry views',
    links: [
      { to: '/mol/overview',      label: 'Labour market',    icon: ICONS.bars },
      { to: '/mol/supply-demand', label: 'Supply & demand',  icon: ICONS.scales },
      { to: '/mol/mismatch',      label: 'Skills mismatch',  icon: ICONS.gap },
      { to: '/moe/quadrant',      label: 'Investment matrix', icon: ICONS.target },
      { to: '/moe/priorities',    label: 'Investment priority', icon: ICONS.trend },
    ],
  },
  {
    title: 'Institution & student',
    links: [
      { to: '/university/overview',  label: 'Institution',     icon: ICONS.building },
      { to: '/university/expansion', label: 'Expansion',       icon: ICONS.activity },
      { to: '/student/careers',      label: 'Career explorer', icon: ICONS.compass },
      { to: '/student/evaluator',    label: 'Placement odds',  icon: ICONS.student },
    ],
  },
]

const NAV_BY_ROLE = {
  ADMIN,
  STUDENT,
  MOE,
  MOL,
  UNIVERSITY,
}

/** Sidebar sections for a role. Unknown or missing role gets an empty nav. */
export function navFor(role) {
  return NAV_BY_ROLE[role] ?? []
}

/** Every route a role may reach — used by tests and the route table. */
export function routesFor(role) {
  return navFor(role).flatMap(section => section.links.map(l => l.to))
}

export default NAV_BY_ROLE
