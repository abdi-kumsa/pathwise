import { useState } from 'react'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import EmptyState from '../../components/EmptyState'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getScenarios, patchScenario } from '../../api/admin'

const STATUSES = ['draft', 'submitted', 'approved', 'rejected', 'archived']

export default function AdminScenariosPage() {
  const { data, loading, error, refetch } = useFetch(getScenarios)
  const [busy, setBusy] = useState(null)
  const [formError, setFormError] = useState(null)
  const rows = data?.rows ?? []

  const onStatus = async (id, status) => {
    setBusy(id)
    setFormError(null)
    try {
      await patchScenario(id, status)
      await refetch()
    } catch (e) {
      setFormError(e?.message ?? 'Could not update status')
    } finally {
      setBusy(null)
    }
  }

  return (
    <div>
      <SectionHeader
        title="Scenario governance"
        subtitle="Saved what-if runs, assumptions and approval status"
      />
      <DataNote tone="simulated">
        Approval is internal governance. It does not turn a run into an official
        ministry circular — official_forecast stays false.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {formError && <ErrorBanner message={formError} />}
      {loading && <LoadingSpinner message="Loading scenarios…" height={240} />}

      {data && rows.length === 0 && (
        <EmptyState
          title="No saved scenarios"
          description="Persist a what-if from the MoE policy simulator to see it here."
        />
      )}

      {rows.length > 0 && (
        <div className="panel" style={{ marginTop: 16, overflowX: 'auto' }}>
          <table data-testid="scenario-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--text-secondary)' }}>
                <th style={th}>Name</th>
                <th style={th}>Owner</th>
                <th style={th}>Assumptions</th>
                <th style={th}>Official forecast</th>
                <th style={th}>Approval</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(row => (
                <tr key={row.id} data-testid="scenario-row">
                  <td style={td}>{row.name}</td>
                  <td style={td}>{row.owner}</td>
                  <td style={td}>{summarise(row.assumptions)}</td>
                  <td style={td}>{row.official_forecast ? 'true' : 'false'}</td>
                  <td style={td}>
                    <select
                      value={row.status}
                      disabled={busy === row.id}
                      onChange={e => onStatus(row.id, e.target.value)}
                      aria-label={`Status for ${row.name}`}
                    >
                      {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function summarise(assumptions) {
  if (!assumptions || typeof assumptions !== 'object') return '—'
  const inner = assumptions.assumptions || assumptions
  const keys = Object.keys(inner).filter(k => k !== 'official_forecast').slice(0, 4)
  return keys.map(k => `${k}=${JSON.stringify(inner[k])}`).join(', ') || '—'
}

const th = { padding: '8px 10px', borderBottom: '1px solid var(--border)', fontWeight: 600, fontSize: 11, textTransform: 'uppercase' }
const td = { padding: '10px', borderBottom: '1px solid var(--border)', verticalAlign: 'top' }
