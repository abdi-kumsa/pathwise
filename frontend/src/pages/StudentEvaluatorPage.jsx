import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ReferenceLine, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import { submitStudentProfile, getSkillRecommendations } from '../api/enrollment'

const PROGRAMS = [
  'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
  'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
  'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
  'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

const FEAT_LABEL = {
  gpa_scaled:                 'GPA',
  internships:                'Internships',
  projects:                   'Projects',
  communication_score_scaled: 'Communication',
}

const PRIORITY_STYLE = {
  High:   { bg: '#fef2f2', color: '#ef4444' },
  Medium: { bg: '#fffbeb', color: '#d97706' },
  Low:    { bg: '#f0fdf4', color: '#16a34a' },
}

const probColor = p => p >= 0.75 ? '#10b981' : p >= 0.50 ? '#f59e0b' : '#ef4444'

function SliderField({ label, value, min, max, step, unit, onChange }) {
  return (
    <div style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <label style={{ fontSize: '13px', fontWeight: '600', color: 'var(--navy)' }}>{label}</label>
        <span style={{ fontSize: '13px', fontWeight: '700', color: 'var(--blue)' }}>{value}{unit}</span>
      </div>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(Number(e.target.value))}
        style={{ width: '100%', accentColor: '#2563eb', cursor: 'pointer' }}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  )
}

export default function StudentEvaluatorPage() {
  const [form, setForm] = useState({
    gpa: 3.2, internships: 1, projects: 3, communication_score: 6, program: 'MS Data Science',
  })
  const [result,      setResult]      = useState(null)
  const [recs,        setRecs]        = useState(null)
  const [submitting,  setSubmitting]  = useState(false)
  const [error,       setError]       = useState(null)

  const handleSubmit = async () => {
    setSubmitting(true)
    setError(null)
    setRecs(null)
    try {
      const data = await submitStudentProfile(form)
      setResult(data)
      // fetch global skill recommendations in parallel (no student_id needed)
      const recData = await getSkillRecommendations()
      setRecs(recData)
    } catch (e) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Prediction failed')
    } finally {
      setSubmitting(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setRecs(null)
    setError(null)
  }

  const shapData = result
    ? result.shap_values
        .slice(0, 8)
        .map(s => ({
          feature: FEAT_LABEL[s.feature] ?? s.feature.replace('prog_', '').replace(/_/g, ' '),
          value:   parseFloat(s.shap.toFixed(3)),
        }))
    : []

  const probPct = result ? (result.placement_probability * 100).toFixed(1) : null
  const color   = result ? probColor(result.placement_probability) : '#2563eb'

  return (
    <div>
      <SectionHeader title="Student evaluator" subtitle="Predict placement outcomes based on student profile" />

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start' }}>

        {/* ── Input form ─────────────────────────────────────────────────────── */}
        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px 28px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '700', color: 'var(--navy)', marginBottom: '24px' }}>
            Student Profile
          </p>

          <SliderField
            label="GPA" value={form.gpa} min={2.0} max={4.0} step={0.1} unit=""
            onChange={v => setForm(f => ({ ...f, gpa: v }))}
          />
          <SliderField
            label="Internships" value={form.internships} min={0} max={10} step={1} unit=""
            onChange={v => setForm(f => ({ ...f, internships: v }))}
          />
          <SliderField
            label="Projects" value={form.projects} min={0} max={10} step={1} unit=""
            onChange={v => setForm(f => ({ ...f, projects: v }))}
          />
          <SliderField
            label="Communication score" value={form.communication_score} min={1} max={10} step={1} unit="/10"
            onChange={v => setForm(f => ({ ...f, communication_score: v }))}
          />

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--navy)', marginBottom: '8px' }}>
              Programme
            </label>
            <select
              value={form.program}
              onChange={e => setForm(f => ({ ...f, program: e.target.value }))}
              style={{ width: '100%', fontSize: '13px', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', color: 'var(--navy)', background: 'var(--white)', cursor: 'pointer' }}
            >
              {PROGRAMS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          {error && (
            <p style={{ fontSize: '13px', color: '#ef4444', marginBottom: '12px' }}>{error}</p>
          )}

          <button
            onClick={handleSubmit}
            disabled={submitting}
            style={{
              width: '100%', padding: '12px', borderRadius: '10px', border: 'none',
              background: submitting ? '#94a3b8' : '#2563eb', color: 'white',
              fontSize: '14px', fontWeight: '600', cursor: submitting ? 'not-allowed' : 'pointer',
              fontFamily: "'Sora', sans-serif", transition: 'background 0.2s',
            }}
          >
            {submitting ? 'Predicting…' : 'Predict Placement'}
          </button>
        </div>

        {/* ── Results ────────────────────────────────────────────────────────── */}
        <div>
          {!result ? (
            <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '48px 28px', textAlign: 'center' }}>
              <div style={{ width: '52px', height: '52px', borderRadius: '12px', background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '28px', height: '28px' }}>
                  <path d="M9 11H5a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h4"/>
                  <path d="M9 21V9a2 2 0 0 1 2-2h6l4 4v8a2 2 0 0 1-2 2h-8a2 2 0 0 1-2-2Z"/>
                </svg>
              </div>
              <p style={{ fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '6px' }}>Set profile and predict</p>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Adjust the sliders then click Predict Placement to see the XGBoost result and SHAP explanation.</p>
            </div>
          ) : (
            <>
              {/* Probability card */}
              <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px 28px', marginBottom: '16px', textAlign: 'center' }}>
                <p style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '12px' }}>
                  Placement Probability
                </p>
                <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '56px', fontWeight: '800', color, lineHeight: 1, marginBottom: '10px' }}>
                  {probPct}%
                </p>
                <span style={{
                  display: 'inline-block', padding: '4px 14px', borderRadius: '20px', fontSize: '13px', fontWeight: '700',
                  background: result.prediction === 'Placed' ? '#ecfdf5' : '#fef2f2',
                  color:      result.prediction === 'Placed' ? '#10b981'  : '#ef4444',
                }}>
                  {result.prediction}
                </span>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '10px' }}>
                  Base value: {result.base_value.toFixed(3)} (log-odds)
                </p>
              </div>

              {/* SHAP waterfall */}
              <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px', marginBottom: '16px' }}>
                <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '4px' }}>
                  SHAP Feature Contributions
                </p>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                  Blue = helps placement · Red = hurts placement · Values in log-odds
                </p>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={shapData} layout="vertical" margin={{ top: 4, right: 16, left: 90, bottom: 4 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                    <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} />
                    <YAxis type="category" dataKey="feature" tick={{ fontSize: 11, fill: '#64748b' }} width={90} />
                    <ReferenceLine x={0} stroke="#94a3b8" strokeWidth={1} />
                    <Tooltip formatter={v => [v.toFixed(4), 'SHAP value']} />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {shapData.map((entry, i) => (
                        <Cell key={i} fill={entry.value >= 0 ? '#2563eb' : '#ef4444'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>

              {/* Skill recommendations */}
              {recs && (
                <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px', marginBottom: '16px' }}>
                  <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '4px' }}>
                    Skill Recommendations
                  </p>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                    Based on SHAP feature importance — focus areas ranked by impact on placement probability.
                  </p>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px' }}>
                    {recs.recommendations.map((r, i) => {
                      const ps = PRIORITY_STYLE[r.priority] ?? PRIORITY_STYLE.Low
                      return (
                        <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '12px 14px', borderRadius: '10px', background: '#f8fafc', border: '1px solid #f1f5f9' }}>
                          <span style={{ flexShrink: 0, background: ps.bg, color: ps.color, borderRadius: '6px', padding: '2px 8px', fontSize: '11px', fontWeight: '700', marginTop: '1px' }}>
                            {r.priority}
                          </span>
                          <div>
                            <p style={{ fontSize: '13px', fontWeight: '600', color: 'var(--navy)', marginBottom: '2px' }}>{r.skill}</p>
                            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{r.reason}</p>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  {recs.alternative_pathways?.length > 0 && (
                    <>
                      <p style={{ fontSize: '12px', fontWeight: '700', color: 'var(--navy)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '10px' }}>
                        Alternative Pathways
                      </p>
                      <ul style={{ margin: 0, padding: '0 0 0 16px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {recs.alternative_pathways.map((p, i) => (
                          <li key={i} style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>{p}</li>
                        ))}
                      </ul>
                    </>
                  )}
                </div>
              )}

              <button
                onClick={handleReset}
                style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline', padding: 0 }}
              >
                Reset
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
