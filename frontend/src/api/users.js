import client from './client'

// ── Admin: user management ────────────────────────────────────────────────────

export const listUsers = async () => {
  const { data } = await client.get('/api/users')
  if (Array.isArray(data)) return data
  return data?.rows ?? []
}

export const createUser = async ({ username, password, role, displayName, institution }) => {
  const { data } = await client.post('/api/users', {
    username,
    password,
    role,
    display_name: displayName,
    // Only meaningful for UNIVERSITY; the API drops it for other roles.
    institution_name: institution || null,
  })
  return data
}

/** PATCH — send only what changed. Username is not updatable. */
export const updateUser = async (username, changes) => {
  const body = {}
  if (changes.role !== undefined)        body.role = changes.role
  if (changes.displayName !== undefined) body.display_name = changes.displayName
  if (changes.institution !== undefined) body.institution_name = changes.institution || null
  if (changes.isActive !== undefined)    body.is_active = changes.isActive

  const { data } = await client.patch(`/api/users/${encodeURIComponent(username)}`, body)
  return data
}

/** Admin reset — does not require the current password. */
export const resetPassword = async (username, newPassword) => {
  const { data } = await client.post(
    `/api/users/${encodeURIComponent(username)}/password`,
    { new_password: newPassword },
  )
  return data
}

/** Soft delete. Returns the updated user so the row can re-render. */
export const deactivateUser = async (username) => {
  const { data } = await client.delete(`/api/users/${encodeURIComponent(username)}`)
  return data
}

export const reactivateUser = (username) => updateUser(username, { isActive: true })

/** Institutions a UNIVERSITY account may be scoped to. */
export const getInstitutionOptions = async () => {
  const { data } = await client.get('/api/users/meta/institutions')
  return data
}

// ── Any role: own account ─────────────────────────────────────────────────────

export const changeOwnPassword = async (currentPassword, newPassword) => {
  await client.post('/api/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
