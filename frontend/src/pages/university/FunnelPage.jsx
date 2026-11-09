import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import EmptyState from '../../components/EmptyState'
import DataTable, { StatusWord } from '../../components/DataTable'
import Sparkline from '../../components/Sparkline'
import useFetch from '../../hooks/useFetch'
import { getInstitutionFunnel } from '../../api/roles'
import { ORDINAL_BLUE, STATUS, fmtNum, fmtPct } from '../../config/chartTheme'

const STAGES = [
  { key: 'applications', label: 'Applications' },
  { key: 'offers_placement', label: 'Offers / placement' },
  { key: 'acceptance', label: 'Acceptance' },
  { key: 'enrollment', label: 'Enrolment' },
]

const bound = r => r.binding_constraint && r.binding_constraint !== 'none'

const COLUMNS = [
  { key: 'program', label: 'Programme' },
  { key: 'trend', label: 'Applications, by year', sortable: false, render: r => <Sparkline values={r.trend ?? []} /> },
  { key: 'applications_count', label: 'Applications', align: 'right', render: r => fmtNum(r.applications_count) },
  { key: 'offers_count', label: 'Offers', align: 'right', render: r => fmtNum(r.offers_count) },
  { key: 'accepted_offers_count', label: 'Accepted', align: 'right', render: r => fmtNum(r.accepted_offers_count) },
  { key: 'yield_rate_pct', label: 'Yield', align: 'right', render: r => (r.yield_rate_pct == null ? '—' : fmtPct(r.yield_rate_pct, 0)) },
  {
    key: 'binding_constraint', label: 'Binding constraint',
    render: r => (
      <StatusWord status={r.binding_constraint || 'none'} color={bound(r) ? STATUS.serious : STATUS.good}>
        {(r.binding_constraint || 'none').replace(/_/g, ' ')}
      </StatusWord>
    ),
  },
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
  const constrainedLoss = rows.filter(bound)

  return (
    <div>
      <SectionHeader
        title="Where applicants drop out"
        subtitle={data ? `${data.institution}: applications, offers, acceptance and enrolment` : 'Loading…'}
      />
      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading funnel…" height={280} />}
      {data && (
        <>
          <DataNote tone="simulated">
            Where a drop is on the constraint side, the binding rule is named. Loss between offers and acceptance is yield, on the demand side.
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
                      <span style={{ fontWeight: 600 }}>{fmtNum(count)}</span>
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
            <p className="panel-title">By programme{latestYear ? ` · ${latestYear}` : ''}</p>
            <p className="panel-sub">
              {constrainedLoss.length
                ? `${constrainedLoss.length} of ${rows.length} programmes lose seats to a constraint rather than to demand.`
                : 'No programme is bound by a constraint on the latest run.'}
            </p>
            <DataTable
              columns={COLUMNS}
              rows={rows}
              rowKey={r => `${r.program}-${r.academic_year || r.year || ''}`}
              defaultSort={{ key: 'applications_count', dir: 'desc' }}
              emptyText="No programmes in the latest year"
            />
          </div>
        </>
      )}
    </div>
  )
}
