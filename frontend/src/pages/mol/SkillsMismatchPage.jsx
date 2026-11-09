import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getSkillsShortage } from '../../api/roles'
import { ORDINAL_BLUE } from '../../config/chartTheme'

const SKILL_CLASSES = [
  { key: 'technical_skill_demand', label: 'technical' },
  { key: 'digital_skill_demand', label: 'digital' },
  { key: 'soft_skill_demand', label: 'soft' },
  { key: 'emerging_skill_demand', label: 'emerging' },
]

function cellFill(value, max) {
  if (!max) return ORDINAL_BLUE[0]
  const t = Number(value || 0) / max
  if (t < 0.34) return ORDINAL_BLUE[0]
  if (t < 0.67) return ORDINAL_BLUE[1]
  return ORDINAL_BLUE[2]
}

export default function SkillsMismatchPage() {
  const { data, loading, error, refetch } = useFetch(getSkillsShortage)

  const skillRows = data?.rows ?? []
  const latest = skillRows.reduce((m, r) => Math.max(m, Number(r.period || 0)), 0)
  const heat = skillRows.filter(r => Number(r.period) === latest)
  const maxSkill = Math.max(0, ...heat.flatMap(r => SKILL_CLASSES.map(c => Number(r[c.key] || 0))))

  return (
    <div>
      <SectionHeader
        title="Where skills fall short"
        subtitle="Employer-demanded skills versus the graduate pipeline — skills, not credential fit"
      />
      <DataNote tone="simulated">
        Simulated Ethiopian structure. Credential-fit classification is not shown
        here and is not a ranking.
      </DataNote>
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading skills heatmap…" height={300} />}

      {data && heat.length === 0 && (
        <EmptyState title="No skill rows" description="The skills-shortage table is empty for this period." />
      )}

      {data && heat.length > 0 && (
        <div className="panel" style={{ marginTop: 16 }} data-testid="skills-heatmap">
          <p className="panel-title">Skills heatmap by field</p>
          <p className="panel-sub">Technical, digital, soft and emerging demand. Intensity is ordinal blue; the class name is in the header.</p>
          <div className="table-scroll">
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ textAlign: 'left' }}>Field</th>
                  {SKILL_CLASSES.map(c => (
                    <th key={c.key} data-testid="skill-class">{c.label}</th>
                  ))}
                  <th>Shortage index</th>
                </tr>
              </thead>
              <tbody>
                {heat.map(r => (
                  <tr key={r.field}>
                    <td style={{ textAlign: 'left', fontWeight: 500 }}>{r.field}</td>
                    {SKILL_CLASSES.map(c => (
                      <td key={c.key} className="num" style={{ background: cellFill(r[c.key], maxSkill) }}>
                        {Number(r[c.key] || 0).toFixed(2)}
                      </td>
                    ))}
                    <td className="num">{Number(r.skill_shortages || 0).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      <style>{`
        .table-scroll th {
          text-align: right; padding: 8px 12px; font-size: 11px; font-weight: 600;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em;
          border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 9px 12px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); text-align: right;
        }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
