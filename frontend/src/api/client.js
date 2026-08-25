import axios from 'axios'

const TOKEN_KEY = 'pathwise.token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// Attach the bearer token to every outgoing request. Reading from localStorage
// per request rather than capturing it once means a fresh login takes effect
// immediately, with no need to rebuild the client.
client.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status

    // 401 means the token is missing, expired, or invalid — drop it and send
    // the user back to login. Skipped for the login call itself, where a 401 is
    // simply wrong credentials and must surface as an inline form error.
    const isLoginCall = error.config?.url?.includes('/api/auth/login')
    if (status === 401 && !isLoginCall) {
      clearToken()
      if (window.location.pathname !== '/login') {
        window.location.replace('/login?expired=1')
      }
    }

    // 403 is a role problem, not a session problem. Keep the session and let
    // the page render the message — logging out here would be baffling.
    const message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred'

    const wrapped = new Error(message)
    wrapped.status = status
    return Promise.reject(wrapped)
  }
)

export default client
