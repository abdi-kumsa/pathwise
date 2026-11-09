import { useMemo, useState } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import EmptyState from '../../components/EmptyState'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getAuditLog } from '../../api/admin'

export default function AdminAuditLogPage() {
  const [draft, setDraft] = useState({ actor: '', action: '', resource: '', since: '', until: '' })
  const [query, setQuery] = useState({})
  const [search, setSearch] = useState('')
  const { data, loading, error, refetch } = useFetch(
    () => getAuditLog(clean(query)),
    [query.actor, query.action, query.resource, query.since, query.until],
  )
  const rows = data?.rows ?? []
  const visible = useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return rows
    return rows.filter(r =>
      `${r.actor} ${r.action} ${r.resource || ''} ${r.created_at || ''}`.toLowerCase().includes(q)
    )
  }, [rows, search])

  const submit = (e) => {
    e.preventDefault()
    setQuery({ ...draft })
  }

  return (
    <div>
      <SectionHeader
        title="Audit log"
        subtitle="Exports, model runs, scenario actions and user mutations"
      />
      <DataNote tone="info">
        Page views on known dashboard routes, searches, exports, scenario runs, institution drill-downs,
        grants and user changes are logged. Rows older than {data?.retention_days ?? 365} days are removed
        daily, and each removal is itself logged (action <code>audit_retention</code>). Search by actor,
        action, resource or date; filters match text literally.
        {data?.total != null && ` ${data.total.toLocaleString()} matching row(s).`}
      </DataNote>

      <form onSubmit={submit} className="panel" style={{ marginTop: 16, padding: 14, display: 'grid', gap: 10, gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))' }}>
        <label style={lab}>Actor
          <input value={draft.actor} onChange={e => setDraft({ ...draft, actor: e.target.value })} />
        </label>
        <label style={lab}>Action
          <input value={draft.action} onChange={e => setDraft({ ...draft, action: e.target.value })} />
        </label>
        <label style={lab}>Resource
          <input value={draft.resource} onChange={e => setDraft({ ...draft, resource: e.target.value })} />
        </label>
        <label style={lab}>Since
          <input type="date" value={draft.since} onChange={e => setDraft({ ...draft, since: e.target.value })} />
        </label>
        <label style={lab}>Until
          <input type="date" value={draft.until} onChange={e => setDraft({ ...draft, until: e.target.value })} />
        </label>
        <div style={{ display: 'flex', alignItems: 'end' }}>
          <button type="submit">Search API</button>
        </div>
      </form>

      <label style={{ ...lab, marginTop: 12, display: 'block' }}>
        Filter this page
        <input
          data-testid="audit-search"
          placeholder="actor, action, resource or date"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{ width: '100%', marginTop: 4 }}
        />
      </label>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading audit log…" height={240} />}

      {data && visible.length === 0 && (
        <EmptyState
          title="No audit rows"
          description={rows.length ? 'Nothing matches this search.' : 'Exports and simulator runs will appear here.'}
        />
      )}

      {visible.length > 0 && (
        <div className="panel" style={{ marginTop: 16, overflowX: 'auto' }}>
          <table data-testid="audit-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>
                <th style={th}>When</th>
                <th style={th}>Actor</th>
                <th style={th}>Action</th>
                <th style={th}>Resource</th>
              </tr>
            </thead>
            <tbody>
              {visible.map(row => (
                <tr key={row.id} data-testid="audit-row">
                  <td style={td}>{row.created_at?.replace('T', ' ').slice(0, 19)}</td>
                  <td style={td}>{row.actor}</td>
                  <td style={td}>{row.action}</td>
                  <td style={td}>{row.resource || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function clean(q) {
  const out = {}
  for (const [k, v] of Object.entries(q)) {
    if (v) out[k] = v
  }
  return out
}

const lab = { fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4 }
const th = { padding: '8px 10px', borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: 11, textTransform: 'uppercase' }
const td = { padding: '10px', borderBottom: '1px solid var(--border)' }
