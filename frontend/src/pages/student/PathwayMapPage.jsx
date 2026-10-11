import { useMemo, useState } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getPathways } from '../../api/student'
import { SERIES, STATUS } from '../../config/chartTheme'

export default function PathwayMapPage() {
  const { data, loading, error, refetch } = useFetch(getPathways)
  const [selected, setSelected] = useState(null)
  const programs = (data?.programs ?? []).slice(0, 12)
  const occupations = (data?.occupations ?? []).slice(0, 14)
  const edges = data?.edges ?? []

  const layout = useMemo(() => {
    const left = programs.map((p, i) => ({
      id: p.program,
      kind: 'program',
      label: p.program,
      sub: p.field,
      x: 28,
      y: 28 + i * 36,
    }))
    const right = occupations.map((o, i) => ({
      id: o.occupation,
      kind: 'occupation',
      label: o.occupation,
      sub: o.field,
      x: 520,
      y: 28 + i * 32,
    }))
    const nodes = [...left, ...right]
    const byId = Object.fromEntries(nodes.map(n => [n.id, n]))
    const links = edges
      .filter(e => byId[e.source] && byId[e.target])
      .map(e => ({ ...e, a: byId[e.source], b: byId[e.target] }))
    return { nodes, links }
  }, [programs, occupations, edges])

  const related = selected
    ? edges.filter(e => e.source === selected || e.target === selected)
    : []

  return (
    <div>
      <SectionHeader
        title="Programme-to-occupation pathways"
        subtitle="Interactive map of the Ethiopia join backbone — click a node to highlight links"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading pathways…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">{data.note}</DataNote>
          {layout.nodes.length === 0 ? (
            <EmptyState title="No pathway nodes" description="Programme and occupation joins are empty." />
          ) : (
            <div className="panel" style={{ marginTop: 16 }} data-testid="pathway-graph">
              <p className="panel-title">Pathway graph</p>
              <p className="panel-sub">Programmes on the left, occupations on the right.</p>
              <svg viewBox="0 0 720 520" width="100%" height="520" role="img" aria-label="Programme to occupation pathway graph">
                {layout.links.map((e, i) => {
                  const on = selected && (e.source === selected || e.target === selected)
                  return (
                    <path
                      key={`${e.source}-${e.target}-${i}`}
                      d={`M ${e.a.x + 8} ${e.a.y} C 260 ${e.a.y}, 300 ${e.b.y}, ${e.b.x - 8} ${e.b.y}`}
                      fill="none"
                      stroke={on ? SERIES[0] : '#CBD5E1'}
                      strokeWidth={on ? 2.4 : 1}
                    />
                  )
                })}
                {layout.nodes.map(n => (
                  <g key={`${n.kind}-${n.id}`} onClick={() => setSelected(n.id)} style={{ cursor: 'pointer' }}>
                    <circle
                      cx={n.x}
                      cy={n.y}
                      r={selected === n.id ? 7 : 5}
                      fill={n.kind === 'program' ? SERIES[0] : SERIES[1]}
                    />
                    <text x={n.kind === 'program' ? n.x + 12 : n.x - 12} y={n.y + 4}
                      textAnchor={n.kind === 'program' ? 'start' : 'end'}
                      fontSize="11" fill={selected === n.id ? SERIES[0] : '#334155'}>
                      {n.label}
                    </text>
                  </g>
                ))}
              </svg>
            </div>
          )}
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">{selected ? `Links from ${selected}` : 'Select a node'}</p>
            {!selected && <EmptyState title="Nothing selected" description="Pick a programme or occupation on the graph." />}
            {related.map((e, i) => (
              <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid var(--border)', color: STATUS.good }}>
                {e.source} → {e.target}
                {e.sector ? ` · ${e.sector}` : ''}
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
