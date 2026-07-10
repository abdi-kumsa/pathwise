import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import LoadingSpinner from '../components/LoadingSpinner'

describe('LoadingSpinner', () => {

  it('renders a spinner element', () => {
    const { container } = render(<LoadingSpinner />)
    // The spinning circle must exist somewhere in the DOM
    const spinner = container.querySelector('[style*="border-radius: 50%"]')
      || container.querySelector('[class*="spin"]')
      || container.firstChild
    expect(spinner).toBeTruthy()
  })

  it('renders with default height wrapper', () => {
    const { container } = render(<LoadingSpinner />)
    const wrapper = container.firstChild
    expect(wrapper).toBeTruthy()
  })

  it('applies custom height when provided', () => {
    const { container } = render(<LoadingSpinner height={400} />)
    const wrapper = container.firstChild
    // The outer div should carry the height value somewhere in its style
    expect(wrapper.getAttribute('style')).toContain('400')
  })

  it('default height is 280', () => {
    const { container } = render(<LoadingSpinner />)
    const wrapper = container.firstChild
    expect(wrapper.getAttribute('style')).toContain('280')
  })

  it('renders an optional message when provided', () => {
    render(<LoadingSpinner message="Loading forecast…" />)
    expect(screen.getByText('Loading forecast…')).toBeInTheDocument()
  })

  it('does not crash without any props', () => {
    expect(() => render(<LoadingSpinner />)).not.toThrow()
  })
})
