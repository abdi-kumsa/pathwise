/**
 * Page tests — Market Demand Dashboard
 * Covers: MarketOverviewPage, HiringAnalyticsPage, SkillGapPage, ForecastPage
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
  getRegionalHiringData,
  getSkillGapData,
  getJobInternshipRatio,
  getHiringSourceBreakdown,
  getDemandForecast,
} from '../api/marketDemand'

import MarketOverviewPage   from '../pages/MarketOverviewPage'
import HiringAnalyticsPage  from '../pages/HiringAnalyticsPage'
import SkillGapPage         from '../pages/SkillGapPage'
import ForecastPage         from '../pages/ForecastPage'

// ── fixtures ──────────────────────────────────────────────────────────────────
const OVERVIEW = { total_companies: 30, total_placements: 2649, avg_salary: 118526, avg_time_to_hire: 54, top_role: 'Full Stack Developer' }
const COMPANIES = [{ company: 'Google', count: 104 }, { company: 'Meta', count: 87 }]
const RATIO  = { job_count: 2649, internship_count: 6007, ratio: 0.44 }
const SOURCES = [{ source: 'LinkedIn', count: 900 }, { source: 'Company Site', count: 700 }]
const REGIONS = [{ location: 'San Francisco', count: 500 }]
const SKILL_GAP = {
  skills: [
    { skill: 'Python', demand_score: 95, curriculum_coverage: 70, gap_score: 25 },
    { skill: 'SQL',    demand_score: 88, curriculum_coverage: 75, gap_score: 13 },
  ],
  top_gap_skill: 'Python', avg_gap_score: 19,
}
const FORECAST_DATA = Array.from({ length: 12 }, (_, i) => ({
  month: `2025-${String(i + 1).padStart(2, '0')}-01`,
  predicted_postings: 100 + i * 5,
  lower_bound: 90 + i * 5,
  upper_bound: 110 + i * 5,
}))

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

describe('HiringAnalyticsPage', () => {

  const setupSuccess = () => {
    getMarketOverview.mockResolvedValue(OVERVIEW)
    getTopHiringCompanies.mockResolvedValue(COMPANIES)
    getJobInternshipRatio.mockResolvedValue(RATIO)
    getHiringSourceBreakdown.mockResolvedValue(SOURCES)
  }
  const setupFail = () => {
    getMarketOverview.mockRejectedValue(new Error('fetch failed'))
    getTopHiringCompanies.mockRejectedValue(new Error('fetch failed'))
    getJobInternshipRatio.mockRejectedValue(new Error('fetch failed'))
    getHiringSourceBreakdown.mockRejectedValue(new Error('fetch failed'))
  }

  it('shows loading dashes initially', () => {
    setupSuccess()
    render(<HiringAnalyticsPage />)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('renders avg_time_to_hire value after data loads', async () => {
    setupSuccess()
    render(<HiringAnalyticsPage />)
    await waitFor(() => expect(screen.getByText('54 days')).toBeInTheDocument())
  })

  it('renders top company name after data loads', async () => {
    setupSuccess()
    render(<HiringAnalyticsPage />)
    await waitFor(() => expect(screen.getByText('Google')).toBeInTheDocument())
  })

  it('shows ErrorBanner on failure', async () => {
    setupFail()
    render(<HiringAnalyticsPage />)
    await waitFor(() => expect(screen.getByText('fetch failed')).toBeInTheDocument())
  })
})

// ─── SkillGapPage ─────────────────────────────────────────────────────────────

describe('SkillGapPage', () => {

  it('shows page title', async () => {
    getSkillGapData.mockResolvedValue(SKILL_GAP)
    render(<SkillGapPage />)
    expect(screen.getByText('Skill gap analysis')).toBeInTheDocument()
  })

  it('shows loading dashes while fetching', () => {
    getSkillGapData.mockReturnValue(new Promise(() => {}))
    render(<SkillGapPage />)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('renders top_gap_skill after data loads', async () => {
    getSkillGapData.mockResolvedValue(SKILL_GAP)
    render(<SkillGapPage />)
    // "Python" appears in both the KPI card and chart data labels
    await waitFor(() => expect(screen.getAllByText('Python').length).toBeGreaterThan(0))
  })

  it('renders avg_gap_score KPI', async () => {
    getSkillGapData.mockResolvedValue(SKILL_GAP)
    render(<SkillGapPage />)
    await waitFor(() => expect(screen.getByText('19.0')).toBeInTheDocument())
  })

  it('shows ErrorBanner on failure', async () => {
    getSkillGapData.mockRejectedValue(new Error('skill data unavailable'))
    render(<SkillGapPage />)
    await waitFor(() => expect(screen.getByText('skill data unavailable')).toBeInTheDocument())
  })

  it('shows Retry button and it calls the API again', async () => {
    getSkillGapData
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce(SKILL_GAP)
    render(<SkillGapPage />)
    await waitFor(() => screen.getByRole('button', { name: /retry/i }))
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    // "Python" appears in KPI card and chart labels after successful fetch
    await waitFor(() => expect(screen.getAllByText('Python').length).toBeGreaterThan(0))
  })
})

// ─── ForecastPage ─────────────────────────────────────────────────────────────

describe('ForecastPage', () => {

  it('shows page title', () => {
    getDemandForecast.mockResolvedValue(FORECAST_DATA)
    render(<ForecastPage />)
    expect(screen.getByText('Demand forecast')).toBeInTheDocument()
  })

  it('shows loading dashes while fetching', () => {
    getDemandForecast.mockReturnValue(new Promise(() => {}))
    render(<ForecastPage />)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('renders 12-month total KPI after data loads', async () => {
    getDemandForecast.mockResolvedValue(FORECAST_DATA)
    render(<ForecastPage />)
    // total = sum of predicted_postings = 100+105+...+155 = 12*100 + 5*(0+1+...+11) = 1200+330 = 1530
    const total = FORECAST_DATA.reduce((s, d) => s + d.predicted_postings, 0)
    await waitFor(() => expect(screen.getByText(total.toLocaleString())).toBeInTheDocument())
  })

  it('shows ErrorBanner on failure', async () => {
    getDemandForecast.mockRejectedValue(new Error('forecast unavailable'))
    render(<ForecastPage />)
    await waitFor(() => expect(screen.getByText('forecast unavailable')).toBeInTheDocument())
  })

  it('shows Retry button on error', async () => {
    getDemandForecast.mockRejectedValue(new Error('fail'))
    render(<ForecastPage />)
    await waitFor(() => expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument())
  })
})
