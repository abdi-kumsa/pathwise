import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getEmerging } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps,
  fmtCompact, fmtMoney, fmtDelta, fmtNum,
} from '../../config/chartTheme'

/**
 * "Which field or department are emerging that show progress for future
 * investment" — the MoL half of that question.
 *
 * The trend chart plots at most three fields at once. That is not an arbitrary
 * cap: a multi-line chart puts every series beside every other, and only the
 * first three categorical slots clear the all-pairs colour-separation floors.
 * Selecting a fourth replaces the oldest rather than adding an unreadable hue.
 */
const MAX_COMPARE = 3

export default function EmergingOccupationsPage() {
  const [level, setLevel] = useState('family')
  const [selected, setSelected] = useState([])

  const { data, loading, error, refetch } = useFetch(
    () => getEmerging(level, level === 'family' ? 9 : 20),
    [level]
  )

  const rows = data ?? []
  const key = level === 'family' ? 'job_family' : 'job_title'

  // Default to the three fastest-growing once data lands.
  const active = selected.length ? selected : rows.slice(0, MAX_COMPARE).map(r => r[key])

  const toggle = (name) => {
    setSelected(prev => {
      const base = prev.length ? prev : rows.slice(0, MAX_COMPARE).map(r => r[key])
      if (base.includes(name)) {
        const next = base.filter(n => n !== name)
        return next.length ? next : base           // never empty the chart
      }
      return [...base, name].slice(-MAX_COMPARE)   // oldest drops out
    })
  }

  // Merge the per-row series into one year-indexed table for the line chart.
  const years = [...new Set(rows.flatMap(r => r.series.map(s => s.year)))].sort()
  const chartData = years.map(year => {
    const point = { year }
    for (const name of active) {
      const row = rows.find(r => r[key] === name)
      point[name] = row?.series.find(s => s.year === year)?.openings ?? null
    }
    return point
  })

  return (
    <div>
      <SectionHeader
        title="Emerging occupations"
        subtitle="Which parts of the labour market are growing, and how fast"
      />
      <DataNote tone="simulated">
        Simulated Ethiopian structure, 2016–2025. Not official MoLS statistics.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="eo-toolbar">
          <div className="eo-toggle" role="group" aria-label="Level of detail">
            <button className={level === 'family' ? 'active' : ''}
                    onClick={() => { setLevel('family'); setSelected([]) }}>
              By field
            </button>
            <button className={level === 'title' ? 'active' : ''}
                    onClick={() => { setLevel('title'); setSelected([]) }}>
              By occupation
            </button>
          </div>
          <p className="eo-hint">
            Select up to {MAX_COMPARE} rows to compare. A fourth replaces the oldest.
          </p>
        </div>
      </div>

      {loading && <LoadingSpinner message="Loading demand trends…" height={300} />}

      {!loading && rows.length > 0 && (
        <>
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Openings over time</p>
            <p className="panel-sub">Annual job openings, 2016–2025</p>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData} margin={{ top: 4, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="year" {...axisProps} />
                <YAxis {...axisProps} tickFormatter={fmtCompact} width={48} />
                <Tooltip {...tooltipProps} formatter={v => fmtNum(v)} />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} iconType="plainline" />
                {active.map((name, i) => (
                  <Line isAnimationActive={false}
                    key={name}
                    type="monotone"
                    dataKey={name}
                    stroke={SERIES[i]}
                    strokeWidth={2}
                    dot={{ r: 3, strokeWidth: 0, fill: SERIES[i] }}
                    activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2 }}
                    connectNulls
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="panel">
            <p className="panel-title">
              {level === 'family' ? 'Fields' : 'Occupations'} ranked by growth
            </p>
            <p className="panel-sub">Click a row to add or remove it from the chart above</p>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>{level === 'family' ? 'Field' : 'Occupation'}</th>
                    <th>Growth / yr</th>
                    <th>Total openings</th>
                    <th>Avg salary</th>
                    <th>Supply ratio</th>
                    <th>Time to fill</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map(r => {
                    const name = r[key]
                    const on = active.includes(name)
                    const slot = active.indexOf(name)
                    return (
                      <tr key={name} onClick={() => toggle(name)}
                          className={on ? 'row-active' : ''}>
                        <td style={{ textAlign: 'left' }}>
                          <span className="row-dot" style={{
                            background: on ? SERIES[slot] : 'transparent',
                            borderColor: on ? SERIES[slot] : 'var(--border)',
                          }} />
                          {name}
                          {level === 'title' && (
                            <span className="row-sub">{r.job_family}</span>
                          )}
                        </td>
                        <td className="num" style={{
                          color: r.openings_cagr_pct > 0 ? 'var(--green)' : 'var(--red)',
                          fontWeight: 600,
                        }}>
                          {fmtDelta(r.openings_cagr_pct)}
                        </td>
                        <td className="num">{fmtNum(r.total_openings)}</td>
                        <td className="num">{fmtMoney(r.avg_salary)}</td>
                        <td className="num">{r.supply_demand_ratio.toFixed(2)}</td>
                        <td className="num">{r.time_to_fill_days}d</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <style>{`
        .eo-toolbar {
          display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
        }
        .eo-toggle { display: flex; background: var(--page); border-radius: 9px; padding: 3px; }
        .eo-toggle button {
          border: none; background: none; padding: 7px 15px; border-radius: 7px;
          font-size: 13px; font-weight: 500; color: var(--text-secondary);
          cursor: pointer; font-family: inherit;
        }
        .eo-toggle button.active {
          background: var(--white); color: var(--navy); font-weight: 600;
          box-shadow: var(--shadow-card);
        }
        .eo-hint { font-size: 12px; color: var(--text-muted); }

        .table-scroll th {
          text-align: right; padding: 8px 12px; font-size: 11px;
          font-weight: 600; color: var(--text-muted); text-transform: uppercase;
          letter-spacing: .04em; border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 9px 12px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); text-align: right;
        }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
        .table-scroll tbody tr { cursor: pointer; }
        .table-scroll tbody tr:hover { background: #FAFBFD; }
        .table-scroll tbody tr.row-active { background: var(--blue-light); }
        .row-dot {
          display: inline-block; width: 9px; height: 9px; border-radius: 50%;
          border: 1.5px solid; margin-right: 9px; vertical-align: middle;
        }
        .row-sub {
          display: block; font-size: 11px; color: var(--text-muted); margin-left: 18px;
        }
      `}</style>
    </div>
  )
}
