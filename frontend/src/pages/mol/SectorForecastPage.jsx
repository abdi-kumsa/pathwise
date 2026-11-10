import { useState } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import ForecastChart from '../../components/ForecastChart'
import EmptyState from '../../components/EmptyState'
import EthiopiaRegionMap from '../../components/EthiopiaRegionMap'
import useFetch from '../../hooks/useFetch'
import { getLabourForecast } from '../../api/roles'

const GRAINS = [
  { id: 'sector,period',     label: 'Sector',     noun: 'sectors',     measure: 'Employment', target: 'M2.employment_demand' },
  { id: 'occupation,period', label: 'Occupation', noun: 'occupations', measure: 'Vacancies',  target: 'M2.vacancies' },
  { id: 'region,period',     label: 'Region',     noun: 'regions',     measure: 'Employment', target: 'M2.employment_demand' },
]
const MAX_SERIES = 6

// Employment where the grain has it; vacancies for occupations, which have no
// employment series of their own.
const valueOf = r => (r ? r.employment_demand ?? r.vacancies ?? r.occupational_demand ?? null : null)
const lowOf   = r => (r.employment_demand != null ? r.employment_demand_low  : r.vacancies_low)  ?? null
const highOf  = r => (r.employment_demand != null ? r.employment_demand_high : r.vacancies_high) ?? null
const byX = (a, b) => a.x - b.x

export default function SectorForecastPage() {
  const [grain, setGrain] = useState(GRAINS[0].id)
  const g = GRAINS.find(x => x.id === grain)
  const dim = grain.split(',')[0]
  const { data, loading, error, refetch } = useFetch(
    () => getLabourForecast(grain, 3),
    [grain],
  )
  const rows = data?.rows ?? []
  const history = data?.history ?? []
  const periods = [...new Set(rows.map(r => r.period))].sort()
  const firstForecast = periods[0]
  const lastForecast = periods[periods.length - 1]
  const observedYears = history.map(h => h.period)
  const firstObserved = observedYears.length ? Math.min(...observedYears) : null
  const lastObserved = observedYears.length ? Math.max(...observedYears) : null

  // Largest first-year forecasts first; six series is the most the chart reads at.
  const allKeys = [...new Set(rows.map(r => r[dim]).filter(Boolean))]
  const keys = allKeys
    .map(k => ({ k, v: Number(valueOf(rows.find(r => r[dim] === k && r.period === firstForecast)) ?? 0) }))
    .sort((a, b) => b.v - a.v)
    .slice(0, MAX_SERIES)
    .map(x => x.k)

  const series = keys.map(k => ({
    key: k,
    history: history
      .filter(h => h[dim] === k && valueOf(h) != null)
      .map(h => ({ x: h.period, y: Number(valueOf(h)) }))
      .sort(byX),
    forecast: rows
      .filter(r => r[dim] === k && valueOf(r) != null)
      .map(r => ({ x: r.period, y: Number(valueOf(r)), low: lowOf(r), high: highOf(r) }))
      .sort(byX),
  }))

  const mapRows = dim === 'region'
    ? rows.filter(r => r.period === lastForecast).map(r => ({
      name: r.region,
      value: Number(r.employment_demand || r.vacancies || 0),
    }))
    : []

  return (
    <div>
      <SectionHeader
        title="Where demand is heading"
        subtitle={lastObserved
          ? `Observed ${firstObserved}–${lastObserved}, forecast to ${lastForecast}`
          : 'Employment by sector and region, vacancies by occupation'}
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      <div className="mm-toggle" role="group" aria-label="Forecast grain" style={{ marginBottom: 12 }}>
        {GRAINS.map(x => (
          <button key={x.id} className={grain === x.id ? 'active' : ''} onClick={() => setGrain(x.id)}>{x.label}</button>
        ))}
      </div>
      {loading && <LoadingSpinner message="Loading forecast…" height={280} />}
      {data && rows.length === 0 && (
        <EmptyState title="No forecast rows" description={`No ${g.measure.toLowerCase()} series for this grain.`} />
      )}
      {data && rows.length > 0 && (
        <>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">{g.measure} by {g.label.toLowerCase()}</p>
            <p className="panel-sub">
              {g.measure === 'Employment' ? 'Employment level' : 'Vacancy count'}
              {allKeys.length > MAX_SERIES
                ? `, the ${MAX_SERIES} largest of ${allKeys.length} ${g.noun}`
                : `, all ${allKeys.length} ${g.noun}`}
            </p>
            <ForecastChart
              series={series}
              height={340}
              unit={g.measure === 'Employment' ? 'employment' : 'vacancies'}
              caption="A range for a total is the sum of the regional ranges, which is conservative."
            />
          </div>
          {dim === 'region' && (
            <div className="panel" style={{ marginTop: 16 }}>
              <p className="panel-title">Region map · {lastForecast}</p>
              <p className="panel-sub">Schematic regions, not an administrative map.</p>
              <EthiopiaRegionMap regions={mapRows} valueLabel="demand" />
            </div>
          )}
          <ForecastAccuracyNote accuracy={data.accuracy?.[g.target]} />
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
