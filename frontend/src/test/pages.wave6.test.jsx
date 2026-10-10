/**
 * Wave 6 ranking and empty-state pages.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

vi.mock('recharts', () => {
  const Pass = ({ children }) => <>{children}</>
  const Null = () => null
  return {
    ResponsiveContainer: Pass,
    BarChart: Pass, LineChart: Pass, AreaChart: Pass, ScatterChart: Pass,
    Scatter: Null, ZAxis: Null,
    Bar: Null, Line: Null, Area: Null,
    XAxis: Null, YAxis: Null, CartesianGrid: Null,
    Tooltip: Null, Legend: Null, Cell: Null, ReferenceLine: Null,
  }
})

vi.mock('../api/roles', () => ({
  getPolicyPriority: vi.fn(),
  getSkillsShortage: vi.fn(),
  getMigration: vi.fn(),
}))

import { getPolicyPriority, getSkillsShortage, getMigration } from '../api/roles'
import InvestmentPriorityPage from '../pages/moe/InvestmentPriorityPage'
import SkillsMismatchPage from '../pages/mol/SkillsMismatchPage'
import MigrationPage from '../pages/mol/MigrationPage'

beforeEach(() => vi.clearAllMocks())

describe('W.MOE.05 policy priority factors', () => {
  it('shows labour_shortage, national_priority, student_demand and feasibility — never ROI or fit', async () => {
    getPolicyPriority.mockResolvedValue({
      method: 'Each factor is min-max normalised across fields.',
      fit_classification_used: false,
      ranking_factors: ['labour_shortage', 'national_priority', 'student_demand', 'feasibility'],
      weights: {
        labour_shortage: 0.35,
        national_priority: 0.25,
        student_demand: 0.20,
        feasibility: 0.20,
      },
      rows: [
        {
          rank: 1,
          field: 'Engineering & Technology',
          score: 82,
          status: 'shortage',
          signed_gap: 1200,
          unconstrained_demand: 4000,
          feasibility: 0.7,
          factors: [
            { factor: 'labour_shortage', weight: 0.35, contribution: 28 },
            { factor: 'national_priority', weight: 0.25, contribution: 20 },
            { factor: 'student_demand', weight: 0.20, contribution: 16 },
            { factor: 'feasibility', weight: 0.20, contribution: 18 },
          ],
        },
      ],
    })

    render(<InvestmentPriorityPage />)
    await waitFor(() => expect(screen.getByTestId('priority-row')).toBeInTheDocument())
    expect(screen.getByTestId('priority-matrix')).toBeInTheDocument()
    const factors = screen.getAllByTestId('factor').map(el => el.textContent)
    expect(factors.join(' ')).toMatch(/labour_shortage/)
    expect(factors.join(' ')).toMatch(/national_priority/)
    expect(factors.join(' ')).toMatch(/student_demand/)
    expect(factors.join(' ')).toMatch(/feasibility/)
    expect(factors.join(' ').toLowerCase()).not.toMatch(/roi|fit_class|overeducated|undereducated/)
    expect(screen.getByText(/Fit classification is not used/)).toBeInTheDocument()
  })
})

describe('W.MOL.04 skills heatmap', () => {
  it('labels technical, digital and soft skill classes', async () => {
    getSkillsShortage.mockResolvedValue({
      n: 1,
      rows: [{
        field: 'Engineering & Technology',
        period: 2026,
        technical_skill_demand: 0.8,
        digital_skill_demand: 0.6,
        soft_skill_demand: 0.4,
        emerging_skill_demand: 0.3,
        skill_shortages: 0.7,
      }],
    })

    render(<SkillsMismatchPage />)
    await waitFor(() => expect(screen.getByTestId('skills-heatmap')).toBeInTheDocument())
    const classes = screen.getAllByTestId('skill-class').map(el => el.textContent)
    expect(classes).toEqual(expect.arrayContaining(['technical', 'digital', 'soft']))
  })
})

describe('W.MOL.08 migration empty state', () => {
  it('renders EmptyState when available is false', async () => {
    getMigration.mockResolvedValue({
      available: false,
      reason: 'No migration series in the current Ethiopia tables.',
      rows: [],
      note: 'Degrades rather than inventing coverage.',
    })
    render(<MigrationPage />)
    await waitFor(() => expect(screen.getByText('Migration series unavailable')).toBeInTheDocument())
  })
})
