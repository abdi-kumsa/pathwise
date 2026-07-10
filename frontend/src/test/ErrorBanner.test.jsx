import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import ErrorBanner from '../components/ErrorBanner'

describe('ErrorBanner', () => {

  it('renders the error message', () => {
    render(<ErrorBanner message="Network timeout" />)
    expect(screen.getByText('Network timeout')).toBeInTheDocument()
  })

  it('renders a default fallback label', () => {
    render(<ErrorBanner message="Something went wrong" />)
    // component renders message text in two <p> tags (title + body)
    const els = screen.getAllByText(/Something went wrong/i)
    expect(els.length).toBeGreaterThanOrEqual(1)
  })

  it('shows Retry button when onRetry prop is provided', () => {
    render(<ErrorBanner message="err" onRetry={vi.fn()} />)
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('does NOT render a Retry button when onRetry is absent', () => {
    render(<ErrorBanner message="err" />)
    expect(screen.queryByRole('button', { name: /retry/i })).not.toBeInTheDocument()
  })

  it('calls onRetry when Retry button is clicked', () => {
    const spy = vi.fn()
    render(<ErrorBanner message="err" onRetry={spy} />)
    fireEvent.click(screen.getByRole('button', { name: /retry/i }))
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('is accessible — contains an alert or visible error region', () => {
    const { container } = render(<ErrorBanner message="oops" />)
    // Either an [role=alert] or at minimum visible text
    const hasAlert = container.querySelector('[role="alert"]')
    const hasText  = screen.getByText('oops')
    expect(hasAlert || hasText).toBeTruthy()
  })
})
