import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import useFetch from '../../hooks/useFetch'
import useDebounced from '../../hooks/useDebounced'
import { getPolicySimulator, persistPolicySimulator } from '../../api/roles'
import { SERIES, axisProps, gridProps, tooltipProps, fmtNum } from '../../config/chartTheme'

const FIELDS = [
  '',
  'Engineering & Technology',
  'Natural & Computational Sciences',
  'Medicine & Health Sciences',
  'Agriculture & Life Sciences',
  'Business & Economics',
  'Social Sciences & Humanities',
  'Law',
  'Education',
]

export default function PolicySimulatorPage() {
  const [quota, setQuota] = useState(1)
  const [capacity, setCapacity] = useState(1)
  const [natural, setNatural] = useState(0.7)
  const [passShift, setPassShift] = useState(0)
  const [horizon, setHorizon] = useState(1)
  const [priority, setPriority] = useState('')
  const [saved, setSaved] = useState(null)
  const [saving, setSaving] = useState(false)

  const params = {
    quota_scale: quota,
    capacity_scale: capacity,
    natural_share: natural,
    pass_rate_shift_pp: passShift,
    horizon,
    ...(priority ? { priority_field: priority } : {}),
  }
  // Sliders update the labels immediately but only run a scenario once the
  // value has settled: each run is audited and rate limited on the server.
  const settledKey = useDebounced(JSON.stringify(params), 400)
  const { data, loading, error, refetch } = useFetch(
    () => getPolicySimulator(JSON.parse(settledKey)),
    [settledKey],
  )

  const chart = data ? [
    { metric: 'Unconstrained demand', baseline: data.baseline?.unconstrained_demand, scenario: data.scenario?.unconstrained_demand },
    { metric: 'Constrained enrolment', baseline: data.baseline?.constrained_enrollment, scenario: data.scenario?.constrained_enrollment },
    { metric: 'Expected graduates', baseline: data.baseline?.expected_graduates, scenario: data.scenario?.expected_graduates },
  ] : []

  async function persist() {
    setSaving(true)
    try {
      const body = await persistPolicySimulator({
        quota_scale: quota,
        capacity_scale: capacity,
        natural_share: natural,
        pass_rate_shift_pp: passShift,
        priority_field: priority || null,
        name: 'policy-simulator',
        horizon,
      })
      setSaved(body)
    } catch (err) {
      setSaved({ error: err.message })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div>
      <SectionHeader
        title="Test a quota or placement change"
        subtitle="Quota, priority field, placement rule and capacity — a draft, not an official forecast"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      <DataNote tone="simulated">
        Scenario runs are not official forecasts. Each saved run keeps its assumptions attached, so it cannot be quoted as a baseline.
      </DataNote>
      <ForecastAccuracyNote />
      <div className="panel" style={{ marginTop: 16 }}>
        <p className="panel-title">Levers</p>
        <label className="sim-label">Quota scale {quota.toFixed(2)}</label>
        <input type="range" min="0.25" max="3" step="0.05" value={quota} onChange={e => setQuota(Number(e.target.value))} />
        <label className="sim-label">Capacity scale {capacity.toFixed(2)}</label>
        <input type="range" min="0.25" max="3" step="0.05" value={capacity} onChange={e => setCapacity(Number(e.target.value))} />
        <label className="sim-label">Band allocation — natural-science share {Math.round(natural * 100)}%</label>
        <input type="range" min="0.5" max="0.9" step="0.01" value={natural} onChange={e => setNatural(Number(e.target.value))} />
        <label className="sim-label">Placement rule — ESSLCE pass rate {passShift > 0 ? '+' : ''}{passShift} pp</label>
        <input type="range" min="-15" max="15" step="1" value={passShift} onChange={e => setPassShift(Number(e.target.value))} />
        <label className="sim-label">Horizon {horizon} year{horizon > 1 ? 's' : ''} — graduates respond only from about year 5</label>
        <input type="range" min="1" max="5" step="1" value={horizon} onChange={e => setHorizon(Number(e.target.value))} />
        <label className="sim-label">Priority field</label>
        <select value={priority} onChange={e => setPriority(e.target.value)} style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border)' }}>
          {FIELDS.map(f => <option key={f || 'none'} value={f}>{f || 'None'}</option>)}
        </select>
        <button type="button" className="sim-save" onClick={persist} disabled={saving}>
          {saving ? 'Saving draft…' : 'Persist unofficial scenario'}
        </button>
        {saved && !saved.error && (
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 8 }}>
            Saved as a {saved.status || 'draft'} scenario, not an official forecast.
          </p>
        )}
        {saved?.error && <ErrorBanner message={saved.error} />}
      </div>
      {loading && <LoadingSpinner message="Running scenario…" height={220} />}
      {data && (
        <div className="panel" style={{ marginTop: 16 }}>
          <p className="panel-title">Baseline vs scenario</p>
          <p className="panel-sub">{data.note}</p>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chart} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis dataKey="metric" {...axisProps} />
              <YAxis {...axisProps} tickFormatter={fmtNum} />
              <Tooltip {...tooltipProps} />
              <Legend />
              <Bar dataKey="baseline" name="Baseline" fill={SERIES[0]} />
              <Bar dataKey="scenario" name="Scenario" fill={SERIES[1]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
      <style>{`
        .sim-label { display: block; font-size: 12.5px; font-weight: 600; color: var(--navy); margin: 12px 0 4px; }
        input[type=range] { width: 100%; }
        .sim-save {
          margin-top: 16px; border: none; background: var(--navy); color: white;
          padding: 8px 14px; border-radius: 8px; font-weight: 600; cursor: pointer;
        }
        .sim-save:disabled { opacity: .6; cursor: default; }
      `}</style>
    </div>
  )
}
