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

export const getInvestmentPriority = async () => {
  const { data } = await client.get('/api/education/investment-priority')
  return data
}

export const getFieldDetail = async (field) => {
  const { data } = await client.get(`/api/education/field/${encodeURIComponent(field)}`)
  return data
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

// ── Cross-entity search ───────────────────────────────────────────────────────

export const globalSearch = async (q, limit = 15) => {
  const { data } = await client.get('/api/search', { params: { q, limit } })
  return data
}
