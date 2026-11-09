/**
 * Page tests — Student Enrollment Intelligence Dashboard
 * Covers: EnrollmentForecastPage (leftover US LSTM page, routed only with
 *         VITE_LEGACY_US_MODELS=true)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

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

vi.mock('../api/enrollment', () => ({
  getEnrollmentSummary:    vi.fn(),
  getEnrollmentForecast:   vi.fn(),
  getAdmissionRisk:        vi.fn(),
  getPlacementByStream:    vi.fn(),
  submitStudentProfile:    vi.fn(),
  getSkillRecommendations: vi.fn(),
}))

import {
  getEnrollmentSummary,
  getEnrollmentForecast,
} from '../api/enrollment'

import EnrollmentForecastPage from '../pages/EnrollmentForecastPage'

// ── fixtures ──────────────────────────────────────────────────────────────────
const SUMMARY = {
  total_students: 3000,
  total_programs: 12,
  top_program:    'MS Data Science',
  avg_placement_rate: 88.3,
  enrollment_by_year: { '2019': 469, '2020': 529, '2021': 518, '2022': 503, '2023': 473, '2024': 508 },
}

const FORECAST = {
  program: 'MS Data Science',
  historical: [
    { year: 2019, predicted_count: 40 }, { year: 2020, predicted_count: 44 },
    { year: 2021, predicted_count: 43 }, { year: 2022, predicted_count: 42 },
    { year: 2023, predicted_count: 39 }, { year: 2024, predicted_count: 41 },
  ],
  forecast: [
    { year: 2025, predicted_count: 43 },
    { year: 2026, predicted_count: 46 },
    { year: 2027, predicted_count: 49 },
  ],
}

beforeEach(() => vi.clearAllMocks())

// ─── EnrollmentForecastPage ───────────────────────────────────────────────────

describe('EnrollmentForecastPage', () => {

  it('shows page title', () => {
    getEnrollmentSummary.mockResolvedValue(SUMMARY)
    getEnrollmentForecast.mockResolvedValue(FORECAST)
    render(<EnrollmentForecastPage />)
    expect(screen.getByText('Enrollment forecast')).toBeInTheDocument()
  })

  it('shows loading dashes while summary is loading', () => {
    getEnrollmentSummary.mockReturnValue(new Promise(() => {}))
    getEnrollmentForecast.mockReturnValue(new Promise(() => {}))
    render(<EnrollmentForecastPage />)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('renders total_students KPI after summary loads', async () => {
    getEnrollmentSummary.mockResolvedValue(SUMMARY)
    getEnrollmentForecast.mockResolvedValue(FORECAST)
    render(<EnrollmentForecastPage />)
    await waitFor(() => expect(screen.getByText('3,000')).toBeInTheDocument())
  })

  it('renders top_program KPI', async () => {
    getEnrollmentSummary.mockResolvedValue(SUMMARY)
    getEnrollmentForecast.mockResolvedValue(FORECAST)
    render(<EnrollmentForecastPage />)
    await waitFor(() => expect(screen.getByText('MS Data Science')).toBeInTheDocument())
  })

  it('shows avg_placement_rate KPI', async () => {
    getEnrollmentSummary.mockResolvedValue(SUMMARY)
    getEnrollmentForecast.mockResolvedValue(FORECAST)
    render(<EnrollmentForecastPage />)
    await waitFor(() => expect(screen.getByText('88.3%')).toBeInTheDocument())
  })

  it('shows an ErrorBanner if summary fetch fails', async () => {
    getEnrollmentSummary.mockRejectedValue(new Error('summary failed'))
    getEnrollmentForecast.mockResolvedValue(FORECAST)
    render(<EnrollmentForecastPage />)
    await waitFor(() => expect(screen.getByText('summary failed')).toBeInTheDocument())
  })

  it('shows a separate ErrorBanner if forecast fetch fails', async () => {
    getEnrollmentSummary.mockResolvedValue(SUMMARY)
    getEnrollmentForecast.mockRejectedValue(new Error('forecast failed'))
    render(<EnrollmentForecastPage />)
    await waitFor(() => expect(screen.getByText('forecast failed')).toBeInTheDocument())
  })

  it('re-fetches forecast when program dropdown changes', async () => {
    getEnrollmentSummary.mockResolvedValue(SUMMARY)
    getEnrollmentForecast.mockResolvedValue(FORECAST)
    render(<EnrollmentForecastPage />)
    await waitFor(() => expect(getEnrollmentForecast).toHaveBeenCalledTimes(1))

    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, 'MS Artificial Intelligence')
    await waitFor(() => expect(getEnrollmentForecast).toHaveBeenCalledTimes(2))
    expect(getEnrollmentForecast).toHaveBeenLastCalledWith('MS Artificial Intelligence', 3)
  })

  it('summary fetch fires only once regardless of program change', async () => {
    getEnrollmentSummary.mockResolvedValue(SUMMARY)
    getEnrollmentForecast.mockResolvedValue(FORECAST)
    render(<EnrollmentForecastPage />)
    await waitFor(() => expect(getEnrollmentSummary).toHaveBeenCalledTimes(1))

    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, 'MS Cloud Computing')
    await waitFor(() => expect(getEnrollmentForecast).toHaveBeenCalledTimes(2))
    // summary must NOT be called again
    expect(getEnrollmentSummary).toHaveBeenCalledTimes(1)
  })
})

// ─── AdmissionRiskPage ────────────────────────────────────────────────────────
