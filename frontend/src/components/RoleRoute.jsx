import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import LoadingSpinner from './LoadingSpinner'

/**
 * Route guard.
 *
 * This is a usability layer, not the security boundary — every protected
 * endpoint enforces roles server-side, so hiding a route here only stops a user
 * landing on a page that would show them nothing but a 403.
 *
 * Three outcomes:
 *   not signed in  -> /login, remembering where they were headed
 *   wrong role     -> their own home page, rather than a dead end
 *   allowed        -> render
 */
export default function RoleRoute({ allow, children }) {
  const { user, booting } = useAuth()
  const location = useLocation()

  // Wait for the boot-time /me check, or a valid session flashes the login page.
  if (booting) {
    return <LoadingSpinner message="Restoring your session…" height={320} />
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  // No `allow` list means "any signed-in role".
  const permitted = !allow || allow.length === 0 || allow.includes(user.role)
  if (!permitted) {
    return <Navigate to={user.home ?? '/'} replace />
  }

  return children
}
