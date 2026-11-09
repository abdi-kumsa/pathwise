import { useState } from 'react'
import AhpMatrixEditor from '../../components/AhpMatrixEditor'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import EmptyState from '../../components/EmptyState'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import {
  getAhpWeights,
  getExpertValidations,
  getFeatureImportance,
  getModelComparison,
  getPriorityTiers,
  postAhpWeights,
  postExpertValidation,
  clearSeededExpertValidations,
  downloadExpertValidations,
} from '../../api/admin'
import { SERIES } from '../../config/chartTheme'

const DEFAULT_MATRIX = [
  [1, 2, 4],
  [0.5, 1, 2],
  [0.25, 0.5, 1],
]

export default function AdminMethodologyPage() {
  const { data, loading, error, refetch } = useFetch(() =>
    Promise.all([
      getFeatureImportance(),
      getPriorityTiers(),
      getModelComparison(),
      getExpertValidations(),
      getAhpWeights(),
    ]).then(([importance, tiers, comparison, experts, ahp]) => ({
      importance, tiers, comparison, experts, ahp,
    }))
  )

  const [ahpError, setAhpError] = useState(null)
  const [ahpOk, setAhpOk] = useState(null)
  const [matrixText, setMatrixText] = useState(JSON.stringify(DEFAULT_MATRIX))
  const [labelsText, setLabelsText] = useState('enrolment history, labour demand, capacity')
  const [busy, setBusy] = useState(false)

  const [expertForm, setExpertForm] = useState({
    spec_id: 'M1.C1',
    expert_role: 'higher_education',
    verdict: 'accepted',
    expert_name: '',
    organisation: '',
    notes: '',
  })
  const [expertError, setExpertError] = useState(null)

  const learned = data?.importance?.learned_importance
  const collection = data?.importance?.collection_priority || []
  const unused = data?.importance?.unused_by_learner || []
  const placementRows = learned?.placement?.rows || []
  const m1Rows = learned?.model1?.rows || []
  const m2Rows = learned?.model2?.rows || []

  const submitAhp = async (e) => {
    e.preventDefault()
    setBusy(true)
    setAhpError(null)
    setAhpOk(null)
    try {
      const matrix = JSON.parse(matrixText)
      const labels = labelsText.split(',').map(s => s.trim()).filter(Boolean)
      const out = await postAhpWeights({ model: 'M1', matrix, labels })
      setAhpOk(out)
      await refetch()
    } catch (err) {
      setAhpError(err?.message || 'AHP refused')
      setAhpOk(null)
    } finally {
      setBusy(false)
    }
  }

  const submitExpert = async (e) => {
    e.preventDefault()
    setBusy(true)
    setExpertError(null)
    try {
      await postExpertValidation({ ...expertForm, notes: expertForm.notes || null })
      setExpertForm({ ...expertForm, notes: '' })
      await refetch()
    } catch (err) {
      setExpertError(err?.message || 'Could not record validation')
    } finally {
      setBusy(false)
    }
  }

  const clearSeeded = async () => {
    if (!window.confirm('Delete the demonstration rows? Recorded reviews are kept.')) return
    setBusy(true)
    try {
      await clearSeededExpertValidations()
      await refetch()
    } finally {
      setBusy(false)
    }
  }

  const coverage = data?.experts?.coverage

  return (
    <div>
      <SectionHeader
        title="Methodology"
        subtitle="Learned importance beside collection priority, plus AHP and expert sign-off"
      />
      <DataNote tone="simulated">
        Expert validations may be seeded. Collection-priority percentages are
        not model weights. AHP is a separate methodology — never blended into SHAP.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading methodology…" height={280} />}

      {data && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginTop: 16 }}>
            <section data-testid="learned_importance" className="panel" style={{ padding: 14 }}>
              <p className="panel-title">Learned importance</p>
              <p className="panel-sub">
                Ethiopia M1/M2 coefficient and permutation. Placement SHAP is a leftover US tool — not an Ethiopia OLS explanation.
              </p>
              {(m1Rows.length === 0 && m2Rows.length === 0 && placementRows.length === 0) ? (
                <EmptyState title="No learned rankings yet" description="Run explainability after training." />
              ) : (
                <>
                  {m1Rows.length > 0 && <RankList rows={m1Rows.slice(0, 8)} label="M1 |coefficient|" />}
                  {m2Rows.length > 0 && <RankList rows={m2Rows.slice(0, 8)} label="M2 |coefficient|" />}
                  {unused.length > 0 && (
                    <p data-testid="unused-features" style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 10 }}>
                      {unused.length} DOC1 columns are unused_by_learner. OLS did not learn from all 10 categories.
                    </p>
                  )}
                  {placementRows.length > 0 && (
                    <details style={{ marginTop: 12 }}>
                      <summary style={{ fontSize: 12, cursor: 'pointer', color: 'var(--text-secondary)' }}>
                        Leftover US placement SHAP
                      </summary>
                      <RankList rows={placementRows.slice(0, 8)} label="Placement SHAP" />
                    </details>
                  )}
                </>
              )}
            </section>

            <section data-testid="collection_priority" className="panel" style={{ padding: 14 }}>
              <p className="panel-title">Collection priority</p>
              <p className="panel-sub">DOC1 data-collection percentages — not used as model weights</p>
              <ul style={{ listStyle: 'none', display: 'grid', gap: 6, marginTop: 8 }}>
                {collection.map(row => (
                  <li key={row.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5 }}>
                    <span>{row.id} {row.name}</span>
                    <span style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{row.collection_priority}%</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>

          <div className="panel" style={{ marginTop: 16, padding: 14 }} data-testid="ahp-panel">
            <p className="panel-title">AHP (beside SHAP, never blended)</p>
            <p className="panel-sub">Pairwise matrix → principal-eigenvector weights. CR &gt; 0.1 is refused.</p>
            <form onSubmit={submitAhp} style={{ display: 'grid', gap: 8, marginTop: 10 }}>
              <label style={lab}>Labels (comma separated)
                <input value={labelsText} onChange={e => setLabelsText(e.target.value)} />
              </label>
              <AhpMatrixEditor
                labels={labelsText.split(',').map(x => x.trim()).filter(Boolean)}
                matrix={(() => { try { return JSON.parse(matrixText) } catch { return null } })()}
                onChange={m => setMatrixText(JSON.stringify(m))}
              />
              <details>
                <summary style={{ fontSize: 12, cursor: 'pointer' }}>Edit as JSON</summary>
                <label style={lab}>Pairwise matrix (JSON)
                  <textarea rows={4} value={matrixText} onChange={e => setMatrixText(e.target.value)} />
                </label>
              </details>
              <button type="submit" disabled={busy}>Compute weights</button>
            </form>
            {ahpError && (
              <p data-testid="ahp-refused" style={{ color: 'var(--red)', fontSize: 13, marginTop: 10 }}>
                {ahpError}
              </p>
            )}
            {(ahpOk || data.ahp?.weights) && !ahpError && (
              <div data-testid="ahp-weights" style={{ marginTop: 10, fontSize: 13 }}>
                CR {(ahpOk || data.ahp).consistency_ratio}
                <ul>
                  {Object.entries((ahpOk || data.ahp).weights || {}).map(([k, v]) => (
                    <li key={k}>{k}: {Number(v).toFixed(3)}</li>
                  ))}
                </ul>
              </div>
            )}
            {!(ahpOk || data.ahp?.weights) && !ahpError && (
              <p data-testid="ahp-empty" style={{ fontSize: 12.5, color: 'var(--text-secondary)', marginTop: 8 }}>
                No usable AHP weights stored.
              </p>
            )}
          </div>

          <div className="panel" style={{ marginTop: 16, padding: 14 }}>
            <p className="panel-title">Priority tiers</p>
            <TierTable model="M1" tiers={data.tiers?.model1} />
            <TierTable model="M2" tiers={data.tiers?.model2} />
          </div>

          <div className="panel" style={{ marginTop: 16, padding: 14 }}>
            <p className="panel-title">Model comparison</p>
            <p className="panel-sub">{data.comparison?.validation}</p>
            {(data.comparison?.targets || []).map(t => (
              <div key={t.id} style={{ marginTop: 8 }}>
                <p style={{ fontSize: 13, fontWeight: 600 }}>{t.id} — {t.target}</p>
                <p style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  Candidates: {(t.candidates || Object.keys(t.estimators || {})).join(', ')}
                </p>
              </div>
            ))}
            {(data.comparison?.us_models_not_compared || []).length > 0 && (
              <p style={{ fontSize: 12, marginTop: 8, color: 'var(--text-secondary)' }}>
                Not compared: {(data.comparison.us_models_not_compared).join('; ')}
              </p>
            )}
          </div>

          <div className="panel" style={{ marginTop: 16, padding: 14 }}>
            <p className="panel-title">Expert validations</p>
            <p className="panel-sub">
              PROC.S2: record each expert&apos;s judgement on a DOC1 category or variable, with their name
              and organisation. Only recorded reviews count; demonstration rows never do.
            </p>
            {coverage && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 16, fontSize: 12.5, margin: '8px 0' }}>
                <span><strong>{coverage.recorded_reviews}</strong> recorded review(s)</span>
                <span><strong>{coverage.domains_with_a_review}</strong> / {coverage.domains_total} expert domains reviewed</span>
                <span><strong>{coverage.categories_accepted}</strong> / {coverage.categories_total} categories accepted</span>
                <span style={{ color: coverage.complete ? 'var(--green)' : '#B45309' }}>
                  {coverage.complete ? 'Validation complete' : 'Validation incomplete'}
                </span>
                <button type="button" onClick={downloadExpertValidations}>Export CSV</button>
                {coverage.seeded_rows > 0 && (
                  <button type="button" onClick={clearSeeded} disabled={busy}>
                    Clear {coverage.seeded_rows} demonstration row(s)
                  </button>
                )}
              </div>
            )}
            {expertError && <p style={{ color: 'var(--red)', fontSize: 12.5 }}>{expertError}</p>}
            <form onSubmit={submitExpert} style={{ display: 'grid', gap: 8, gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', margin: '10px 0' }}>
              <label style={lab}>Spec id
                <input value={expertForm.spec_id} onChange={e => setExpertForm({ ...expertForm, spec_id: e.target.value })} />
              </label>
              <label style={lab}>Domain
                <select value={expertForm.expert_role} onChange={e => setExpertForm({ ...expertForm, expert_role: e.target.value })}>
                  {(data.experts?.expert_domains || []).map(d => <option key={d} value={d}>{d}</option>)}
                </select>
              </label>
              <label style={lab}>Expert name
                <input value={expertForm.expert_name} required minLength={2}
                       onChange={e => setExpertForm({ ...expertForm, expert_name: e.target.value })} />
              </label>
              <label style={lab}>Organisation
                <input value={expertForm.organisation} required minLength={2}
                       onChange={e => setExpertForm({ ...expertForm, organisation: e.target.value })} />
              </label>
              <label style={lab}>Verdict
                <select value={expertForm.verdict} onChange={e => setExpertForm({ ...expertForm, verdict: e.target.value })}>
                  <option value="accepted">accepted</option>
                  <option value="revision">revision</option>
                  <option value="rejected">rejected</option>
                </select>
              </label>
              <label style={{ ...lab, gridColumn: '1 / -1' }}>Notes
                <textarea
                  rows={2}
                  value={expertForm.notes}
                  onChange={e => setExpertForm({ ...expertForm, notes: e.target.value })}
                />
              </label>
              <div style={{ display: 'flex', alignItems: 'end' }}>
                <button type="submit" disabled={busy}>Record</button>
              </div>
            </form>
            <ul style={{ listStyle: 'none', display: 'grid', gap: 6 }}>
              {(data.experts?.rows || []).map(row => (
                <li key={row.id} style={{ fontSize: 12.5 }}>
                  <strong>{row.spec_id}</strong> · {row.expert_role} · {row.verdict}
                  {row.source === 'seeded'
                    ? ' · demonstration row (not a validation)'
                    : ` · ${row.expert_name}, ${row.organisation}`}
                  {row.notes ? ` — ${row.notes}` : ''}
                </li>
              ))}
            </ul>
          </div>
        </>
      )}
    </div>
  )
}

function RankList({ rows, label }) {
  return (
    <div style={{ marginTop: 10 }}>
      <p style={{ fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{label}</p>
      <ul style={{ listStyle: 'none', marginTop: 4 }}>
        {rows.map((row, i) => (
          <li key={row.feature} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12.5, gap: 8 }}>
            <span>{i + 1}. {row.feature}</span>
            <span style={{ color: SERIES[0], fontFamily: 'IBM Plex Mono, monospace' }}>
              {Number(row.importance).toFixed(4)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function TierTable({ model, tiers }) {
  if (!tiers) return null
  return (
    <div style={{ marginTop: 8 }}>
      <p style={{ fontSize: 13, fontWeight: 600 }}>{model}</p>
      <ul style={{ listStyle: 'none' }}>
        {tiers.map(t => (
          <li key={t.id} style={{ fontSize: 12.5, marginTop: 4 }}>
            {t.id} · {t.combined_priority}% · {(t.groups || []).join(', ')}
          </li>
        ))}
      </ul>
    </div>
  )
}

const lab = { fontSize: 11, fontWeight: 600, color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4 }
