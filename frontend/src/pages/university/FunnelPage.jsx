import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import useFetch from '../../hooks/useFetch'
import { getInstitutionFunnel } from '../../api/roles'
import { ORDINAL_BLUE, STATUS, fmtNum } from '../../config/chartTheme'

const STAGES = [
  { key: 'applications', label: 'Applications' },
  { key: 'offers_placement', label: 'Offers / placement' },
  { key: 'acceptance', label: 'Acceptance' },
  { key: 'enrollment', label: 'Enrolment' },
]

export default function FunnelPage() {
  const { data, loading, error, refetch } = useFetch(getInstitutionFunnel)
  const stages = data?.stages ?? {}
  const allRows = data?.rows ?? []
  const latestYear = [...new Set(allRows.map(r => r.academic_year || r.year).filter(Boolean))].sort().at(-1)
  const rows = latestYear
    ? allRows.filter(r => (r.academic_year || r.year) === latestYear)
    : allRows.slice(0, 24)
  const counts = STAGES.map(s => Number(stages[s.key] || 0))
  const max = Math.max(...counts, 1)
  const constrainedLoss = rows.filter(r => r.binding_constraint && r.binding_constraint !== 'none')

  return (
    <div>
      <SectionHeader
        title="Application and placement funnel"
        subtitle={data ? `${data.institution} — applications → offers → acceptance → enrolment` : 'Loading…'}
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading funnel…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            When a drop is constraint-side, the binding rule is listed. Demand-side loss is yield between offers and acceptance.
          </DataNote>
          {counts.every(c => c === 0) && (
            <EmptyState title="Empty funnel" description="No applications or constrained enrolment for this institution." />
          )}
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Funnel stages</p>
            <div className="funnel" style={{ display: 'flex', flexDirection: 'column', gap: 18, marginTop: 8 }}>
              {STAGES.map((s, i) => {
                const count = counts[i]
                const prev = i === 0 ? null : counts[i - 1]
                const pct = (count / max) * 100
                const fill = ORDINAL_BLUE[i] ?? ORDINAL_BLUE[ORDINAL_BLUE.length - 1]
                return (
                  <div key={s.key}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)' }}>{s.label}</span>
                      <span style={{ fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{fmtNum(count)}</span>
                    </div>
                    <div style={{ height: 26, background: 'var(--page)', borderRadius: 6, overflow: 'hidden' }}>
                      <div style={{ width: `${Math.max(pct, 1.5)}%`, height: '100%', background: fill, borderRadius: 6 }} />
                    </div>
                    {prev != null && (
                      <span style={{ display: 'block', fontSize: 11, color: 'var(--text-muted)', marginTop: 5 }}>
                        {prev ? `${((count / prev) * 100).toFixed(1)}% of previous stage` : '—'}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
          <div className="panel" style={{ marginTop: 16 }}>
            <p className="panel-title">Binding constraint</p>
            <p className="panel-sub">
              {constrainedLoss.length
                ? 'Loss on these programmes is constraint-side, not a demand collapse.'
                : 'No binding constraint on the latest constrained run.'}
            </p>
            {rows.slice(0, 24).map(r => (
              <div key={`${r.program}-${r.academic_year || ''}`} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span>{r.program}</span>
                <span style={{ color: r.binding_constraint && r.binding_constraint !== 'none' ? STATUS.serious : STATUS.good }}>
                  {r.binding_constraint || 'none'}
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
