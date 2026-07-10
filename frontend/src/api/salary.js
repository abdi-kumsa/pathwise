import apiClient from './client'

export const getSalaryForecast = async () => {
  const response = await apiClient.get('/api/recommendations/salary-forecast')
  return response.data
}

export const predictSalary = async (profileData) => {
  const response = await apiClient.post('/api/recommendations/salary-predict', profileData)
  return response.data
}

export const getEscapeRoutes = async (profileData, topN = 5) => {
  const response = await apiClient.post('/api/recommendations/escape-routes', {
    ...profileData,
    top_n: topN,
  })
  return response.data
}

export const getProgramEscapeRoutes = async (program, topN = 5) => {
  const response = await apiClient.get('/api/recommendations/escape-routes', {
    params: { program, top_n: topN },
  })
  return response.data
}
