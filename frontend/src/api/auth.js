import client, { getToken, setToken, clearToken } from './client'

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

/** Exchange the current, still-valid token for a fresh one. */
export const refresh = async () => {
  const { data } = await client.post('/api/auth/refresh')
  setToken(data.access_token)
  return data.user
}

/**
 * Seconds until the stored token expires, read from its own `exp` claim.
 * Null when there is no token or it cannot be decoded. Reading the claim is
 * not a security check — the server verifies every request — it only tells
 * the client when to refresh.
 */
export const secondsUntilExpiry = () => {
  const token = getToken()
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return typeof payload.exp === 'number' ? payload.exp - Date.now() / 1000 : null
  } catch {
    return null
  }
}
