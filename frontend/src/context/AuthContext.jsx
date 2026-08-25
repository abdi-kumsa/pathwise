import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import * as authApi from '../api/auth'
import { getToken, clearToken } from '../api/client'

const AuthContext = createContext(null)

/**
 * Holds the signed-in user for the whole app.
 *
 * On boot, if a token is in localStorage we ask the API who it belongs to
 * rather than trusting a cached user object — the token may have expired while
 * the tab was closed, and /api/auth/me is the only authority on that.
 *
 * `booting` exists so routes do not flash the login page during that check.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [booting, setBooting] = useState(true)

  useEffect(() => {
    let cancelled = false

    const rehydrate = async () => {
      if (!getToken()) {
        setBooting(false)
        return
      }
      try {
        const me = await authApi.getMe()
        if (!cancelled) setUser(me)
      } catch {
        // Expired or tampered token — drop it and start clean.
        clearToken()
      } finally {
        if (!cancelled) setBooting(false)
      }
    }

    rehydrate()
    return () => { cancelled = true }
  }, [])

  const login = useCallback(async (username, password) => {
    const me = await authApi.login(username, password)
    setUser(me)
    return me
  }, [])

  const logout = useCallback(() => {
    authApi.logout()
    setUser(null)
  }, [])

  const value = {
    user,
    booting,
    login,
    logout,
    isAuthenticated: user !== null,
    role: user?.role ?? null,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (ctx === null) {
    throw new Error('useAuth must be used inside an AuthProvider')
  }
  return ctx
}

export default AuthContext
