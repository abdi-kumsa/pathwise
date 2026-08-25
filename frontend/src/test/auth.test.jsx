/**
 * Auth layer — AuthContext session lifecycle and RoleRoute guarding.
 *
 * The auth API module is mocked so no HTTP happens; what is under test is the
 * state machine (boot → rehydrate → authenticated → logout) and the routing
 * decisions that hang off it.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'

// ── mocks ─────────────────────────────────────────────────────────────────────

vi.mock('../api/auth', () => ({
  login:   vi.fn(),
  getMe:   vi.fn(),
  logout:  vi.fn(),
  getRoles: vi.fn(),
}))

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), post: vi.fn(), interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } } },
  getToken:   vi.fn(),
  setToken:   vi.fn(),
  clearToken: vi.fn(),
}))

import * as authApi from '../api/auth'
import { getToken, clearToken } from '../api/client'
import { AuthProvider, useAuth } from '../context/AuthContext'
import RoleRoute from '../components/RoleRoute'

const STUDENT = {
  username: 'student', role: 'STUDENT', role_label: 'Student',
  display_name: 'Demo Student', institution: null, home: '/student/careers',
}

const MOE = {
  username: 'moe', role: 'MOE', role_label: 'Ministry of Education',
  display_name: 'MoE', institution: null, home: '/moe/overview',
}

/** Small probe that renders whatever the context currently holds. */
function Probe() {
  const { user, booting, isAuthenticated, role, login, logout } = useAuth()
  return (
    <div>
      <span data-testid="booting">{String(booting)}</span>
      <span data-testid="authed">{String(isAuthenticated)}</span>
      <span data-testid="role">{role ?? 'none'}</span>
      <span data-testid="name">{user?.display_name ?? 'none'}</span>
      <button onClick={() => login('student', 'pw')}>sign in</button>
      <button onClick={logout}>sign out</button>
    </div>
  )
}

const renderWithAuth = (ui = <Probe />) =>
  render(<MemoryRouter><AuthProvider>{ui}</AuthProvider></MemoryRouter>)

beforeEach(() => {
  vi.clearAllMocks()
})

afterEach(() => {
  vi.clearAllMocks()
})

// ─────────────────────────────────────────────────────────────────────────────

describe('AuthContext', () => {

  it('finishes booting with no user when no token is stored', async () => {
    getToken.mockReturnValue(null)
    renderWithAuth()

    await waitFor(() => expect(screen.getByTestId('booting')).toHaveTextContent('false'))
    expect(screen.getByTestId('authed')).toHaveTextContent('false')
    expect(authApi.getMe).not.toHaveBeenCalled()
  })

  it('rehydrates the session from a stored token', async () => {
    getToken.mockReturnValue('a.valid.token')
    authApi.getMe.mockResolvedValue(STUDENT)

    renderWithAuth()

    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('true'))
    expect(screen.getByTestId('role')).toHaveTextContent('STUDENT')
    expect(screen.getByTestId('name')).toHaveTextContent('Demo Student')
  })

  it('discards a token the API rejects', async () => {
    getToken.mockReturnValue('expired.token')
    authApi.getMe.mockRejectedValue(new Error('401'))

    renderWithAuth()

    await waitFor(() => expect(screen.getByTestId('booting')).toHaveTextContent('false'))
    expect(screen.getByTestId('authed')).toHaveTextContent('false')
    expect(clearToken).toHaveBeenCalled()
  })

  it('sets the user after a successful login', async () => {
    getToken.mockReturnValue(null)
    authApi.login.mockResolvedValue(STUDENT)

    renderWithAuth()
    await waitFor(() => expect(screen.getByTestId('booting')).toHaveTextContent('false'))

    await userEvent.click(screen.getByText('sign in'))

    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('true'))
    expect(authApi.login).toHaveBeenCalledWith('student', 'pw')
  })

  it('clears the user on logout', async () => {
    getToken.mockReturnValue('t')
    authApi.getMe.mockResolvedValue(STUDENT)

    renderWithAuth()
    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('true'))

    await userEvent.click(screen.getByText('sign out'))

    await waitFor(() => expect(screen.getByTestId('authed')).toHaveTextContent('false'))
    expect(authApi.logout).toHaveBeenCalled()
  })

  it('throws if useAuth is used outside a provider', () => {
    // React logs the error boundary trace; silence it for this one assertion.
    const spy = vi.spyOn(console, 'error').mockImplementation(() => {})
    expect(() => render(<Probe />)).toThrow(/AuthProvider/)
    spy.mockRestore()
  })
})

// ─────────────────────────────────────────────────────────────────────────────

describe('RoleRoute', () => {

  const routes = (
    <Routes>
      <Route path="/login" element={<p>login page</p>} />
      <Route path="/moe/overview" element={<p>moe home</p>} />
      <Route path="/student/careers" element={<p>student home</p>} />
      <Route path="/secret" element={
        <RoleRoute allow={['MOE']}><p>moe only content</p></RoleRoute>
      } />
      <Route path="/any" element={
        <RoleRoute><p>any signed-in content</p></RoleRoute>
      } />
    </Routes>
  )

  const renderAt = (path) =>
    render(
      <MemoryRouter initialEntries={[path]}>
        <AuthProvider>{routes}</AuthProvider>
      </MemoryRouter>
    )

  it('redirects an anonymous visitor to the login page', async () => {
    getToken.mockReturnValue(null)
    renderAt('/secret')
    await waitFor(() => expect(screen.getByText('login page')).toBeInTheDocument())
  })

  it('renders the page for a permitted role', async () => {
    getToken.mockReturnValue('t')
    authApi.getMe.mockResolvedValue(MOE)

    renderAt('/secret')
    await waitFor(() => expect(screen.getByText('moe only content')).toBeInTheDocument())
  })

  it('sends a disallowed role to its own home rather than a dead end', async () => {
    getToken.mockReturnValue('t')
    authApi.getMe.mockResolvedValue(STUDENT)

    renderAt('/secret')
    await waitFor(() => expect(screen.getByText('student home')).toBeInTheDocument())
    expect(screen.queryByText('moe only content')).not.toBeInTheDocument()
  })

  it('admits any signed-in role when no allow list is given', async () => {
    getToken.mockReturnValue('t')
    authApi.getMe.mockResolvedValue(STUDENT)

    renderAt('/any')
    await waitFor(() => expect(screen.getByText('any signed-in content')).toBeInTheDocument())
  })

  it('does not flash the login page while the session is being restored', async () => {
    getToken.mockReturnValue('t')
    // Never resolves, so the app stays in the booting state.
    authApi.getMe.mockReturnValue(new Promise(() => {}))

    renderAt('/secret')

    expect(screen.queryByText('login page')).not.toBeInTheDocument()
    expect(screen.queryByText('moe only content')).not.toBeInTheDocument()
    expect(screen.getByText(/Restoring your session/i)).toBeInTheDocument()
  })
})
