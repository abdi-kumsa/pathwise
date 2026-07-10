/**
 * Page tests — Student Enrollment Intelligence Dashboard
 * Covers: EnrollmentForecastPage, AdmissionRiskPage, PlacementByStreamPage
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react'
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
  getAdmissionRisk,
  getPlacementByStream,
} from '../api/enrollment'

import EnrollmentForecastPage from '../pages/EnrollmentForecastPage'
import AdmissionRiskPage      from '../pages/AdmissionRiskPage'
import PlacementByStreamPage  from '../pages/PlacementByStreamPage'

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

const RISKS = [
  { program: 'MS Cybersecurity', risk_score: 24.5, trend: 'down', recommended_intake: 35 },
  { program: 'MS HCI',           risk_score: 12.1, trend: 'down', recommended_intake: 28 },
  { program: 'MS Cloud',         risk_score:  4.3, trend: 'stable', recommended_intake: 40 },
]

const STREAMS = [
  { program: 'MS Data Science', placement_rate: 94.5, avg_salary: 125000, student_count: 250 },
  { program: 'MS AI',           placement_rate: 92.1, avg_salary: 132000, student_count: 200 },
  { program: 'BS CS',           placement_rate: 85.0, avg_salary: 98000,  student_count: 150 },
]

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

describe('AdmissionRiskPage', () => {

  it('shows page title', () => {
    getAdmissionRisk.mockResolvedValue(RISKS)
    render(<AdmissionRiskPage />)
    expect(screen.getByText('Admission risk')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    getAdmissionRisk.mockReturnValue(new Promise(() => {}))
    render(<AdmissionRiskPage />)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('renders risk table rows after data loads', async () => {
    getAdmissionRisk.mockResolvedValue(RISKS)
    render(<AdmissionRiskPage />)
    // "MS Cybersecurity" appears in KPI card (highest risk) AND in the table row
    await waitFor(() => expect(screen.getAllByText('MS Cybersecurity').length).toBeGreaterThan(0))
    expect(screen.getAllByText('MS HCI').length).toBeGreaterThan(0)
  })

  it('renders risk_score values', async () => {
    getAdmissionRisk.mockResolvedValue(RISKS)
    render(<AdmissionRiskPage />)
    await waitFor(() => expect(screen.getByText('24.5')).toBeInTheDocument())
    expect(screen.getByText('12.1')).toBeInTheDocument()
  })

  it('renders trend badges', async () => {
    getAdmissionRisk.mockResolvedValue(RISKS)
    render(<AdmissionRiskPage />)
    await waitFor(() => expect(screen.getAllByText('Declining').length).toBe(2))
    expect(screen.getByText('Stable')).toBeInTheDocument()
  })

  it('shows declining count in KPI', async () => {
    getAdmissionRisk.mockResolvedValue(RISKS)
    render(<AdmissionRiskPage />)
    // 2 declining programmes in fixture
    await waitFor(() => expect(screen.getByText('2')).toBeInTheDocument())
  })

  it('shows ErrorBanner on failure', async () => {
    getAdmissionRisk.mockRejectedValue(new Error('risk data error'))
    render(<AdmissionRiskPage />)
    await waitFor(() => expect(screen.getByText('risk data error')).toBeInTheDocument())
  })

  it('initial API call uses default limit of 12', async () => {
    getAdmissionRisk.mockResolvedValue(RISKS)
    render(<AdmissionRiskPage />)
    await waitFor(() => expect(getAdmissionRisk).toHaveBeenCalledWith(12))
  })

  it('debounces slider — only fires one API call 500ms after slider change', async () => {
    vi.useFakeTimers()
    getAdmissionRisk.mockResolvedValue(RISKS)
    render(<AdmissionRiskPage />)

    // Wait for the initial call to settle
    await act(async () => { vi.advanceTimersByTime(600) })
    const initialCalls = getAdmissionRisk.mock.calls.length

    // Move slider — should NOT trigger immediately
    const slider = screen.getByRole('slider')
    fireEvent.change(slider, { target: { value: '5' } })

    // 400ms later — still no new call
    await act(async () => { vi.advanceTimersByTime(400) })
    expect(getAdmissionRisk.mock.calls.length).toBe(initialCalls)

    // 500ms total — now it fires
    await act(async () => { vi.advanceTimersByTime(100) })
    expect(getAdmissionRisk.mock.calls.length).toBe(initialCalls + 1)
    expect(getAdmissionRisk).toHaveBeenLastCalledWith(5)

    vi.useRealTimers()
  })
})

// ─── PlacementByStreamPage ────────────────────────────────────────────────────

describe('PlacementByStreamPage', () => {

  it('shows page title', () => {
    getPlacementByStream.mockResolvedValue(STREAMS)
    render(<PlacementByStreamPage />)
    expect(screen.getByText('Placement by stream')).toBeInTheDocument()
  })

  it('shows loading dashes initially', () => {
    getPlacementByStream.mockReturnValue(new Promise(() => {}))
    render(<PlacementByStreamPage />)
    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('renders top programme name after data loads', async () => {
    getPlacementByStream.mockResolvedValue(STREAMS)
    render(<PlacementByStreamPage />)
    await waitFor(() => expect(screen.getAllByText('MS Data Science').length).toBeGreaterThan(0))
  })

  it('renders overall placement rate KPI', async () => {
    getPlacementByStream.mockResolvedValue(STREAMS)
    render(<PlacementByStreamPage />)
    const avg = ((94.5 + 92.1 + 85.0) / 3).toFixed(1)
    await waitFor(() => expect(screen.getByText(avg + '%')).toBeInTheDocument())
  })

  it('renders avg salary KPI', async () => {
    getPlacementByStream.mockResolvedValue(STREAMS)
    render(<PlacementByStreamPage />)
    const avgSalary = '$' + Math.round((125000 + 132000 + 98000) / 3 / 1000) + 'K'
    await waitFor(() => expect(screen.getByText(avgSalary)).toBeInTheDocument())
  })

  it('shows ErrorBanner when fetch fails', async () => {
    getPlacementByStream.mockRejectedValue(new Error('stream error'))
    render(<PlacementByStreamPage />)
    await waitFor(() => expect(screen.getByText('stream error')).toBeInTheDocument())
  })

  it('shows Retry button and re-fetches on click', async () => {
    getPlacementByStream
      .mockRejectedValueOnce(new Error('fail'))
      .mockResolvedValueOnce(STREAMS)
    render(<PlacementByStreamPage />)
    await waitFor(() => screen.getByRole('button', { name: /retry/i }))
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    await waitFor(() => expect(screen.getAllByText('MS Data Science').length).toBeGreaterThan(0))
  })
})
