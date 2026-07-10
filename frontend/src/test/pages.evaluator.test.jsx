/**
 * Page tests — StudentEvaluatorPage
 * The most complex page: form submission, SHAP waterfall, skill recommendations.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
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

import { submitStudentProfile, getSkillRecommendations } from '../api/enrollment'
import StudentEvaluatorPage from '../pages/StudentEvaluatorPage'

// ── fixtures ──────────────────────────────────────────────────────────────────
const PREDICTION = {
  placement_probability: 0.97,
  prediction:  'Placed',
  base_value:  2.0377,
  shap_values: [
    { feature: 'gpa_scaled',                 value: 3.8,   shap:  1.42 },
    { feature: 'internships',                value: 2,     shap:  0.88 },
    { feature: 'projects',                   value: 5,     shap:  0.55 },
    { feature: 'communication_score_scaled', value: 9,     shap:  0.31 },
    { feature: 'prog_MS Data Science',       value: 1,     shap:  0.22 },
    { feature: 'prog_MS AI',                 value: 0,     shap: -0.05 },
    { feature: 'prog_BS CS',                 value: 0,     shap: -0.08 },
    { feature: 'prog_MBA',                   value: 0,     shap: -0.11 },
  ],
}

const WEAK_PREDICTION = {
  placement_probability: 0.21,
  prediction:  'Not Placed',
  base_value:  2.0377,
  shap_values: [
    { feature: 'gpa_scaled',   value: 2.1, shap: -1.12 },
    { feature: 'internships',  value: 0,   shap: -0.75 },
    { feature: 'projects',     value: 1,   shap: -0.45 },
    { feature: 'communication_score_scaled', value: 3, shap: -0.33 },
  ],
}

const RECS = {
  student_id: null,
  recommendations: [
    { skill: 'Academic Performance (GPA)', priority: 'High',   reason: 'Strongest placement predictor' },
    { skill: 'Industry Experience',        priority: 'High',   reason: 'Internships strongly linked to placement' },
    { skill: 'Project Portfolio',          priority: 'Medium', reason: 'Portfolio differentiates candidates' },
    { skill: 'Communication Skills',       priority: 'Low',    reason: 'Baseline communication expected' },
  ],
  alternative_pathways: [
    'Consider a Graduate Certificate in Data Science',
    'Pursue cloud certifications (AWS/Azure)',
  ],
}

beforeEach(() => vi.clearAllMocks())

// ─── Initial state ─────────────────────────────────────────────────────────────

describe('StudentEvaluatorPage — initial state', () => {

  it('shows page title', () => {
    render(<StudentEvaluatorPage />)
    expect(screen.getByText('Student evaluator')).toBeInTheDocument()
  })

  it('shows placeholder prompt before prediction', () => {
    render(<StudentEvaluatorPage />)
    expect(screen.getByText(/Set profile and predict/i)).toBeInTheDocument()
  })

  it('shows the Predict Placement button', () => {
    render(<StudentEvaluatorPage />)
    expect(screen.getByRole('button', { name: /predict placement/i })).toBeInTheDocument()
  })

  it('shows GPA slider', () => {
    render(<StudentEvaluatorPage />)
    expect(screen.getByText('GPA')).toBeInTheDocument()
  })

  it('shows programme dropdown with default selection', () => {
    render(<StudentEvaluatorPage />)
    const select = screen.getByRole('combobox')
    expect(select.value).toBe('MS Data Science')
  })

  it('shows all 12 programme options in dropdown', () => {
    render(<StudentEvaluatorPage />)
    const options = screen.getAllByRole('option')
    expect(options.length).toBe(12)
  })
})

// ─── Successful prediction ─────────────────────────────────────────────────────

describe('StudentEvaluatorPage — successful prediction', () => {

  beforeEach(() => {
    submitStudentProfile.mockResolvedValue(PREDICTION)
    getSkillRecommendations.mockResolvedValue(RECS)
  })

  it('shows probability % after submission', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('97.0%')).toBeInTheDocument())
  })

  it('shows "Placed" prediction badge for high-probability profile', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('Placed')).toBeInTheDocument())
  })

  it('shows base_value in log-odds display', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText(/2\.038/)).toBeInTheDocument())
  })

  it('shows SHAP Feature Contributions heading', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('SHAP Feature Contributions')).toBeInTheDocument())
  })

  it('calls getSkillRecommendations after prediction succeeds', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(getSkillRecommendations).toHaveBeenCalledTimes(1))
  })

  it('renders Skill Recommendations section heading', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('Skill Recommendations')).toBeInTheDocument())
  })

  it('renders all 4 recommendation skill names', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => {
      expect(screen.getByText('Academic Performance (GPA)')).toBeInTheDocument()
      expect(screen.getByText('Industry Experience')).toBeInTheDocument()
      expect(screen.getByText('Project Portfolio')).toBeInTheDocument()
      expect(screen.getByText('Communication Skills')).toBeInTheDocument()
    })
  })

  it('renders recommendation priority badges', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => {
      expect(screen.getAllByText('High').length).toBe(2)
      expect(screen.getByText('Medium')).toBeInTheDocument()
      expect(screen.getByText('Low')).toBeInTheDocument()
    })
  })

  it('renders recommendation reasons', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('Strongest placement predictor')).toBeInTheDocument())
  })

  it('renders Alternative Pathways section', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('Alternative Pathways')).toBeInTheDocument())
  })

  it('renders both alternative pathway items', async () => {
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => {
      expect(screen.getByText('Consider a Graduate Certificate in Data Science')).toBeInTheDocument()
      expect(screen.getByText('Pursue cloud certifications (AWS/Azure)')).toBeInTheDocument()
    })
  })

  it('button shows "Predicting…" while request is in-flight', async () => {
    let resolve
    submitStudentProfile.mockImplementationOnce(() => new Promise(r => { resolve = r }))
    getSkillRecommendations.mockResolvedValue(RECS)
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('Predicting…')).toBeInTheDocument())
    resolve(PREDICTION)
    await waitFor(() => expect(screen.getByText('97.0%')).toBeInTheDocument())
  })
})

// ─── Weak / Not Placed prediction ─────────────────────────────────────────────

describe('StudentEvaluatorPage — Not Placed result', () => {

  it('shows "Not Placed" badge for weak profile', async () => {
    submitStudentProfile.mockResolvedValue(WEAK_PREDICTION)
    getSkillRecommendations.mockResolvedValue(RECS)
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('Not Placed')).toBeInTheDocument())
  })

  it('shows 21.0% probability for weak profile', async () => {
    submitStudentProfile.mockResolvedValue(WEAK_PREDICTION)
    getSkillRecommendations.mockResolvedValue(RECS)
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('21.0%')).toBeInTheDocument())
  })
})

// ─── Reset ────────────────────────────────────────────────────────────────────

describe('StudentEvaluatorPage — reset', () => {

  it('Reset button clears results and shows placeholder again', async () => {
    submitStudentProfile.mockResolvedValue(PREDICTION)
    getSkillRecommendations.mockResolvedValue(RECS)
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => screen.getByText('97.0%'))

    fireEvent.click(screen.getByRole('button', { name: /reset/i }))
    await waitFor(() => expect(screen.getByText(/Set profile and predict/i)).toBeInTheDocument())
    expect(screen.queryByText('97.0%')).not.toBeInTheDocument()
    expect(screen.queryByText('Skill Recommendations')).not.toBeInTheDocument()
  })
})

// ─── Error handling ────────────────────────────────────────────────────────────

describe('StudentEvaluatorPage — error handling', () => {

  it('shows error message when prediction API fails', async () => {
    submitStudentProfile.mockRejectedValue({ response: { data: { detail: 'Model not loaded' } } })
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('Model not loaded')).toBeInTheDocument())
  })

  it('button returns to "Predict Placement" after failure', async () => {
    submitStudentProfile.mockRejectedValue(new Error('timeout'))
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByRole('button', { name: /predict placement/i })).toBeInTheDocument())
  })

  it('can re-submit after an error', async () => {
    submitStudentProfile
      .mockRejectedValueOnce(new Error('timeout'))
      .mockResolvedValueOnce(PREDICTION)
    getSkillRecommendations.mockResolvedValue(RECS)
    render(<StudentEvaluatorPage />)

    // first attempt fails
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => screen.getByText('timeout'))

    // second attempt succeeds
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    await waitFor(() => expect(screen.getByText('97.0%')).toBeInTheDocument())
  })

  it('still shows prediction even if skill recommendations fetch fails', async () => {
    submitStudentProfile.mockResolvedValue(PREDICTION)
    getSkillRecommendations.mockRejectedValue(new Error('recs unavailable'))
    render(<StudentEvaluatorPage />)
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))
    // probability should still render
    await waitFor(() => expect(screen.getByText('97.0%')).toBeInTheDocument())
    // but recs section should not appear
    expect(screen.queryByText('Skill Recommendations')).not.toBeInTheDocument()
  })
})

// ─── Form interactions ─────────────────────────────────────────────────────────

describe('StudentEvaluatorPage — form interactions', () => {

  it('GPA slider updates the displayed value', async () => {
    render(<StudentEvaluatorPage />)
    const sliders = screen.getAllByRole('slider')
    const gpaSlider = sliders[0]
    fireEvent.change(gpaSlider, { target: { value: '3.8' } })
    await waitFor(() => expect(screen.getByText('3.8')).toBeInTheDocument())
  })

  it('changing programme dropdown updates selected value', async () => {
    render(<StudentEvaluatorPage />)
    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, 'MS Cybersecurity')
    expect(select.value).toBe('MS Cybersecurity')
  })

  it('submitStudentProfile is called with current form values', async () => {
    submitStudentProfile.mockResolvedValue(PREDICTION)
    getSkillRecommendations.mockResolvedValue(RECS)
    render(<StudentEvaluatorPage />)

    // Change GPA to 3.9
    const sliders = screen.getAllByRole('slider')
    fireEvent.change(sliders[0], { target: { value: '3.9' } })
    fireEvent.click(screen.getByRole('button', { name: /predict placement/i }))

    await waitFor(() => expect(submitStudentProfile).toHaveBeenCalledWith(
      expect.objectContaining({ gpa: 3.9 })
    ))
  })
})
