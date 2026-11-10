/**
 * Role -> sidebar sections.
 *
 * Replaces the three hard-coded link arrays that used to live in Sidebar.jsx.
 * The sidebar now renders whatever the signed-in user's role maps to here, so
 * adding a page for one role never touches another role's navigation.
 *
 * Labels name the question a page answers ("Where demand outruns graduates"),
 * not the model or layer that answers it. Page titles repeat the label, so
 * the sidebar and the page always agree.
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
    title: 'Your field',
    links: [
      { to: '/student/profile',           label: 'Your profile and eligibility', icon: ICONS.student },
      { to: '/student/outlook',           label: 'Jobs outlook for your field',  icon: ICONS.trend },
      { to: '/student/demand-comparison', label: 'Students vs jobs, by field',   icon: ICONS.scales },
      { to: '/student/alignment',         label: 'Where your field has room',    icon: ICONS.target },
      { to: '/student/gap',               label: 'Shortage or oversupply',       icon: ICONS.gap },
    ],
  },
  {
    title: 'Your options',
    links: [
      { to: '/student/alternatives',   label: 'Alternative fields',            icon: ICONS.route },
      { to: '/student/skill-roadmap',  label: 'Skills to add',                 icon: ICONS.check },
      { to: '/student/pathways',       label: 'Programme to occupation paths', icon: ICONS.map },
      { to: '/student/opportunities',  label: 'Opportunities and alerts',      icon: ICONS.alert },
    ],
  },
]

const MOL = [
  {
    title: 'Labour market',
    links: [
      { to: '/mol/overview',         label: 'Labour market today',     icon: ICONS.bars },
      { to: '/mol/formal-informal',  label: 'Formal vs informal work', icon: ICONS.users },
      { to: '/mol/forecast',         label: 'Where demand is heading', icon: ICONS.trend },
      { to: '/mol/mismatch',         label: 'Where skills fall short', icon: ICONS.grid },
    ],
  },
  {
    title: 'Supply into the market',
    links: [
      { to: '/mol/public',     label: 'Public-sector hiring',            icon: ICONS.building },
      { to: '/mol/fdi',        label: 'Investment and industrial parks', icon: ICONS.map },
      { to: '/mol/absorption', label: 'How fast graduates find work',    icon: ICONS.check },
      { to: '/mol/migration',  label: 'Migration and labour pressure',   icon: ICONS.route },
      { to: '/mol/report',     label: 'Workforce planning report',       icon: ICONS.activity },
    ],
  },
]

const MOE = [
  {
    title: 'Supply and demand',
    links: [
      { to: '/moe/overview',     label: 'National snapshot',               icon: ICONS.bars },
      { to: '/moe/constraints',  label: 'Where capacity caps demand',      icon: ICONS.scales },
      { to: '/moe/gap',          label: 'Where demand outruns graduates',  icon: ICONS.gap },
      { to: '/moe/simulator',    label: 'Test a policy change',            icon: ICONS.activity },
    ],
  },
  {
    title: 'Where to invest',
    links: [
      { to: '/moe/priorities',    label: 'Which fields to grow first',    icon: ICONS.trend },
      { to: '/moe/regions',       label: 'Which regions are misaligned',  icon: ICONS.map },
      { to: '/moe/institutions',  label: 'How institutions compare',      icon: ICONS.building },
      { to: '/moe/impact',        label: 'What past policy changed',      icon: ICONS.alert },
    ],
  },
]

const UNIVERSITY = [
  {
    title: 'Your institution',
    links: [
      { to: '/university/overview',    label: 'Overview',                      icon: ICONS.building },
      { to: '/university/portfolio',   label: 'Which programmes are healthy',  icon: ICONS.grid },
      { to: '/university/demand',      label: 'How many will apply',           icon: ICONS.trend },
      { to: '/university/constrained', label: 'How many you can enrol',        icon: ICONS.activity },
      { to: '/university/three-way',   label: 'Do programmes match jobs',      icon: ICONS.scales },
    ],
  },
  {
    title: 'From admission to work',
    links: [
      { to: '/university/funnel',      label: 'Where applicants drop out',          icon: ICONS.funnel },
      { to: '/university/cohort',      label: 'Who progresses, who repeats',        icon: ICONS.users },
      { to: '/university/outcomes',    label: 'Where graduates end up',             icon: ICONS.check },
      { to: '/university/curriculum',  label: 'Which skills the curriculum misses', icon: ICONS.target },
      { to: '/university/resources',   label: 'Where to put resources',             icon: ICONS.money },
    ],
  },
]

const ADMIN = [
  {
    title: 'Platform',
    links: [
      { to: '/admin/overview',   label: 'Platform health',   icon: ICONS.grid },
      { to: '/admin/pipeline',   label: 'Data pipeline',     icon: ICONS.activity },
      { to: '/admin/quality',    label: 'Data quality',      icon: ICONS.alert },
      { to: '/admin/monitoring', label: 'Model monitoring',  icon: ICONS.trend },
      { to: '/admin/users',      label: 'Accounts',          icon: ICONS.users },
    ],
  },
  {
    title: 'Governance',
    links: [
      { to: '/admin/scenarios', label: 'Scenarios',  icon: ICONS.shield },
      { to: '/admin/audit',     label: 'Audit log',  icon: ICONS.check },
    ],
  },
  {
    title: 'Methodology',
    links: [
      { to: '/admin/methodology', label: 'Importance and weights', icon: ICONS.scales },
    ],
  },
  {
    title: 'Ministry views',
    links: [
      { to: '/mol/overview',      label: 'Labour market today',            icon: ICONS.bars },
      { to: '/mol/forecast',      label: 'Where demand is heading',        icon: ICONS.trend },
      { to: '/mol/mismatch',      label: 'Where skills fall short',        icon: ICONS.gap },
      { to: '/mol/report',        label: 'Workforce planning report',      icon: ICONS.activity },
      { to: '/moe/overview',      label: 'National snapshot',              icon: ICONS.building },
      { to: '/moe/priorities',    label: 'Which fields to grow first',     icon: ICONS.trend },
      { to: '/moe/simulator',     label: 'Test a policy change',           icon: ICONS.target },
    ],
  },
  {
    title: 'Institution and student',
    links: [
      { to: '/university/overview',  label: 'Institution overview',          icon: ICONS.building },
      { to: '/university/portfolio', label: 'Which programmes are healthy',  icon: ICONS.grid },
      { to: '/university/three-way', label: 'Do programmes match jobs',      icon: ICONS.scales },
      { to: '/student/profile',      label: 'Student profile',               icon: ICONS.student },
      { to: '/student/alternatives', label: 'Alternative fields',            icon: ICONS.route },
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
