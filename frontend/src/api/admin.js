import client from './client'

export const getPlatformHealth = () =>
  client.get('/api/admin/platform-health').then(r => r.data)

export const getPipelineStatus = () =>
  client.get('/api/admin/pipeline-status').then(r => r.data)

export const getDataQuality = () =>
  client.get('/api/admin/data-quality').then(r => r.data)

export const getScenarios = () =>
  client.get('/api/admin/scenarios').then(r => r.data)

export const patchScenario = (id, status) =>
  client.patch(`/api/admin/scenarios/${id}`, { status }).then(r => r.data)

export const getAuditLog = (params = {}) =>
  client.get('/api/admin/audit-log', { params }).then(r => r.data)

export const getFeatureImportance = () =>
  client.get('/api/methodology/feature-importance').then(r => r.data)

export const getPriorityTiers = () =>
  client.get('/api/methodology/priority-tiers').then(r => r.data)

export const getModelComparison = () =>
  client.get('/api/methodology/model-comparison').then(r => r.data)

export const getExpertValidations = () =>
  client.get('/api/methodology/expert-validations').then(r => r.data)

export const postExpertValidation = (body) =>
  client.post('/api/methodology/expert-validations', body).then(r => r.data)

export const clearSeededExpertValidations = () =>
  client.post('/api/methodology/expert-validations/clear-seeded').then(r => r.data)

/** CSV of every DOC1 category with its latest recorded verdict; downloads in the browser. */
export const downloadExpertValidations = async () => {
  const { data } = await client.get('/api/methodology/expert-validations/export', { responseType: 'blob' })
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = 'expert-validations.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export const getAhpWeights = () =>
  client.get('/api/ahp/weights').then(r => r.data)

export const postAhpWeights = (body) =>
  client.post('/api/ahp/weights', body).then(r => r.data)

export const postAhpConsistency = (body) =>
  client.post('/api/ahp/consistency', body).then(r => r.data)

export const getDrift = (window = 100) =>
  client.get('/api/monitoring/drift', { params: { window } }).then(r => r.data)
