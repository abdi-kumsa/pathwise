import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getCurriculumAlignment } from '../../api/roles'
import { ORDINAL_BLUE, STATUS } from '../../config/chartTheme'

const SKILL_COLS = [
  { key: 'technical_skill_demand', label: 'technical' },
  { key: 'digital_skill_demand', label: 'digital' },
  { key: 'soft_skill_demand', label: 'soft' },
  { key: 'emerging_skill_demand', label: 'emerging' },
]

function cellFill(value, max) {
  if (max <= 0 || value == null) return { bg: ORDINAL_BLUE[0], fg: '#0F172A' }
  const t = value / max
  if (t < 0.34) return { bg: ORDINAL_BLUE[0], fg: '#0F172A' }
  if (t < 0.67) return { bg: ORDINAL_BLUE[1], fg: '#0F172A' }
  return { bg: ORDINAL_BLUE[2], fg: '#FFFFFF' }
}

export default function CurriculumAlignmentPage() {
  const { data, loading, error, refetch } = useFetch(getCurriculumAlignment)
  const skills = data?.pathways?.skills ?? []
  const max = Math.max(
    0,
    ...skills.flatMap(s => SKILL_COLS.map(c => Number(s[c.key] || 0))),
  )

  return (
    <div>
      <SectionHeader
        title="Which skills the curriculum misses"
        subtitle="Employer skill demand versus the programme/field mapping"
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading curriculum alignment…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            {data.note || data.pathways?.note}
          </DataNote>
          {skills.length === 0 && (
            <EmptyState
              title="No skill mapping yet"
              description="Coverage is inferred from the join backbone until a ministry curriculum file exists."
            />
          )}
          {skills.length > 0 && (
            <div className="panel" style={{ marginTop: 16, overflowX: 'auto' }}>
              <p className="panel-title">Skill-demand heatmap</p>
              <p className="panel-sub">Coverage is inferred from the Ethiopia join backbone, not a curriculum file</p>
              <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 12 }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left', padding: '8px 10px', fontSize: 11, color: 'var(--text-muted)' }}>Field</th>
                    {SKILL_COLS.map(c => (
                      <th key={c.key} style={{ padding: '8px 10px', fontSize: 11, color: 'var(--text-muted)' }}>{c.label}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {skills.map(row => (
                    <tr key={row.field}>
                      <td style={{ textAlign: 'left', padding: '6px 10px', fontWeight: 500 }}>{row.field}</td>
                      {SKILL_COLS.map(c => {
                        const v = Number(row[c.key] || 0)
                        const tone = cellFill(v, max)
                        return (
                          <td key={c.key} style={{
                            padding: '6px 10px', textAlign: 'center',
                            background: tone.bg,
                            color: tone.fg,
                            fontVariantNumeric: 'tabular-nums',
                            fontSize: 12,
                          }}>
                            {v.toFixed(2)}
                          </td>
                        )
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 10 }}>
                Light → dark {ORDINAL_BLUE.join(' · ')} marks low → high employer demand.
              </p>
            </div>
          )}
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Programme health on the same mapping</p>
            {(data.program_health?.rows ?? []).map(r => (
              <div key={`${r.program || ''}-${r.field || ''}`} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span>{r.program || r.field}</span>
                <span style={{ color: r.status === 'shortage' ? STATUS.serious : r.status === 'oversupply' ? STATUS.warning : STATUS.good }}>
                  {r.status} · {r.action}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
