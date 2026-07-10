/**
 * API layer tests — verify every function calls the correct URL
 * and forwards all parameters correctly.
 *
 * The Axios client is mocked at the module level so no real HTTP calls are made.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── mock the shared Axios client ──────────────────────────────────────────────
vi.mock('../api/client', () => ({
  default: {
    get:  vi.fn(),
    post: vi.fn(),
  },
}))

import apiClient from '../api/client'
import {
  getMarketOverview,
  getTopHiringCompanies,
  getRegionalHiringData,
  getSkillGapData,
  getJobInternshipRatio,
  getHiringSourceBreakdown,
  getDemandForecast,
} from '../api/marketDemand'

import {
  getEnrollmentSummary,
  getEnrollmentForecast,
  getAdmissionRisk,
  getPlacementByStream,
  submitStudentProfile,
  getSkillRecommendations,
} from '../api/enrollment'

// ─── helpers ─────────────────────────────────────────────────────────────────

const mockGet  = data => apiClient.get.mockResolvedValue({ data })
const mockPost = data => apiClient.post.mockResolvedValue({ data })

beforeEach(() => {
  vi.clearAllMocks()
})

// ─── Market API ───────────────────────────────────────────────────────────────

describe('marketDemand API', () => {

  it('getMarketOverview calls /api/market/overview', async () => {
    mockGet({ total_companies: 30 })
    const result = await getMarketOverview()
    expect(apiClient.get).toHaveBeenCalledWith('/api/market/overview')
    expect(result).toEqual({ total_companies: 30 })
  })

  it('getTopHiringCompanies calls /api/market/top-companies with default n=10', async () => {
    mockGet([])
    await getTopHiringCompanies()
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/market/top-companies',
      { params: { n: 10 } }
    )
  })

  it('getTopHiringCompanies forwards custom n value', async () => {
    mockGet([])
    await getTopHiringCompanies(5)
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/market/top-companies',
      { params: { n: 5 } }
    )
  })

  it('getRegionalHiringData calls /api/market/regional-hiring', async () => {
    mockGet([])
    await getRegionalHiringData()
    expect(apiClient.get).toHaveBeenCalledWith('/api/market/regional-hiring')
  })

  it('getSkillGapData calls /api/market/skill-gap', async () => {
    mockGet({})
    await getSkillGapData()
    expect(apiClient.get).toHaveBeenCalledWith('/api/market/skill-gap')
  })

  it('getJobInternshipRatio calls /api/market/job-internship-ratio', async () => {
    mockGet({})
    await getJobInternshipRatio()
    expect(apiClient.get).toHaveBeenCalledWith('/api/market/job-internship-ratio')
  })

  it('getHiringSourceBreakdown calls /api/market/hiring-sources', async () => {
    mockGet([])
    await getHiringSourceBreakdown()
    expect(apiClient.get).toHaveBeenCalledWith('/api/market/hiring-sources')
  })

  it('getDemandForecast calls /api/market/demand-forecast with default months=12', async () => {
    mockGet([])
    await getDemandForecast()
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/market/demand-forecast',
      { params: { months: 12 } }
    )
  })

  it('getDemandForecast forwards custom months value', async () => {
    mockGet([])
    await getDemandForecast(6)
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/market/demand-forecast',
      { params: { months: 6 } }
    )
  })
})

// ─── Enrollment API ───────────────────────────────────────────────────────────

describe('enrollment API', () => {

  it('getEnrollmentSummary calls /api/enrollment/summary', async () => {
    mockGet({ total_students: 3000 })
    const result = await getEnrollmentSummary()
    expect(apiClient.get).toHaveBeenCalledWith('/api/enrollment/summary')
    expect(result).toEqual({ total_students: 3000 })
  })

  it('getEnrollmentForecast calls correct URL with program and default years=3', async () => {
    mockGet({ forecast: [] })
    await getEnrollmentForecast('MS Data Science')
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/enrollment/forecast',
      { params: { program: 'MS Data Science', years: 3 } }
    )
  })

  it('getEnrollmentForecast forwards custom years value', async () => {
    mockGet({ forecast: [] })
    await getEnrollmentForecast('MS AI', 5)
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/enrollment/forecast',
      { params: { program: 'MS AI', years: 5 } }
    )
  })

  it('getAdmissionRisk calls correct URL with default limit=10', async () => {
    mockGet([])
    await getAdmissionRisk()
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/enrollment/admission-risk',
      { params: { limit: 10 } }
    )
  })

  it('getAdmissionRisk forwards custom limit', async () => {
    mockGet([])
    await getAdmissionRisk(5)
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/enrollment/admission-risk',
      { params: { limit: 5 } }
    )
  })

  it('getPlacementByStream calls /api/enrollment/placement-by-stream', async () => {
    mockGet([])
    await getPlacementByStream()
    expect(apiClient.get).toHaveBeenCalledWith('/api/enrollment/placement-by-stream')
  })

  it('submitStudentProfile POSTs to /api/enrollment/predict-placement with full profile', async () => {
    const profile = { gpa: 3.8, internships: 2, projects: 5, communication_score: 9, program: 'MS Data Science' }
    mockPost({ placement_probability: 0.97, prediction: 'Placed' })
    const result = await submitStudentProfile(profile)
    expect(apiClient.post).toHaveBeenCalledWith('/api/enrollment/predict-placement', profile)
    expect(result.prediction).toBe('Placed')
  })

  it('getSkillRecommendations calls /api/enrollment/skill-recommendations with no student_id by default', async () => {
    mockGet({ recommendations: [], alternative_pathways: [] })
    await getSkillRecommendations()
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/enrollment/skill-recommendations',
      { params: { student_id: undefined } }
    )
  })

  it('getSkillRecommendations forwards student_id when provided', async () => {
    mockGet({ recommendations: [] })
    await getSkillRecommendations(42)
    expect(apiClient.get).toHaveBeenCalledWith(
      '/api/enrollment/skill-recommendations',
      { params: { student_id: 42 } }
    )
  })
})
