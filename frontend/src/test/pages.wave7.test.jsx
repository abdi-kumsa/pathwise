/**
 * Wave 7 admin widgets — two-panel importance, audit search, AHP refusal.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../api/admin', () => ({
  getFeatureImportance: vi.fn(),
  getPriorityTiers: vi.fn(),
  getModelComparison: vi.fn(),
  getExpertValidations: vi.fn(),
  getAhpWeights: vi.fn(),
  postAhpWeights: vi.fn(),
  postExpertValidation: vi.fn(),
  getAuditLog: vi.fn(),
  getPipelineStatus: vi.fn(),
}))

import {
  getFeatureImportance,
  getPriorityTiers,
  getModelComparison,
  getExpertValidations,
  getAhpWeights,
  postAhpWeights,
  getAuditLog,
  getPipelineStatus,
} from '../api/admin'
import AdminMethodologyPage from '../pages/admin/AdminMethodologyPage'
import AdminAuditLogPage from '../pages/admin/AdminAuditLogPage'
import AdminPipelinePage from '../pages/admin/AdminPipelinePage'

beforeEach(() => vi.clearAllMocks())

const importance = {
  panels: ['learned_importance', 'collection_priority'],
  never_merged: true,
  learned_importance: {
    placement: {
      method: 'shap',
      rows: [{ feature: 'internships', importance: 0.12, method: 'shap' }],
    },
    model1: { rows: [{ feature: 'enrollment_lag_1y', importance: 0.4 }] },
    model2: { rows: [] },
  },
  collection_priority: [
    { id: 'M1.C1', name: 'Enrolment history', collection_priority: 12 },
  ],
}

describe('W.ADM.04 two labelled panels', () => {
  it('renders learned_importance beside collection_priority and never a blended score', async () => {
    getFeatureImportance.mockResolvedValue(importance)
    getPriorityTiers.mockResolvedValue({
      model1: [{ id: 'T1', combined_priority: 70, groups: ['M1.C1'] }],
      model2: [{ id: 'T1', combined_priority: 55, groups: ['M2.C1'] }],
    })
    getModelComparison.mockResolvedValue({
      validation: 'grouped chronological holdout',
      targets: [{ id: 'M1.enrollment', target: 'program_enrollment_count', candidates: ['seasonal_naive', 'historical_mean', 'ols_lags'] }],
      us_models_not_compared: ['US LSTM'],
    })
    getExpertValidations.mockResolvedValue({
      expert_domains: ['higher_education'],
      rows: [{ id: 1, spec_id: 'M1.C1', expert_role: 'higher_education', verdict: 'accepted' }],
    })
    getAhpWeights.mockResolvedValue({ weights: null, refused: false })

    render(<AdminMethodologyPage />)
    await waitFor(() => expect(screen.getByTestId('learned_importance')).toBeInTheDocument())
    const learned = screen.getByTestId('learned_importance')
    const priority = screen.getByTestId('collection_priority')
    expect(learned.textContent).toMatch(/Learned importance/)
    expect(priority.textContent).toMatch(/Collection priority/)
    expect(learned.textContent).toMatch(/internships/)
    expect(priority.textContent).toMatch(/M1.C1/)
    expect(document.body.textContent).not.toMatch(/blended_score/)
    expect(document.body.textContent).not.toMatch(/blended score/i)
  })

  it('refuses an inconsistent AHP matrix in the UI', async () => {
    getFeatureImportance.mockResolvedValue(importance)
    getPriorityTiers.mockResolvedValue({ model1: [], model2: [] })
    getModelComparison.mockResolvedValue({ targets: [] })
    getExpertValidations.mockResolvedValue({ expert_domains: ['higher_education'], rows: [] })
    getAhpWeights.mockResolvedValue({ weights: null })
    postAhpWeights.mockRejectedValue(new Error('consistency_ratio_exceeds_0.1'))

    render(<AdminMethodologyPage />)
    await waitFor(() => expect(screen.getByTestId('ahp-empty')).toBeInTheDocument())
    await userEvent.click(screen.getByText('Compute weights'))
    expect(await screen.findByTestId('ahp-refused')).toBeInTheDocument()
    expect(screen.getByTestId('ahp-refused').textContent).toMatch(/consistency_ratio/)
  })
})

describe('W.ADM.08 searchable audit table', () => {
  it('filters rows from the search box', async () => {
    getAuditLog.mockResolvedValue({
      n: 2,
      rows: [
        { id: 1, actor: 'moe', action: 'report_export', resource: 'workforce', created_at: '2026-01-01T00:00:00' },
        { id: 2, actor: 'admin', action: 'scenario_run', resource: 'scenario:1', created_at: '2026-01-02T00:00:00' },
      ],
    })
    render(<AdminAuditLogPage />)
    await waitFor(() => expect(screen.getAllByTestId('audit-row')).toHaveLength(2))
    await userEvent.type(screen.getByTestId('audit-search'), 'report_export')
    expect(screen.getAllByTestId('audit-row')).toHaveLength(1)
    expect(screen.getByText('report_export')).toBeInTheDocument()
  })
})

describe('W.ADM.02 pipeline status list', () => {
  it('lists twenty feeds', async () => {
    const feeds = Array.from({ length: 20 }, (_, i) => ({
      source_table: `table_${i}`,
      family: 'education',
      rows: 10,
      status: 'ok',
      status_label: 'ok',
      freshness: 'current',
      tier: 'simulated',
      last_sync: '2026-01-01T00:00:00Z',
    }))
    getPipelineStatus.mockResolvedValue({ n: 20, feeds })
    render(<AdminPipelinePage />)
    await waitFor(() => expect(screen.getAllByTestId('pipeline-feed')).toHaveLength(20))
  })
})
