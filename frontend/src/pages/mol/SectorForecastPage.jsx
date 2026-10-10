import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import EthiopiaRegionMap from '../../components/EthiopiaRegionMap'
import useFetch from '../../hooks/useFetch'
import { getLabourForecast } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, colorFor, fmtNum } from '../../config/chartTheme'

const GRAINS = [
  { id: 'sector,period', label: 'Sector' },
  { id: 'occupation,period', label: 'Occupation' },
  { id: 'region,period', label: 'Region' },
]

export default function SectorForecastPage() {
  const [grain, setGrain] = useState('sector,period')
  const dim = grain.split(',')[0]
  const { data, loading, error, refetch } = useFetch(
    () => getLabourForecast(grain, 3),
    [grain],
  )
  const rows = data?.rows ?? []
  const keys = [...new Set(rows.map(r => r[dim]).filter(Boolean))]
  const periods = [...new Set(rows.map(r => r.period))].sort()
  const chart = periods.map(period => {
    const point = { period }
    keys.forEach(k => {
      const hit = rows.find(r => r.period === period && r[dim] === k)
      point[k] = Number(hit?.employment_demand || hit?.vacancies || hit?.occupational_demand || 0)
    })
    return point
  })
  const regionLatest = periods[periods.length - 1]
  const mapRows = dim === 'region'
    ? rows.filter(r => r.period === regionLatest).map(r => ({
      name: r.region,
      value: Number(r.employment_demand || r.vacancies || 0),
    }))
    : []

  return (
    <div>
      <SectionHeader
        title="Sector and occupational demand forecast"
        subtitle="Projected demand by sector, occupation and region"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      <div className="mm-toggle" role="group" aria-label="Forecast grain" style={{ marginBottom: 12 }}>
        {GRAINS.map(g => (
          <button key={g.id} className={grain === g.id ? 'active' : ''} onClick={() => setGrain(g.id)}>{g.label}</button>
        ))}
      </div>
      {loading && <LoadingSpinner message="Loading forecast…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            group_by={grain}. Employment demand (or vacancies when demand is empty) on one scale.
          </DataNote>
          {rows.length === 0 ? (
            <EmptyState title="No forecast rows" description="No employment-demand series for this grain." />
          ) : (
            <>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Forecast by {dim}</p>
            <ResponsiveContainer width="100%" height={320}>
              <LineChart data={chart} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="period" {...axisProps} />
                <YAxis {...axisProps} tickFormatter={fmtNum} />
                <Tooltip {...tooltipProps} />
                <Legend />
                {keys.slice(0, 6).map(k => (
                  <Line key={k} type="monotone" dataKey={k} name={k} stroke={colorFor(k, keys)} strokeWidth={2} dot={false} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
          {dim === 'region' && (
            <div className="panel" style={{ marginTop: 16 }}>
              <p className="panel-title">Region map · {regionLatest}</p>
              <p className="panel-sub">Schematic dashboard regions, not a CSA administrative map.</p>
              <EthiopiaRegionMap regions={mapRows} valueLabel="demand" />
            </div>
          )}
            </>
          )}
        </>
      )}
      <style>{`
        .mm-toggle { display: inline-flex; background: var(--page); border-radius: 9px; padding: 3px; }
        .mm-toggle button {
          border: none; background: none; padding: 7px 14px; border-radius: 7px;
          font-size: 12.5px; font-weight: 500; color: var(--text-secondary); cursor: pointer; font-family: inherit;
        }
        .mm-toggle button.active {
          background: var(--white); color: var(--navy); font-weight: 600; box-shadow: var(--shadow-card);
        }
      `}</style>
    </div>
  )
}
