import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import EthiopiaRegionMap, { ETHIOPIA_REGIONS } from '../components/EthiopiaRegionMap'

describe('EthiopiaRegionMap', () => {
  it('renders all fourteen Wave 1 region names', () => {
    render(<EthiopiaRegionMap regions={ETHIOPIA_REGIONS.map(r => ({ name: r.name, value: 1 }))} />)
    expect(ETHIOPIA_REGIONS).toHaveLength(14)
    for (const r of ETHIOPIA_REGIONS) {
      expect(screen.getByTestId(`region-${r.name}`)).toBeInTheDocument()
    }
  })

  it('fires onSelect with the region name', () => {
    const onSelect = vi.fn()
    render(<EthiopiaRegionMap
      regions={[{ name: 'Oromia', value: 10, status: 'shortage' }]}
      onSelect={onSelect}
    />)
    fireEvent.click(screen.getByTestId('region-Oromia'))
    expect(onSelect).toHaveBeenCalledWith('Oromia')
  })
})
