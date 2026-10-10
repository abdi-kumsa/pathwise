/**
 * Wave 5 ranking pages — alternatives must not rank on fit classification,
 * and programme health must use the three spec buckets.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

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

vi.mock('../api/student', () => ({
  getStudentProfile: vi.fn(),
  getAlternatives: vi.fn(),
  getSkillGaps: vi.fn(),
  getLabourOutlook: vi.fn(),
}))

vi.mock('../api/roles', () => ({
  getPortfolio: vi.fn(),
  getProgramHealth: vi.fn(),
}))

import { getStudentProfile, getAlternatives, getLabourOutlook } from '../api/student'
import { getPortfolio, getProgramHealth } from '../api/roles'
import EscapeRoutePage from '../pages/EscapeRoutePage'
import ProgramPortfolioPage from '../pages/university/ProgramPortfolioPage'
import LabourOutlookPage from '../pages/student/LabourOutlookPage'

beforeEach(() => vi.clearAllMocks())

describe('W.STU.06 alternatives ranking', () => {
  it('shows labour_demand, expected_supply, eligibility and skills_fit — never fit classification', async () => {
    getStudentProfile.mockResolvedValue({ field: 'Engineering & Technology' })
    getAlternatives.mockResolvedValue({
      method: 'Four-factor rank. Fit classification is not used.',
      fit_classification_used: false,
      ranking_factors: ['labour_demand', 'expected_supply', 'eligibility', 'skills_fit'],
      rows: [
        {
          rank: 1,
          field: 'Health Sciences',
          score: 81,
          status: 'shortage',
          severity: 3,
          factors: [
            { factor: 'labour_demand', weight: 0.35, contribution: 28 },
            { factor: 'expected_supply', weight: 0.25, contribution: 20 },
            { factor: 'eligibility', weight: 0.2, contribution: 16 },
            { factor: 'skills_fit', weight: 0.2, contribution: 17 },
          ],
        },
      ],
    })

    render(<EscapeRoutePage />)

    await waitFor(() => expect(screen.getByTestId('alternative-row')).toBeInTheDocument())
    const factors = screen.getAllByTestId('factor').map(el => el.textContent)
    expect(factors.join(' ')).toMatch(/labour_demand/)
    expect(factors.join(' ')).toMatch(/expected_supply/)
    expect(factors.join(' ')).toMatch(/eligibility/)
    expect(factors.join(' ')).toMatch(/skills_fit/)
    expect(factors.join(' ').toLowerCase()).not.toMatch(/fit_class|placement_status|overeducated|undereducated/)
    expect(screen.getByText(/Fit classification is not used/)).toBeInTheDocument()
  })
})

describe('W.UNI.05 programme health buckets', () => {
  it('labels shortage, balanced and oversupply in colour-plus-word rows', async () => {
    getPortfolio.mockResolvedValue({
      institution: 'Addis Ababa University',
      programs: [],
    })
    getProgramHealth.mockResolvedValue({
      method: 'Status is the sign of labour demand minus expected graduates.',
      fit_classification_used: false,
      severity_buckets: ['shortage', 'balanced', 'oversupply'],
      rows: [
        { program: 'BSc Civil Engineering', field: 'Engineering & Technology', status: 'shortage', action: 'expand', severity: 4 },
        { program: 'BA Economics', field: 'Social Sciences', status: 'balanced', action: 'maintain', severity: 1 },
        { program: 'BA Management', field: 'Business & Economics', status: 'oversupply', action: 'review', severity: 3 },
      ],
    })

    render(<ProgramPortfolioPage />)

    await waitFor(() => expect(screen.getByTestId('program-health')).toBeInTheDocument())
    const labels = screen.getAllByTestId('health-status').map(el => el.textContent)
    expect(labels).toEqual(['shortage', 'balanced', 'oversupply'])
    expect(screen.getByText(/expand/)).toBeInTheDocument()
    expect(screen.getByText(/maintain/)).toBeInTheDocument()
    expect(screen.getByText(/review/)).toBeInTheDocument()
  })
})

describe('student labour outlook cell size', () => {
  it('shows the withheld caveat when cell_withheld is true', async () => {
    getLabourOutlook.mockResolvedValue({
      field: 'Engineering & Technology',
      series: { 3: [], 5: [] },
      occupations: [],
      cell_withheld: true,
      min_cell_size: 5,
      note: 'Projected occupational vacancies. Simulated Ethiopian structure.',
    })
    render(<LabourOutlookPage />)
    await waitFor(() => expect(screen.getByText(/Occupations withheld/)).toBeInTheDocument())
    expect(screen.getByText(/are withheld/)).toBeInTheDocument()
  })
})
