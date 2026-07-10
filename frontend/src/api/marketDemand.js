/**
 * Phase 2 — Step 5
 * API service layer for Module 1: Market Demand Forecast Dashboard
 *
 * All functions use the existing Axios client configured in client.js.
 * Endpoints are placeholders — real implementation comes in Phase 4 (backend routers).
 */

import apiClient from './client'

/**
 * Get top hiring companies with job posting counts
 * @returns {Promise} Array of {company, count} objects
 */
export const getTopHiringCompanies = async (n = 10) => {
  const response = await apiClient.get('/api/market/top-companies', { params: { n } })
  return response.data
}

/**
 * Get regional hiring data (job postings by location)
 * @returns {Promise} Array of {location, count} objects
 */
export const getRegionalHiringData = async () => {
  const response = await apiClient.get('/api/market/regional-hiring')
  return response.data
}

/**
 * Get skill gap analysis data
 * @returns {Promise} Object with {demanded_skills, curriculum_coverage, gap_score}
 */
export const getSkillGapData = async () => {
  const response = await apiClient.get('/api/market/skill-gap')
  return response.data
}

/**
 * Get job-to-internship ratio
 * @returns {Promise} Object with {job_count, internship_count, ratio}
 */
export const getJobInternshipRatio = async () => {
  const response = await apiClient.get('/api/market/job-internship-ratio')
  return response.data
}

/**
 * Get hiring source breakdown (where job postings come from)
 * @returns {Promise} Array of {source, count} objects
 */
export const getHiringSourceBreakdown = async () => {
  const response = await apiClient.get('/api/market/hiring-sources')
  return response.data
}

export const getMarketOverview = async () => {
  const response = await apiClient.get('/api/market/overview')
  return response.data
}

export const getDemandForecast = async (months = 12) => {
  const response = await apiClient.get('/api/market/demand-forecast', { params: { months } })
  return response.data
}
