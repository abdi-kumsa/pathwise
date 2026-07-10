import { useState } from 'react'
import SectionHeader from '../components/SectionHeader'
import { getEscapeRoutes } from '../api/salary'

const PROGRAMS = [
  'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
  'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
  'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
  'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

const fmt    = n => '$' + Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 })
const pctCol = p => p >= 0.75 ? '#10b981' : p >= 0.50 ? '#f59e0b' : '#ef4444'
const rankBg  = i => ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe'][i] ?? '#bfdbfe'

function SliderField({ label, value, min, max, step, unit, onChange }) {
  return (
    <div style={{ marginBottom: '18px' }}>
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

function RouteCard({ route, rank }) {
  const col = pctCol(route.placement_probability)
  return (
    <div style={{
      background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px',
      padding: '20px 22px', display: 'flex', gap: '18px', alignItems: 'flex-start',
    }}>
      <div style={{
        flexShrink: 0, width: '34px', height: '34px', borderRadius: '9px',
        background: rankBg(rank), color: 'white',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: "'Sora', sans-serif", fontWeight: '700', fontSize: '14px',
      }}>
        {rank + 1}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '700', color: 'var(--navy)', marginBottom: '10px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {route.program}
        </p>

        <div style={{ display: 'flex', gap: '20px', marginBottom: '10px', flexWrap: 'wrap' }}>
          <div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px' }}>Placement probability</p>
            <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: '20px', fontWeight: '700', color: col }}>
              {(route.placement_probability * 100).toFixed(1)}%
            </p>
          </div>
          <div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px' }}>Avg salary</p>
            <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: '20px', fontWeight: '700', color: 'var(--navy)' }}>
              {route.avg_salary > 0 ? fmt(route.avg_salary) : '—'}
            </p>
          </div>
          <div>
            <p style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '2px' }}>Placement rate</p>
            <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: '20px', fontWeight: '700', color: 'var(--navy)' }}>
              {route.placement_rate}%
            </p>
          </div>
        </div>

        {route.rationale && (
          <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.5', background: '#f8fafc', borderRadius: '8px', padding: '8px 12px' }}>
            {route.rationale}
          </p>
        )}
      </div>
    </div>
  )
}

export default function EscapeRoutePage() {
  const [form, setForm] = useState({
    gpa: 2.5, internships: 0, projects: 1, communication_score: 4,
    program: 'Certificate Data Analytics',
  })
  const [result,     setResult]     = useState(null)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState(null)

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getEscapeRoutes(form, 5)
      setResult(data)
    } catch (e) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const currentProb = result?.current_probability ?? null
  const currentCol  = currentProb !== null ? pctCol(currentProb) : '#64748b'

  return (
    <div>
      <SectionHeader
        title="Escape route mapping"
        subtitle="Find programmes where this student profile would achieve a better placement outcome"
      />

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '24px', alignItems: 'start' }}>

        {/* ── Profile form ─────────────────────────────────────────────────── */}
        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px 26px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '700', color: 'var(--navy)', marginBottom: '20px' }}>
            Student Profile
          </p>

          <SliderField label="GPA" value={form.gpa} min={2.0} max={4.0} step={0.1} unit=""
            onChange={v => setForm(f => ({ ...f, gpa: v }))} />
          <SliderField label="Internships" value={form.internships} min={0} max={10} step={1} unit=""
            onChange={v => setForm(f => ({ ...f, internships: v }))} />
          <SliderField label="Projects" value={form.projects} min={0} max={10} step={1} unit=""
            onChange={v => setForm(f => ({ ...f, projects: v }))} />
          <SliderField label="Communication score" value={form.communication_score} min={1} max={10} step={1} unit="/10"
            onChange={v => setForm(f => ({ ...f, communication_score: v }))} />

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: '600', color: 'var(--navy)', marginBottom: '8px' }}>
              Current programme
            </label>
            <select
              value={form.program}
              onChange={e => setForm(f => ({ ...f, program: e.target.value }))}
              style={{ width: '100%', fontSize: '13px', padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--border)', color: 'var(--navy)', background: 'var(--white)', cursor: 'pointer' }}
            >
              {PROGRAMS.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>

          {error && <p style={{ fontSize: '13px', color: '#ef4444', marginBottom: '12px' }}>{error}</p>}

          <button
            onClick={handleRun}
            disabled={loading}
            style={{
              width: '100%', padding: '12px', borderRadius: '10px', border: 'none',
              background: loading ? '#94a3b8' : '#2563eb', color: 'white',
              fontSize: '14px', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: "'Sora', sans-serif", transition: 'background 0.2s',
            }}
          >
            {loading ? 'Mapping routes…' : 'Find escape routes'}
          </button>
        </div>

        {/* ── Results ──────────────────────────────────────────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {!result ? (
            <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '60px 28px', textAlign: 'center' }}>
              <div style={{ width: '52px', height: '52px', borderRadius: '12px', background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '28px', height: '28px' }}>
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </div>
              <p style={{ fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '6px' }}>Set a profile and find routes</p>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '300px', margin: '0 auto' }}>
                The model will simulate this student across all 12 programmes and rank the best alternatives.
              </p>
            </div>
          ) : (
            <>
              {/* Current programme card */}
              <div style={{
                background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px',
                padding: '18px 22px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <div>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '2px' }}>Current programme</p>
                  <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '15px', fontWeight: '700', color: 'var(--navy)' }}>
                    {result.current_program}
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '2px' }}>Placement probability</p>
                  <p style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: '24px', fontWeight: '700', color: currentCol }}>
                    {(result.current_probability * 100).toFixed(1)}%
                  </p>
                </div>
              </div>

              <p style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', paddingLeft: '4px' }}>
                Top {result.routes.length} alternative programmes
              </p>

              {result.routes.map((route, i) => (
                <RouteCard key={route.program} route={route} rank={i} />
              ))}

              <button
                onClick={() => setResult(null)}
                style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline', padding: '4px 0', textAlign: 'left' }}
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
