/**
 * Page tests — Market Demand Dashboard
 * Covers: MarketOverviewPage (leftover US Prophet page, routed only with
 *         VITE_LEGACY_US_MODELS=true)
 *
 * Strategy:
 *  - API modules are mocked so no HTTP calls happen
 *  - recharts is mocked to avoid ResizeObserver / SVG issues in jsdom
 *  - Each page is tested for: loading state, error state, success state
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'

// ── recharts mock (avoids ResizeObserver + SVG rendering issues) ──────────────
vi.mock('recharts', () => {
  const Pass = ({ children }) => <>{children}</>
  const Null = () => null
  return {
    ResponsiveContainer: Pass,
    BarChart: Pass, LineChart: Pass, AreaChart: Pass,
    Bar: Null, Line: Null, Area: Null,
    XAxis: Null, YAxis: Null, CartesianGrid: Null,
    Tooltip: Null, Legend: Null, Cell: Null, ReferenceLine: Null,
  }
})

// ── API mocks ─────────────────────────────────────────────────────────────────
vi.mock('../api/marketDemand', () => ({
  getMarketOverview:       vi.fn(),
  getTopHiringCompanies:  vi.fn(),
  getRegionalHiringData:  vi.fn(),
  getSkillGapData:        vi.fn(),
  getJobInternshipRatio:  vi.fn(),
  getHiringSourceBreakdown: vi.fn(),
  getDemandForecast:      vi.fn(),
}))

import {
  getMarketOverview,
  getTopHiringCompanies,
} from '../api/marketDemand'

import MarketOverviewPage   from '../pages/MarketOverviewPage'

// ── fixtures ──────────────────────────────────────────────────────────────────
const OVERVIEW = { total_companies: 30, total_placements: 2649, avg_salary: 118526, avg_time_to_hire: 54, top_role: 'Full Stack Developer' }
const COMPANIES = [{ company: 'Google', count: 104 }, { company: 'Meta', count: 87 }]

beforeEach(() => vi.clearAllMocks())

// ─── MarketOverviewPage ───────────────────────────────────────────────────────

describe('MarketOverviewPage', () => {

  it('shows page title', async () => {
    getMarketOverview.mockResolvedValue(OVERVIEW)
    getTopHiringCompanies.mockResolvedValue(COMPANIES)
    render(<MarketOverviewPage />)
    expect(screen.getByText('Market demand overview')).toBeInTheDocument()
  })

  it('shows loading dashes while fetching', () => {
    getMarketOverview.mockReturnValue(new Promise(() => {}))
    getTopHiringCompanies.mockReturnValue(new Promise(() => {}))
    render(<MarketOverviewPage />)
    const dashes = screen.getAllByText('—')
    expect(dashes.length).toBeGreaterThan(0)
  })

  it('renders KPI values after data loads', async () => {
    getMarketOverview.mockResolvedValue(OVERVIEW)
    getTopHiringCompanies.mockResolvedValue(COMPANIES)
    render(<MarketOverviewPage />)
    await waitFor(() => expect(screen.getByText('30')).toBeInTheDocument())
    expect(screen.getByText('2,649')).toBeInTheDocument()
  })

  it('shows ErrorBanner when fetch fails', async () => {
    getMarketOverview.mockRejectedValue(new Error('Server error'))
    getTopHiringCompanies.mockRejectedValue(new Error('Server error'))
    render(<MarketOverviewPage />)
    await waitFor(() => expect(screen.getByText('Server error')).toBeInTheDocument())
  })

  it('shows Retry button inside ErrorBanner', async () => {
    getMarketOverview.mockRejectedValue(new Error('fail'))
    getTopHiringCompanies.mockRejectedValue(new Error('fail'))
    render(<MarketOverviewPage />)
    await waitFor(() => expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument())
  })

  it('refetches when Retry is clicked', async () => {
    getMarketOverview
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce(OVERVIEW)
    getTopHiringCompanies
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce(COMPANIES)
    render(<MarketOverviewPage />)
    await waitFor(() => screen.getByRole('button', { name: /retry/i }))
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    await waitFor(() => expect(screen.getByText('30')).toBeInTheDocument())
  })
})

// ─── HiringAnalyticsPage ─────────────────────────────────────────────────────
