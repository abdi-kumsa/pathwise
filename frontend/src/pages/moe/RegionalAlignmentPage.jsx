import { useState } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import ForecastAccuracyNote from '../../components/ForecastAccuracyNote'
import EthiopiaRegionMap from '../../components/EthiopiaRegionMap'
import DataTable, { StatusWord } from '../../components/DataTable'
import GapTable, { GAP_STATUS_COLOR } from '../../components/GapTable'
import useFetch from '../../hooks/useFetch'
import { getRegionalAlignment } from '../../api/roles'
import { STATUS, fmtNum, fmtPct } from '../../config/chartTheme'

// Same rule as the field table: coverage below 0.85 is a shortage, above 1.15
// an oversupply, so a region and its fields are judged the same way.
const statusOf = (graduates, demand) => {
  if (!demand) return 'balanced'
  const c = graduates / demand
  return c < 0.85 ? 'shortage' : c > 1.15 ? 'oversupply' : 'balanced'
}

export default function RegionalAlignmentPage() {
  const { data, loading, error, refetch } = useFetch(getRegionalAlignment)
  const [selected, setSelected] = useState(null)
  const rows = data?.rows ?? []
  const latest = rows.reduce((m, r) => Math.max(m, Number(r.period || 0)), 0)
  const now = rows.filter(r => Number(r.period) === latest)

  const byRegion = {}
  now.forEach(r => {
    if (!r.region) return
    const cur = byRegion[r.region] ?? {
      name: r.region, enrollment: 0, expected_graduates: 0, labour_demand: 0, fields: 0,
    }
    cur.enrollment += Number(r.enrollment || 0)
    cur.expected_graduates += Number(r.expected_graduates || 0)
    cur.labour_demand += Number(r.labour_demand || 0)
    cur.fields += 1
    byRegion[r.region] = cur
  })
  const regions = Object.values(byRegion).map(r => {
    const gap = r.labour_demand - r.expected_graduates
    return {
      ...r,
      gap,
      value: Math.abs(gap),
      coverage_pct: r.labour_demand ? (r.expected_graduates / r.labour_demand) * 100 : null,
      status: statusOf(r.expected_graduates, r.labour_demand),
    }
  })
  const fields = now.filter(r => r.region === selected)

  const regionColumns = [
    { key: 'name', label: 'Region' },
    { key: 'enrollment', label: 'Enrolment', align: 'right', render: r => fmtNum(Math.round(r.enrollment)) },
    { key: 'expected_graduates', label: 'Graduates', align: 'right', render: r => fmtNum(Math.round(r.expected_graduates)) },
    { key: 'labour_demand', label: 'Labour demand', align: 'right', render: r => fmtNum(Math.round(r.labour_demand)) },
    { key: 'gap', label: 'Demand − graduates', align: 'right', render: r => fmtNum(Math.round(r.gap)) },
    { key: 'coverage_pct', label: 'Coverage', align: 'right', render: r => (r.coverage_pct == null ? '—' : fmtPct(r.coverage_pct, 0)) },
    { key: 'status', label: 'Status', render: r => <StatusWord status={r.status} color={GAP_STATUS_COLOR[r.status] ?? STATUS.warning} /> },
  ]

  return (
    <div>
      <SectionHeader
        title="Which regions are misaligned"
        subtitle={latest ? `Enrolment, expected graduates and labour demand by region, ${latest}` : 'Enrolment, expected graduates and labour demand by region'}
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading regional alignment…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Schematic regions, not an official administrative map; the 2023 SNNP splits are approximate.
          </DataNote>
          <div className="map-table-grid" style={{ marginTop: 16 }}>
            <div className="panel">
              <p className="panel-title">Regions</p>
              <p className="panel-sub">Shaded by the size of the gap; pick a region here or in the table</p>
              <EthiopiaRegionMap regions={regions} selected={selected} onSelect={setSelected} valueLabel="|gap|" />
            </div>
            <div className="panel">
              <p className="panel-title">By region</p>
              <p className="panel-sub">Totals across fields; click a row to see its fields</p>
              <DataTable
                columns={regionColumns}
                rows={regions}
                rowKey="name"
                defaultSort={{ key: 'gap', dir: 'desc' }}
                rowProps={r => ({
                  className: 'selectable',
                  'aria-selected': r.name === selected,
                  onClick: () => setSelected(r.name === selected ? null : r.name),
                })}
              />
            </div>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">{selected ? `${selected}, by field` : 'Fields in a region'}</p>
            {!selected && <p className="panel-sub">Select a region on the map or in the table.</p>}
            {selected && (
              <p className="panel-sub" data-testid="regional-triple">
                Enrolment, expected graduates and labour demand for {latest}.
              </p>
            )}
            {selected && <GapTable rows={fields} trendYears={data.trend_years} />}
          </div>
          <ForecastAccuracyNote />
        </>
      )}
    </div>
  )
}
