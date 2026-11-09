import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent, within } from '@testing-library/react'

import DataTable, { StatusWord } from '../components/DataTable'
import Sparkline from '../components/Sparkline'

const columns = [
  { key: 'field', label: 'Field' },
  { key: 'demand', label: 'Demand', align: 'right' },
  { key: 'status', label: 'Status', render: r => <StatusWord status={r.status} color="#000" /> },
]
const rows = [
  { field: 'Health', demand: 300, status: 'shortage' },
  { field: 'Law', demand: 50, status: 'oversupply' },
  { field: 'ICT', demand: 120, status: 'balanced' },
]

const bodyCells = (col) =>
  within(screen.getAllByRole('rowgroup')[1]).getAllByRole('row').map(r => within(r).getAllByRole('cell')[col].textContent)

describe('DataTable', () => {
  it('renders one row per record with the status in words', () => {
    render(<DataTable columns={columns} rows={rows} rowKey="field" />)
    expect(bodyCells(0)).toEqual(['Health', 'Law', 'ICT'])
    expect(bodyCells(2)).toEqual(['shortage', 'oversupply', 'balanced'])
  })

  it('applies the default sort and flips direction on a second click', () => {
    render(<DataTable columns={columns} rows={rows} rowKey="field" defaultSort={{ key: 'demand', dir: 'desc' }} />)
    expect(bodyCells(1)).toEqual(['300', '120', '50'])
    fireEvent.click(screen.getByRole('button', { name: /Demand/ }))
    expect(bodyCells(1)).toEqual(['50', '120', '300'])
  })

  it('sorts a text column ascending first and numbers largest first', () => {
    render(<DataTable columns={columns} rows={rows} rowKey="field" />)
    fireEvent.click(screen.getByRole('button', { name: /Field/ }))
    expect(bodyCells(0)).toEqual(['Health', 'ICT', 'Law'])
    fireEvent.click(screen.getByRole('button', { name: /Demand/ }))
    expect(bodyCells(1)).toEqual(['300', '120', '50'])
  })

  it('passes rowProps through to the row', () => {
    render(
      <DataTable
        columns={columns} rows={rows} rowKey="field"
        rowProps={r => ({ 'data-testid': r.field === 'Law' ? 'own-field' : 'gap-row' })}
      />,
    )
    expect(screen.getByTestId('own-field')).toHaveTextContent('Law')
    expect(screen.getAllByTestId('gap-row')).toHaveLength(2)
  })

  it('shows the empty text when there are no rows', () => {
    render(<DataTable columns={columns} rows={[]} rowKey="field" emptyText="Nothing here" />)
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
  })
})

describe('Sparkline', () => {
  it('draws a path with first-to-last values in the label', () => {
    const { container } = render(<Sparkline values={[100, 120, null, 150]} />)
    expect(container.querySelector('path')).not.toBeNull()
    expect(screen.getByRole('img', { name: '100 → 150' })).toBeInTheDocument()
  })

  it('renders a dash with fewer than two finite values', () => {
    const { container } = render(<Sparkline values={[null, 5]} />)
    expect(container.querySelector('svg')).toBeNull()
    expect(container.textContent).toBe('—')
  })
})
