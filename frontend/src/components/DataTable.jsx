import { useMemo, useState } from 'react'

/**
 * Dense, sortable table for list pages: one row per field, programme, region
 * or institution. Replaces the card grids and flex lists that made every page
 * the same length regardless of how much it had to say.
 *
 *   columns: [{ key, label, align: 'left' | 'right', width, render(row),
 *               sortValue(row), sortable = true, title }]
 *   rows:     plain objects; rowKey: property name or (row) => key
 *   rowProps: (row) => extra <tr> props, e.g. a data-testid or className
 *
 * Numbers go right-aligned (`align: 'right'`) so columns line up on the
 * digits; the body font already uses tabular numerals.
 */
export default function DataTable({
  columns, rows, rowKey, defaultSort, rowProps, emptyText = 'No rows', caption, className = '',
}) {
  const [sort, setSort] = useState(defaultSort ?? null)

  const sorted = useMemo(() => {
    if (!sort) return rows
    const col = columns.find(c => c.key === sort.key)
    if (!col) return rows
    const val = col.sortValue ?? (r => r[col.key])
    const dir = sort.dir === 'desc' ? -1 : 1
    return [...rows].sort((a, b) => {
      const x = val(a)
      const y = val(b)
      if (x == null && y == null) return 0
      if (x == null) return 1
      if (y == null) return -1
      if (typeof x === 'number' && typeof y === 'number') return (x - y) * dir
      return String(x).localeCompare(String(y)) * dir
    })
  }, [rows, sort, columns])

  const toggle = (c) => setSort(s => (
    s?.key === c.key
      ? { key: c.key, dir: s.dir === 'asc' ? 'desc' : 'asc' }
      : { key: c.key, dir: c.align === 'right' ? 'desc' : 'asc' }   // numbers: largest first
  ))
  const keyOf = typeof rowKey === 'function' ? rowKey : (r => r[rowKey])

  return (
    <div className="table-scroll">
      <table className={`data-table ${className}`.trim()}>
        {caption && <caption>{caption}</caption>}
        <thead>
          <tr>
            {columns.map(c => {
              const active = sort?.key === c.key
              const ariaSort = active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'
              return (
                <th
                  key={c.key}
                  className={c.align === 'right' ? 'num' : undefined}
                  style={c.width ? { width: c.width } : undefined}
                  aria-sort={c.sortable === false ? undefined : ariaSort}
                  title={c.title}
                >
                  {c.sortable === false ? c.label : (
                    <button type="button" className={`sort${active ? ' active' : ''}`} onClick={() => toggle(c)}>
                      {c.label}
                      <span className="sort-mark" aria-hidden="true">{active ? (sort.dir === 'asc' ? '↑' : '↓') : ''}</span>
                    </button>
                  )}
                </th>
              )
            })}
          </tr>
        </thead>
        <tbody>
          {sorted.length === 0 && (
            <tr><td colSpan={columns.length} className="empty">{emptyText}</td></tr>
          )}
          {sorted.map(r => (
            <tr key={keyOf(r)} {...(rowProps?.(r) ?? {})}>
              {columns.map(c => (
                <td key={c.key} className={c.align === 'right' ? 'num' : undefined}>
                  {c.render ? c.render(r) : (r[c.key] ?? '—')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/** A status in words with a small colour mark: the word carries the meaning. */
export function StatusWord({ status, color, children }) {
  return (
    <span className="status-word">
      <i style={{ background: color }} aria-hidden="true" />
      {children ?? status}
    </span>
  )
}
