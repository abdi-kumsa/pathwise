/**
 * Phase 2 — Step 6
 * API service layer for Module 2: Student Enrollment Intelligence Dashboard
 *
 * All functions use the existing Axios client configured in client.js.
 * Endpoints are placeholders — real implementation comes in Phase 4 (backend routers).
 */

import apiClient from './client'

/**
 * Get enrollment forecast for a specific program
 * @param {string} program - Program name (e.g., "MS Data Science")
 * @returns {Promise} Object with {program, forecast: [{year, predicted_count}]}
 */
export const getEnrollmentForecast = async (program, years = 3) => {
  const response = await apiClient.get('/api/enrollment/forecast', {
    params: { program, years }
  })
  return response.data
}

/**
 * Get admission risk analysis
 * @param {number} limit - Risk threshold percentage (5, 10, or 20)
 * @returns {Promise} Array of {program, risk_score, recommended_intake}
 */
export const getAdmissionRisk = async (limit = 10) => {
  const response = await apiClient.get('/api/enrollment/admission-risk', {
    params: { limit }
  })
  return response.data
}

/**
 * Get placement rate by program/stream
 * @returns {Promise} Array of {program, placement_rate, avg_salary}
 */
export const getPlacementByStream = async () => {
  const response = await apiClient.get('/api/enrollment/placement-by-stream')
  return response.data
}

/**
 * Submit student profile for placement prediction (XGBoost model)
 * @param {Object} profileData - {gpa, internships, projects, communication_score, program}
 * @returns {Promise} Object with {placement_probability, prediction, shap_values}
 */
export const submitStudentProfile = async (profileData) => {
  const response = await apiClient.post('/api/enrollment/predict-placement', profileData)
  return response.data
}

/**
 * Get AI skill recommendations for a student
 * @param {number} studentId - Student ID
 * @returns {Promise} Object with {student_id, recommendations: [{skill, priority}], alternative_pathways}
 */
export const getSkillRecommendations = async (studentId) => {
  const response = await apiClient.get('/api/enrollment/skill-recommendations', {
    params: { student_id: studentId }
  })
  return response.data
}

export const getEnrollmentSummary = async () => {
  const response = await apiClient.get('/api/enrollment/summary')
  return response.data
}

export const getSkillRoadmap = async (profileData) => {
  const response = await apiClient.post('/api/enrollment/skill-roadmap', profileData)
  return response.data
}
