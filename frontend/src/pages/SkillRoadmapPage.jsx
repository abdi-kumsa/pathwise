import SectionHeader from '../components/SectionHeader'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorBanner from '../components/ErrorBanner'
import DataNote from '../components/DataNote'
import EmptyState from '../components/EmptyState'
import useFetch from '../hooks/useFetch'
import { getSkillGaps } from '../api/student'
import { SERIES } from '../config/chartTheme'

const CLASSES = [
  { key: 'technical_skill_demand', label: 'technical', color: SERIES[0] },
  { key: 'digital_skill_demand', label: 'digital', color: SERIES[1] },
  { key: 'soft_skill_demand', label: 'soft', color: SERIES[2] },
  { key: 'emerging_skill_demand', label: 'emerging', color: SERIES[3] },
]

export default function SkillRoadmapPage() {
  const { data, loading, error, refetch } = useFetch(getSkillGaps)
  const rows = data?.rows ?? []

  return (
    <div>
      <SectionHeader
        title="Skills to add"
        subtitle="Technical, digital and soft skills mapped onto the MoE programme list"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading skills…" height={240} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Skill classes required by the widget: {(data.skill_classes || ['technical', 'digital', 'soft']).join(', ')}.
            Emerging is shown when the table carries it.
          </DataNote>
          {rows.length === 0 && (
            <EmptyState title="No skill rows" description="The skill-gap table is empty for this field." />
          )}
          {rows.map(row => (
            <div key={row.field || row.program} className="panel" style={{ marginTop: 14 }}>
              <p className="panel-title">{row.program || row.field}</p>
              <p className="panel-sub">{row.field} · net pressure {Number(row.net_pressure || 0).toFixed(2)}</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
                {CLASSES.map(c => (
                  <span key={c.label} data-testid={`skill-${c.label}`} style={{
                    fontSize: 12, fontWeight: 600, padding: '5px 10px', borderRadius: 999,
                    background: 'var(--page)', border: `1px solid ${c.color}`, color: c.color,
                  }}>
                    {c.label} {row[c.key] != null ? Number(row[c.key]).toFixed(2) : '—'}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  )
}
