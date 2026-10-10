import client from './client'

export const getStudentProfile = async () => {
  const { data } = await client.get('/api/student/profile')
  return data
}

export const getLabourOutlook = async (field) => {
  const { data } = await client.get('/api/student/labour-outlook', { params: field ? { field } : {} })
  return data
}

export const getDemandComparison = async () => {
  const { data } = await client.get('/api/student/demand-comparison')
  return data
}

export const getFieldAlignment = async () => {
  const { data } = await client.get('/api/student/field-alignment')
  return data
}

export const getSupplyDemandGap = async () => {
  const { data } = await client.get('/api/student/supply-demand-gap')
  return data
}

export const getAlternatives = async (currentField) => {
  const { data } = await client.get('/api/student/alternatives', {
    params: currentField ? { current_field: currentField } : {},
  })
  return data
}

export const getSkillGaps = async () => {
  const { data } = await client.get('/api/student/skill-gaps')
  return data
}

export const getPathways = async () => {
  const { data } = await client.get('/api/student/pathways')
  return data
}

export const getOpportunities = async () => {
  const { data } = await client.get('/api/student/opportunities')
  return data
}
