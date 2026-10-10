import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ProvenanceBadge from '../components/ProvenanceBadge'
import useProvenance, { DEFAULT_PROVENANCE } from '../hooks/useProvenance'
import { renderHook } from '@testing-library/react'

describe('ProvenanceBadge', () => {
  it('renders source and vintage', () => {
    render(<ProvenanceBadge provenance={DEFAULT_PROVENANCE} />)
    expect(screen.getByText(/Simulated Ethiopian structure/)).toBeInTheDocument()
    expect(screen.getByText(/2016–2025/)).toBeInTheDocument()
  })

  it('exposes the tier for honesty sweeps', () => {
    const { container } = render(<ProvenanceBadge provenance={DEFAULT_PROVENANCE} />)
    expect(container.firstChild.getAttribute('data-tier')).toBe('simulated')
  })

  it('renders nothing without a stamp', () => {
    const { container } = render(<ProvenanceBadge provenance={null} />)
    expect(container.firstChild).toBeNull()
  })
})

describe('useProvenance', () => {
  it('reads the block off a stamped payload', () => {
    const { result } = renderHook(() =>
      useProvenance({ provenance: { source: 'MoE EMIS', tier: 'official', as_of: '2024', method: 'upload' } })
    )
    expect(result.current.tier).toBe('official')
    expect(result.current.source).toBe('MoE EMIS')
  })

  it('falls back to the Wave 0 default', () => {
    const { result } = renderHook(() => useProvenance(null))
    expect(result.current).toEqual(DEFAULT_PROVENANCE)
  })
})
