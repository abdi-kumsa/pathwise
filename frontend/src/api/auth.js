import client, { setToken, clearToken } from './client'

/**
 * Exchange credentials for a JWT.
 *
 * The backend expects the OAuth2 password form, not JSON, so this posts
 * URLSearchParams with an explicit content type rather than the client default.
 */
export const login = async (username, password) => {
  const body = new URLSearchParams({ username, password })
  const { data } = await client.post('/api/auth/login', body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  setToken(data.access_token)
  return data.user
}

/** Resolve the current user from a stored token. Used to rehydrate on boot. */
export const getMe = async () => {
  const { data } = await client.get('/api/auth/me')
  return data
}

/** The role vocabulary — public, used for the login page's demo hints. */
export const getRoles = async () => {
  const { data } = await client.get('/api/auth/roles')
  return data
}

export const logout = () => clearToken()
