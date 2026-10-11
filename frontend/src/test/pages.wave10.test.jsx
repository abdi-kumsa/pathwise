/**
 * Wave 10 — student personalization and named visualizations.
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

vi.mock('../api/student', () => ({
  getFieldAlignment: vi.fn(),
  getSupplyDemandGap: vi.fn(),
  getStudentProfile: vi.fn(),
  getPathways: vi.fn(),
}))

vi.mock('../api/admin', () => ({
  getFeatureImportance: vi.fn(),
  getPriorityTiers: vi.fn(),
  getModelComparison: vi.fn(),
  getExpertValidations: vi.fn(),
  getAhpWeights: vi.fn(),
  postAhpWeights: vi.fn(),
  postExpertValidation: vi.fn(),
}))

import { getFieldAlignment, getSupplyDemandGap, getStudentProfile, getPathways } from '../api/student'
import {
  getFeatureImportance, getPriorityTiers, getModelComparison,
  getExpertValidations, getAhpWeights,
} from '../api/admin'
import FieldAlignmentPage from '../pages/student/FieldAlignmentPage'
import SupplyDemandGapPage from '../pages/student/SupplyDemandGapPage'
import ProfilePage from '../pages/student/ProfilePage'
import PathwayMapPage from '../pages/student/PathwayMapPage'
import AdminMethodologyPage from '../pages/admin/AdminMethodologyPage'

beforeEach(() => vi.clearAllMocks())

describe('W.STU.04 own-field highlight', () => {
  it('highlights the signed-in field and keeps national #1 as comparison', async () => {
    getFieldAlignment.mockResolvedValue({
      field: 'Health Sciences',
      method: 'Four-factor alignment.',
      weights: { labour_demand: 0.4 },
      rows: [
        {
          rank: 1, field: 'Engineering & Technology', score: 90, status: 'shortage',
          severity: 4, labour_demand: 1000, expected_graduates: 400, is_own_field: false,
          factors: [{ factor: 'labour_demand', weight: 0.4, contribution: 36 }],
        },
        {
          rank: 2, field: 'Health Sciences', score: 70, status: 'balanced',
          severity: 1, labour_demand: 500, expected_graduates: 480, is_own_field: true,
          factors: [{ factor: 'labour_demand', weight: 0.4, contribution: 28 }],
        },
      ],
    })
    render(<FieldAlignmentPage />)
    await waitFor(() => expect(screen.getByTestId('own-field')).toBeInTheDocument())
    expect(screen.getByTestId('own-field').textContent).toMatch(/Health Sciences/)
    expect(screen.getByTestId('own-field').textContent).toMatch(/your field/)
    expect(screen.getByText(/National #1/)).toBeInTheDocument()
    expect(screen.getAllByText(/Engineering & Technology/).length).toBeGreaterThan(0)
  })
})

describe('W.STU.05 own-field gap highlight', () => {
  it('marks the JWT field on the gap list', async () => {
    getSupplyDemandGap.mockResolvedValue({
      field: 'Health Sciences',
      rows: [
        { field: 'Engineering & Technology', signed_gap: 200, status: 'shortage', severity: 3, is_own_field: false },
        { field: 'Health Sciences', signed_gap: -40, status: 'balanced', severity: 1, is_own_field: true },
      ],
    })
    render(<SupplyDemandGapPage />)
    await waitFor(() => expect(screen.getByTestId('own-field')).toBeInTheDocument())
    expect(screen.getByTestId('own-field').textContent).toMatch(/Health Sciences/)
    expect(screen.getByTestId('own-field').textContent).toMatch(/your field/)
  })
})

describe('W.STU.01 department honesty', () => {
  it('shows an em dash when department is missing', async () => {
    getStudentProfile.mockResolvedValue({
      program: 'BSc Civil Engineering',
      department: null,
      institution: 'Addis Ababa University',
      enrollment_year: 2024,
      eligibility: { label: 'Eligibility', pct: 62, note: 'Pass-rate proxy.' },
    })
    render(<ProfilePage />)
    await waitFor(() => expect(screen.getByText('Department')).toBeInTheDocument())
    expect(screen.getByText('Not on the seeded SIS record')).toBeInTheDocument()
    expect(screen.getByText(/Department is shown as/)).toBeInTheDocument()
  })
})

describe('W.STU.08 pathway graph', () => {
  it('renders an SVG graph from programs, occupations and edges', async () => {
    getPathways.mockResolvedValue({
      note: 'Simulated join backbone.',
      programs: [{ program: 'BSc Civil Engineering', field: 'Engineering & Technology' }],
      occupations: [{ occupation: 'Civil engineer', field: 'Engineering & Technology' }],
      edges: [{ source: 'BSc Civil Engineering', target: 'Civil engineer', sector: 'Construction' }],
    })
    render(<PathwayMapPage />)
    await waitFor(() => expect(screen.getByTestId('pathway-graph')).toBeInTheDocument())
    expect(screen.getByLabelText(/pathway graph/i)).toBeInTheDocument()
    expect(screen.getByText('BSc Civil Engineering')).toBeInTheDocument()
    expect(screen.getByText('Civil engineer')).toBeInTheDocument()
  })
})

describe('W.ADM.04 unused DOC1 columns', () => {
  it('notes unused_by_learner and does not claim SHAP on Ethiopia OLS', async () => {
    getFeatureImportance.mockResolvedValue({
      panels: ['learned_importance', 'collection_priority'],
      never_merged: true,
      unused_by_learner: [{ model: 'M1', column: 'exam_score_mean', unused_by_learner: true }],
      learned_importance: {
        placement: { rows: [{ feature: 'internships', importance: 0.12 }] },
        model1: { rows: [{ feature: 'enrollment_lag_1y', importance: 0.4 }] },
        model2: { rows: [{ feature: 'employment_lag_1y', importance: 0.3 }] },
      },
      collection_priority: [{ id: 'M1.C1', name: 'Enrolment history', collection_priority: 12 }],
    })
    getPriorityTiers.mockResolvedValue({ model1: [], model2: [] })
    getModelComparison.mockResolvedValue({
      validation: 'grouped chronological holdout',
      targets: [
        { id: 'M2.employment_demand', target: 'employment_level', candidates: ['ols_lags'] },
        { id: 'M2.employment_growth', target: 'employment_growth_pct', candidates: ['ols_lags'] },
        { id: 'M2.vacancies', target: 'vacancy_count', candidates: ['ols_lags'] },
        { id: 'M2.occupational_demand', target: 'occupational_demand', candidates: ['ols_lags'] },
        { id: 'M2.skill_shortages', target: 'skill_shortage_index', candidates: ['ols_lags'] },
      ],
    })
    getExpertValidations.mockResolvedValue({ expert_domains: ['higher_education'], rows: [] })
    getAhpWeights.mockResolvedValue({ weights: null })

    render(<AdminMethodologyPage />)
    await waitFor(() => expect(screen.getByTestId('unused-features')).toBeInTheDocument())
    expect(screen.getByTestId('unused-features').textContent).toMatch(/unused_by_learner/)
    expect(screen.getByTestId('learned_importance').textContent).toMatch(/not an Ethiopia OLS/)
    expect(screen.getByText(/Leftover US placement SHAP/)).toBeInTheDocument()
  })
})
