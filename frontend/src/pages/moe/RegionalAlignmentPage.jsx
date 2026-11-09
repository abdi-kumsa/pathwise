import { useState } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EthiopiaRegionMap from '../../components/EthiopiaRegionMap'
import useFetch from '../../hooks/useFetch'
import { getRegionalAlignment } from '../../api/roles'
import { STATUS, fmtNum } from '../../config/chartTheme'

const STATUS_COLOR = {
  shortage: STATUS.serious,
  balanced: STATUS.good,
  oversupply: STATUS.warning,
}

export default function RegionalAlignmentPage() {
  const { data, loading, error, refetch } = useFetch(getRegionalAlignment)
  const [selected, setSelected] = useState(null)
  const rows = data?.rows ?? []
  const latest = rows.reduce((m, r) => Math.max(m, Number(r.period || 0)), 0)
  const now = rows.filter(r => Number(r.period) === latest)
  const byRegion = {}
  now.forEach(r => {
    const name = r.region
    if (!name) return
    const cur = byRegion[name] || { name, value: 0, status: 'balanced', gap: 0 }
    const gap = Number(r.signed_gap || 0)
    cur.value += Math.abs(gap)
    cur.gap += gap
    byRegion[name] = cur
  })
  Object.values(byRegion).forEach(r => {
    r.status = r.gap > 0 ? 'shortage' : r.gap < 0 ? 'oversupply' : 'balanced'
  })
  const regions = Object.values(byRegion)
  const fields = now.filter(r => r.region === selected)

  return (
    <div>
      <SectionHeader
        title="Regional education–labour alignment"
        subtitle="Enrolment, graduate supply and labour demand by region"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading regional alignment…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Schematic dashboard regions, not a CSA administrative map. 2023 SNNP splits will not match Natural Earth.
          </DataNote>
          <ForecastAccuracyNote />
          <div className="card-grid-2" style={{ marginTop: 16 }}>
            <div className="panel">
              <p className="panel-title">Ethiopia regions</p>
              <p className="panel-sub">Colour is shortage / balanced / oversupply; the word is on the tile and in the table.</p>
              <EthiopiaRegionMap regions={regions} selected={selected} onSelect={setSelected} valueLabel="|gap|" />
            </div>
            <div className="panel">
              <p className="panel-title">{selected ? `${selected} · field breakdown` : 'Select a region'}</p>
              {!selected && <p className="panel-sub">Click a region on the map.</p>}
              {selected && (
                <p className="panel-sub" data-testid="regional-triple">
                  Enrolment, expected graduates and labour demand for the latest period.
                </p>
              )}
              {selected && fields.map(r => (
                <div key={r.field} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>{r.field}</span>
                    <span>
                      <strong style={{ color: STATUS_COLOR[r.status] }}>{r.status}</strong>
                      {' '}· gap {fmtNum(r.signed_gap)} · Q{r.severity}
                    </span>
                  </div>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4 }}>
                    Enrolment {fmtNum(r.enrollment)} · graduates {fmtNum(r.expected_graduates)} · labour {fmtNum(r.labour_demand)}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
