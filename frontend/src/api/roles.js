import client from './client'

// ── Careers (Student) ─────────────────────────────────────────────────────────

export const getJobs = async () => {
  const { data } = await client.get('/api/careers/jobs')
  return data
}

export const searchJobs = async (q, limit = 10) => {
  const { data } = await client.get('/api/careers/search', { params: { q, limit } })
  return data
}

export const getJobDetail = async (jobTitle) => {
  const { data } = await client.get(`/api/careers/job/${encodeURIComponent(jobTitle)}`)
  return data
}

/**
 * Recommend departments for a target job.
 * `profile` is optional — omit it and the API falls back to historical
 * placement rates instead of running the model on a specific student.
 */
export const recommendPrograms = async (jobTitle, profile = null, topN = 5) => {
  const { data } = await client.post('/api/careers/recommend', {
    job_title: jobTitle,
    top_n: topN,
    ...(profile ?? {}),
  })
  return data
}

// ── Labour market (MoL) ───────────────────────────────────────────────────────

export const getLabourOverview = async () => {
  const { data } = await client.get('/api/labour/overview')
  return data
}

export const getEmerging = async (level = 'family', topN = 10) => {
  const { data } = await client.get('/api/labour/emerging', { params: { level, top_n: topN } })
  return data
}

export const getSupplyDemand = async () => {
  const { data } = await client.get('/api/labour/supply-demand')
  return data
}

export const getMismatch = async (by = 'overview') => {
  const { data } = await client.get('/api/labour/mismatch', { params: { by } })
  return data
}

export const getRegionalDemand = async (field = null, topN = 20) => {
  const { data } = await client.get('/api/labour/regional', {
    params: { ...(field ? { field } : {}), top_n: topN },
  })
  return data
}

export const getOccupation = async (jobTitle) => {
  const { data } = await client.get(`/api/labour/occupation/${encodeURIComponent(jobTitle)}`)
  return data
}

// ── Education supply (MoE) ────────────────────────────────────────────────────

export const getEducationOverview = async () => {
  const { data } = await client.get('/api/education/overview')
  return data
}

export const getFieldTrends = async () => {
  const { data } = await client.get('/api/education/field-trends')
  return data
}

export const getInvestmentQuadrant = async () => {
  const { data } = await client.get('/api/education/investment-quadrant')
  return data
}

export const getFieldDetail = async (field) => {
  const { data } = await client.get(`/api/education/field/${encodeURIComponent(field)}`)
  return data
}

export const getDemandConstrainedComparison = async (horizon = 3) => {
  const { data } = await client.get('/api/education/demand-constrained-comparison', {
    params: { horizon },
  })
  return data
}

export const getEducationGap = async (horizon = 1) => {
  const { data } = await client.get('/api/education/supply-demand-gap', {
    params: { horizon },
  })
  return data
}

export const getPolicySimulator = async (params = {}) => {
  const { data } = await client.get('/api/education/policy-simulator', { params })
  return data
}

export const persistPolicySimulator = async (body) => {
  const { data } = await client.post('/api/education/policy-simulator', body)
  return data
}

export const getPolicyPriority = async (horizon = 1) => {
  const { data } = await client.get('/api/model3/policy-priority', { params: { horizon } })
  return data
}

export const getRegionalAlignment = async (horizon = 1) => {
  const { data } = await client.get('/api/education/regional-alignment', {
    params: { horizon },
  })
  return data
}

export const getInstitutionComparison = async (horizon = 1) => {
  const { data } = await client.get('/api/education/institution-comparison', {
    params: { horizon },
  })
  return data
}

export const getPolicyImpact = async () => {
  const { data } = await client.get('/api/education/policy-impact')
  return data
}

export const getFormalInformal = async (horizon = 3) => {
  const { data } = await client.get('/api/model2/formal-informal', { params: { horizon } })
  return data
}

export const getLabourForecast = async (groupBy = 'sector,period', horizon = 3) => {
  const { data } = await client.get('/api/model2/forecast', {
    params: { horizon, group_by: groupBy },
  })
  return data
}

export const getSkillsShortage = async (horizon = 3) => {
  const { data } = await client.get('/api/model2/skills-shortage', { params: { horizon } })
  return data
}

export const getPublicPipeline = async () => {
  const { data } = await client.get('/api/model2/public-pipeline')
  return data
}

export const getFdiPipeline = async () => {
  const { data } = await client.get('/api/model2/fdi-pipeline')
  return data
}

export const getGraduateAbsorption = async () => {
  const { data } = await client.get('/api/labour/graduate-absorption')
  return data
}

export const getMigration = async () => {
  const { data } = await client.get('/api/model2/migration')
  return data
}

export const getWorkforceReport = async (horizon = 3) => {
  const { data } = await client.get('/api/labour/workforce-report', { params: { horizon } })
  return data
}

export const downloadWorkforceReport = async (format) => {
  const { data } = await client.get('/api/labour/workforce-report', {
    params: { format },
    responseType: 'blob',
  })
  const url = window.URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = `workforce-report.${format}`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

// ── Institution (University) ──────────────────────────────────────────────────
// No institution parameter anywhere: the backend scopes these to the caller's
// own institution from their token.

export const getMyInstitution = async () => {
  const { data } = await client.get('/api/institution/me')
  return data
}

export const getPortfolio = async () => {
  const { data } = await client.get('/api/institution/portfolio')
  return data
}

export const getExpansion = async () => {
  const { data } = await client.get('/api/institution/expansion')
  return data
}

export const getResourceEfficiency = async () => {
  const { data } = await client.get('/api/institution/resources')
  return data
}

export const getPeerBenchmark = async () => {
  const { data } = await client.get('/api/institution/benchmark')
  return data
}

export const getProgramHealth = async () => {
  const { data } = await client.get('/api/institution/program-health')
  return data
}

export const getDemandVsLabour = async () => {
  const { data } = await client.get('/api/institution/demand-vs-labour')
  return data
}

export const getInstitutionFunnel = async () => {
  const { data } = await client.get('/api/institution/funnel')
  return data
}

export const getCohortProgression = async () => {
  const { data } = await client.get('/api/institution/cohort-progression')
  return data
}

export const getGraduateOutcomes = async () => {
  const { data } = await client.get('/api/institution/graduate-outcomes')
  return data
}

export const getResourcePlanning = async (quotaScale = 1, capacityScale = 1) => {
  const { data } = await client.get('/api/institution/resource-planning', {
    params: { quota_scale: quotaScale, capacity_scale: capacityScale },
  })
  return data
}

export const getCurriculumAlignment = async () => {
  const { data } = await client.get('/api/institution/curriculum-alignment')
  return data
}

export const getUnconstrainedDemand = async () => {
  const { data } = await client.get('/api/model1/demand/unconstrained', {
    params: { horizon: 3, group_by: 'program,academic_year' },
  })
  return data
}

export const getConstrainedDemand = async () => {
  const { data } = await client.get('/api/model1/demand/constrained', {
    params: { horizon: 3, group_by: 'program,academic_year' },
  })
  return data
}

// ── Cross-entity search ───────────────────────────────────────────────────────

export const globalSearch = async (q, limit = 15) => {
  const { data } = await client.get('/api/search', { params: { q, limit } })
  return data
}
