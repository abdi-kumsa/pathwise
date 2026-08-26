/**
 * User management — API mapping and the Modal's behaviour.
 *
 * The API layer is where camelCase UI state becomes the snake_case the backend
 * expects; a silent mismatch there sends `undefined` and looks like a no-op, so
 * each wrapper's exact call shape is asserted.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('../api/client', () => ({
  default: { get: vi.fn(), post: vi.fn(), patch: vi.fn(), delete: vi.fn() },
  getToken: vi.fn(), setToken: vi.fn(), clearToken: vi.fn(),
}))

import apiClient from '../api/client'
import {
  listUsers, createUser, updateUser, resetPassword,
  deactivateUser, reactivateUser, getInstitutionOptions, changeOwnPassword,
} from '../api/users'
import Modal from '../components/Modal'

const ok = (data) => ({ data })

beforeEach(() => {
  vi.clearAllMocks()
  apiClient.get.mockResolvedValue(ok([]))
  apiClient.post.mockResolvedValue(ok({}))
  apiClient.patch.mockResolvedValue(ok({}))
  apiClient.delete.mockResolvedValue(ok({}))
})

describe('users API', () => {

  it('lists users', async () => {
    apiClient.get.mockResolvedValue(ok([{ username: 'admin' }]))
    const out = await listUsers()
    expect(apiClient.get).toHaveBeenCalledWith('/api/users')
    expect(out).toEqual([{ username: 'admin' }])
  })

  it('maps create fields to the API shape', async () => {
    await createUser({
      username: 'newbie', password: 'secret123', role: 'STUDENT',
      displayName: 'New Person', institution: '',
    })
    expect(apiClient.post).toHaveBeenCalledWith('/api/users', {
      username: 'newbie',
      password: 'secret123',
      role: 'STUDENT',
      display_name: 'New Person',
      institution_name: null,      // empty string must become null, not ''
    })
  })

  it('passes an institution through for university accounts', async () => {
    await createUser({
      username: 'uni', password: 'secret123', role: 'UNIVERSITY',
      displayName: 'Uni', institution: 'Tech Institute',
    })
    expect(apiClient.post.mock.calls[0][1].institution_name).toBe('Tech Institute')
  })

  it('sends only the fields that changed', async () => {
    await updateUser('someone', { displayName: 'Renamed' })
    expect(apiClient.patch).toHaveBeenCalledWith(
      '/api/users/someone', { display_name: 'Renamed' },
    )
  })

  it('can send is_active false without it being dropped as falsy', async () => {
    await updateUser('someone', { isActive: false })
    expect(apiClient.patch.mock.calls[0][1]).toEqual({ is_active: false })
  })

  it('never sends a username in the update body', async () => {
    await updateUser('someone', { role: 'MOL', displayName: 'X' })
    expect(apiClient.patch.mock.calls[0][1]).not.toHaveProperty('username')
  })

  it('encodes usernames into the path', async () => {
    await updateUser('odd name', { role: 'MOL' })
    expect(apiClient.patch.mock.calls[0][0]).toBe('/api/users/odd%20name')
  })

  it('resets a password', async () => {
    await resetPassword('someone', 'brandnew123')
    expect(apiClient.post).toHaveBeenCalledWith(
      '/api/users/someone/password', { new_password: 'brandnew123' },
    )
  })

  it('deactivates via DELETE and reactivates via PATCH', async () => {
    await deactivateUser('someone')
    expect(apiClient.delete).toHaveBeenCalledWith('/api/users/someone')

    await reactivateUser('someone')
    expect(apiClient.patch).toHaveBeenCalledWith(
      '/api/users/someone', { is_active: true },
    )
  })

  it('fetches institution options from the meta route', async () => {
    await getInstitutionOptions()
    expect(apiClient.get).toHaveBeenCalledWith('/api/users/meta/institutions')
  })

  it('sends both passwords when changing your own', async () => {
    await changeOwnPassword('old-one', 'new-one-123')
    expect(apiClient.post).toHaveBeenCalledWith('/api/auth/change-password', {
      current_password: 'old-one',
      new_password: 'new-one-123',
    })
  })

  it('propagates API errors rather than swallowing them', async () => {
    apiClient.post.mockRejectedValue(new Error('Username is already taken.'))
    await expect(
      createUser({ username: 'dupe', password: 'secret123', role: 'STUDENT', displayName: 'D' })
    ).rejects.toThrow('Username is already taken.')
  })
})

describe('Modal', () => {

  it('renders nothing when closed', () => {
    const { container } = render(
      <Modal open={false} title="Hidden" onClose={() => {}}><p>body</p></Modal>
    )
    expect(container).toBeEmptyDOMElement()
  })

  it('renders title and children when open', () => {
    render(<Modal open title="Add account" subtitle="Sub" onClose={() => {}}>
      <p>form goes here</p>
    </Modal>)
    expect(screen.getByText('Add account')).toBeInTheDocument()
    expect(screen.getByText('Sub')).toBeInTheDocument()
    expect(screen.getByText('form goes here')).toBeInTheDocument()
  })

  it('is exposed as a modal dialog to assistive tech', () => {
    render(<Modal open title="Add account" onClose={() => {}}><p>x</p></Modal>)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(dialog).toHaveAttribute('aria-label', 'Add account')
  })

  it('closes on Escape', async () => {
    const onClose = vi.fn()
    render(<Modal open title="T" onClose={onClose}><p>x</p></Modal>)
    await userEvent.keyboard('{Escape}')
    expect(onClose).toHaveBeenCalled()
  })

  it('closes on the X button', async () => {
    const onClose = vi.fn()
    render(<Modal open title="T" onClose={onClose}><p>x</p></Modal>)
    await userEvent.click(screen.getByLabelText('Close'))
    expect(onClose).toHaveBeenCalled()
  })

  it('does not close when the panel itself is clicked', async () => {
    const onClose = vi.fn()
    render(<Modal open title="T" onClose={onClose}><p>inside</p></Modal>)
    await userEvent.click(screen.getByText('inside'))
    expect(onClose).not.toHaveBeenCalled()
  })

  it('moves focus into the dialog on open', async () => {
    render(
      <Modal open title="T" onClose={() => {}}>
        <input aria-label="first field" />
      </Modal>
    )
    await waitFor(() =>
      expect(screen.getByLabelText('first field')).toHaveFocus()
    )
  })

  it('restores page scrolling when it unmounts', () => {
    const { unmount } = render(<Modal open title="T" onClose={() => {}}><p>x</p></Modal>)
    expect(document.body.style.overflow).toBe('hidden')
    unmount()
    expect(document.body.style.overflow).not.toBe('hidden')
  })
})
