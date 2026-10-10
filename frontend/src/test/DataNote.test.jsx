import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataNote from '../components/DataNote'

describe('DataNote', () => {
  it('renders an info note by default', () => {
    render(<DataNote>Fit classification is not comparable across fields.</DataNote>)
    expect(screen.getByText(/not comparable/)).toBeInTheDocument()
  })

  it('supports the simulated tone required by Wave 0', () => {
    render(<DataNote tone="simulated">These figures are simulated Ethiopian structure, not official MoE statistics.</DataNote>)
    expect(screen.getByText(/not official MoE/)).toBeInTheDocument()
  })
})
