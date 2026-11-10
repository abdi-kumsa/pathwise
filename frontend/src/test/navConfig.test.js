/**
 * Navigation config and chart theme.
 *
 * These are the two places where a mistake is silent: a nav link pointing at a
 * route the role cannot open, or a palette hex quietly edited away from the
 * validated set.
 */
import { describe, it, expect } from 'vitest'
import NAV_BY_ROLE, { navFor, routesFor, ICONS } from '../config/navConfig'
import {
  SERIES, SERIES_ALL_PAIRS, ORDINAL_BLUE, STATUS, SEVERITY_COLOR,
  VERDICT_COLOR, FIT_COLOR, colorFor,
  fmtCompact, fmtMoney, fmtPct, fmtNum, fmtDelta, deltaDirection,
} from '../config/chartTheme'

const ROLES = ['ADMIN', 'STUDENT', 'MOE', 'MOL', 'UNIVERSITY']

// The route prefix each role's own pages live under. Admin is exempt: it is a
// superset role and deliberately links into every other role's views.
const OWN_PREFIX = {
  STUDENT:    '/student/',
  MOE:        '/moe/',
  MOL:        '/mol/',
  UNIVERSITY: '/university/',
}

describe('navConfig', () => {

  it('defines navigation for every role', () => {
    for (const role of ROLES) {
      expect(navFor(role).length, `${role} has no nav`).toBeGreaterThan(0)
    }
  })

  it('returns an empty nav for an unknown or missing role', () => {
    expect(navFor('NOT_A_ROLE')).toEqual([])
    expect(navFor(undefined)).toEqual([])
    expect(navFor(null)).toEqual([])
  })

  it('gives every link a route, a label and an icon', () => {
    for (const role of ROLES) {
      for (const section of navFor(role)) {
        expect(section.title, `${role} section missing title`).toBeTruthy()
        for (const link of section.links) {
          expect(link.to.startsWith('/'), `${role}: ${link.to} is not absolute`).toBe(true)
          expect(link.label).toBeTruthy()
          expect(link.icon, `${role}: ${link.label} has no icon`).toBeTruthy()
        }
      }
    }
  })

  it('never repeats a route within one role', () => {
    for (const role of ROLES) {
      const routes = routesFor(role)
      expect(new Set(routes).size, `${role} has duplicate routes`).toBe(routes.length)
    }
  })

  it('keeps each non-admin role inside its own route prefix', () => {
    for (const [role, prefix] of Object.entries(OWN_PREFIX)) {
      for (const route of routesFor(role)) {
        expect(route.startsWith(prefix), `${role} links outside its area: ${route}`).toBe(true)
      }
    }
  })

  it('gives admin access to every other role area', () => {
    const adminRoutes = routesFor('ADMIN').join(' ')
    for (const prefix of Object.values(OWN_PREFIX)) {
      expect(adminRoutes, `admin cannot reach ${prefix}`).toContain(prefix)
    }
  })

  it('puts profile & eligibility first for students', () => {
    expect(navFor('STUDENT')[0].links[0].to).toBe('/student/profile')
  })

  it('does not list leftover US tool routes in role nav', () => {
    const leftover = [
      '/student/careers', '/student/evaluator', '/student/salary', '/student/market',
      '/university/expansion', '/university/benchmark', '/university/enrollment',
      '/moe/fields', '/moe/quadrant', '/moe/labour',
      '/mol/emerging', '/mol/supply-demand', '/mol/regional',
    ]
    for (const role of ['STUDENT', 'UNIVERSITY', 'MOE', 'MOL']) {
      const routes = routesFor(role)
      for (const path of leftover) {
        expect(routes, `${role} still lists ${path}`).not.toContain(path)
      }
    }
  })

  it('references only icons that exist', () => {
    const known = new Set(Object.values(ICONS))
    for (const role of ROLES) {
      for (const section of navFor(role)) {
        for (const link of section.links) {
          expect(known.has(link.icon), `${link.label} uses an unknown icon`).toBe(true)
        }
      }
    }
  })

  it('exports the same object the helpers read from', () => {
    expect(navFor('STUDENT')).toBe(NAV_BY_ROLE.STUDENT)
  })
})

describe('chartTheme palette', () => {

  const HEX = /^#[0-9A-F]{6}$/i

  it('holds the validated categorical hexes in order', () => {
    // Changing these means re-running the palette validator — see the file header.
    expect(SERIES).toEqual(['#2563EB', '#EA580C', '#0E9F6E', '#D97706', '#DB2777', '#6D28D9'])
  })

  it('caps the all-pairs subset at three slots', () => {
    // Scatter and dot charts put every mark beside every other; only the first
    // three slots clear the all-pairs separation floors.
    expect(SERIES_ALL_PAIRS).toHaveLength(3)
    expect(SERIES_ALL_PAIRS).toEqual(SERIES.slice(0, 3))
  })

  it('uses well-formed hex everywhere', () => {
    const all = [
      ...SERIES, ...ORDINAL_BLUE,
      ...Object.values(STATUS), ...Object.values(SEVERITY_COLOR),
      ...Object.values(VERDICT_COLOR), ...Object.values(FIT_COLOR),
    ]
    for (const hex of all) expect(hex, `${hex} is not a hex colour`).toMatch(HEX)
  })

  it('keeps status colours out of the categorical set', () => {
    // A status colour must never be mistaken for "series 4".
    for (const s of Object.values(STATUS)) {
      expect(SERIES, `${s} is both a status and a series colour`).not.toContain(s)
    }
  })

  it('covers every severity and verdict the API can return', () => {
    for (const s of ['critical', 'high', 'moderate', 'low']) {
      expect(SEVERITY_COLOR[s], `no colour for severity ${s}`).toBeTruthy()
    }
    for (const v of ['Expand', 'Hold', 'Consolidate',
                     'Invest', 'Sustain', 'Oversupply risk', 'Review']) {
      expect(VERDICT_COLOR[v], `no colour for verdict ${v}`).toBeTruthy()
    }
    for (const f of ['Matched', 'Overeducated', 'Undereducated']) {
      expect(FIT_COLOR[f], `no colour for fit ${f}`).toBeTruthy()
    }
  })

  it('assigns colour by entity, not by render position', () => {
    const keys = ['alpha', 'beta', 'gamma']
    const beta = colorFor('beta', keys)
    // Filtering alpha out must not repaint beta.
    expect(colorFor('beta', keys)).toBe(beta)
    expect(beta).toBe(SERIES[1])
  })

  it('falls back to the first slot for an unknown key', () => {
    expect(colorFor('nope', ['a', 'b'])).toBe(SERIES[0])
  })
})

describe('chartTheme formatters', () => {

  it('compacts large numbers', () => {
    expect(fmtCompact(999)).toBe('999')
    expect(fmtCompact(1500)).toBe('1.5K')
    expect(fmtCompact(2000)).toBe('2K')
    expect(fmtCompact(25_000)).toBe('25K')
    expect(fmtCompact(2_300_000)).toBe('2.3M')
    expect(fmtCompact(4_100_000_000)).toBe('4.1B')
  })

  it('renders an em dash for missing values rather than NaN', () => {
    for (const f of [fmtCompact, fmtMoney, fmtPct, fmtNum, fmtDelta]) {
      expect(f(null)).toBe('—')
      expect(f(undefined)).toBe('—')
      expect(f(NaN)).toBe('—')
    }
  })

  it('signs deltas so direction is readable without a chart', () => {
    expect(fmtDelta(12.34)).toBe('+12.3%')
    expect(fmtDelta(-5)).toBe('-5.0%')
    expect(fmtDelta(0)).toBe('0.0%')
  })

  it('maps delta direction for KPI arrows', () => {
    expect(deltaDirection(3)).toBe('up')
    expect(deltaDirection(-3)).toBe('down')
    expect(deltaDirection(0)).toBe('neutral')
    expect(deltaDirection(null)).toBe('neutral')
  })

  it('formats money and percentages', () => {
    expect(fmtMoney(125000)).toBe('$125K')
    expect(fmtPct(88.25)).toBe('88.3%')
    expect(fmtPct(88.25, 0)).toBe('88%')
  })
})
