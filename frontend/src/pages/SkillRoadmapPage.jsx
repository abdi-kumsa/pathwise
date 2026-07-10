import { useState } from 'react'
import SectionHeader from '../components/SectionHeader'
import { getSkillRoadmap } from '../api/enrollment'

const PROGRAMS = [
  'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
  'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
  'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
  'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

const PRIORITY_COLOR = {
  High:   { bg: '#fef2f2', border: '#fecaca', text: '#dc2626' },
  Medium: { bg: '#fffbeb', border: '#fde68a', text: '#d97706' },
  Low:    { bg: '#f0fdf4', border: '#bbf7d0', text: '#16a34a' },
}

const probColor = p =>
  p >= 75 ? '#10b981' : p >= 50 ? '#f59e0b' : '#ef4444'

const gainColor = g =>
  g >= 10 ? '#10b981' : g >= 4 ? '#f59e0b' : '#94a3b8'

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

function ProbabilityRing({ value }) {
  const color = probColor(value)
  const radius = 52
  const circ = 2 * Math.PI * radius
  const fill = circ * (value / 100)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '28px 0 20px' }}>
      <svg width="136" height="136" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="68" cy="68" r={radius} fill="none" stroke="#f1f5f9" strokeWidth="10" />
        <circle
          cx="68" cy="68" r={radius} fill="none"
          stroke={color} strokeWidth="10"
          strokeDasharray={`${fill} ${circ}`}
          strokeLinecap="round"
          style={{ transition: 'stroke-dasharray 0.5s ease' }}
        />
      </svg>
      <div style={{ marginTop: '-88px', textAlign: 'center' }}>
        <div style={{ fontFamily: "'Sora', sans-serif", fontSize: '32px', fontWeight: '800', color, lineHeight: 1 }}>
          {value}%
        </div>
        <div style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', marginTop: '4px' }}>
          current probability
        </div>
      </div>
      <div style={{ marginTop: '84px', fontSize: '13px', color: 'var(--text-secondary)', textAlign: 'center', maxWidth: '200px' }}>
        Improve the skills below to increase your placement chances
      </div>
    </div>
  )
}

function RoadmapCard({ rank, item }) {
  const pc = PRIORITY_COLOR[item.priority] ?? PRIORITY_COLOR.Low
  const gc = gainColor(item.probability_gain)
  const gainPositive = item.probability_gain > 0

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '32px 1fr auto',
      gap: '14px',
      alignItems: 'start',
      padding: '16px 18px',
      borderRadius: '12px',
      background: 'var(--white)',
      border: '1px solid var(--border)',
    }}>
      {/* Rank badge */}
      <div style={{
        width: '32px', height: '32px', borderRadius: '8px', flexShrink: 0,
        background: `linear-gradient(135deg, #2563eb, #60a5fa)`,
        opacity: 1 - rank * 0.18,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontFamily: "'Sora', sans-serif", fontWeight: '700', fontSize: '14px', color: '#fff',
      }}>
        {rank + 1}
      </div>

      {/* Content */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span style={{ fontSize: '14px', fontWeight: '700', color: 'var(--navy)' }}>{item.skill}</span>
          <span style={{
            fontSize: '10px', fontWeight: '700', padding: '2px 7px', borderRadius: '20px',
            background: pc.bg, border: `1px solid ${pc.border}`, color: pc.text,
          }}>
            {item.priority}
          </span>
        </div>
        <p style={{ fontSize: '12px', fontWeight: '600', color: 'var(--blue)', marginBottom: '3px' }}>
          {item.action}
        </p>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{item.reason}</p>
      </div>

      {/* Gain */}
      <div style={{ textAlign: 'right', flexShrink: 0 }}>
        <div style={{
          fontFamily: "'IBM Plex Mono', monospace",
          fontSize: '20px', fontWeight: '700',
          color: gainPositive ? gc : '#94a3b8',
        }}>
          {gainPositive ? '+' : ''}{item.probability_gain}%
        </div>
        <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '2px' }}>prob. gain</div>
      </div>
    </div>
  )
}

export default function SkillRoadmapPage() {
  const [form, setForm] = useState({
    gpa: 2.8, internships: 0, projects: 1, communication_score: 4,
    program: 'Certificate Data Analytics',
  })
  const [result,     setResult]     = useState(null)
  const [loading,    setLoading]    = useState(false)
  const [error,      setError]      = useState(null)

  const handleGenerate = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getSkillRoadmap(form)
      setResult(data)
    } catch (e) {
      setError(e?.response?.data?.detail ?? e?.message ?? 'Request failed')
    } finally {
      setLoading(false)
    }
  }

  const topGain = result
    ? Math.max(...result.recommendations.map(r => r.probability_gain))
    : null

  return (
    <div>
      <SectionHeader
        title="Skill roadmap"
        subtitle="Personalised action plan ranked by actual probability gain from the placement model"
      />

      {/* KPI strip */}
      {result && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '28px' }}>
          {[
            { label: 'Current placement probability', value: `${result.current_probability}%`, color: probColor(result.current_probability) },
            { label: 'Max probability gain available', value: `+${topGain}%`, color: '#10b981' },
            { label: 'Programme', value: result.program.replace('MS ', 'MS '), color: 'var(--navy)' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 24px' }}>
              <p style={{ fontSize: '11px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '8px' }}>{label}</p>
              <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '22px', fontWeight: '800', color }}>{value}</p>
            </div>
          ))}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px', alignItems: 'start' }}>

        {/* ── Input form ─────────────────────────────────────────────────── */}
        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px 28px' }}>
          <p style={{ fontFamily: "'Sora', sans-serif", fontSize: '14px', fontWeight: '700', color: 'var(--navy)', marginBottom: '24px' }}>
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
            onClick={handleGenerate}
            disabled={loading}
            style={{
              width: '100%', padding: '12px', borderRadius: '10px', border: 'none',
              background: loading ? '#94a3b8' : '#2563eb', color: 'white',
              fontSize: '14px', fontWeight: '600', cursor: loading ? 'not-allowed' : 'pointer',
              fontFamily: "'Sora', sans-serif", transition: 'background 0.2s',
            }}
          >
            {loading ? 'Generating…' : 'Generate Roadmap'}
          </button>

          {result && (
            <button
              onClick={() => setResult(null)}
              style={{ width: '100%', marginTop: '8px', fontSize: '12px', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
            >
              Reset
            </button>
          )}
        </div>

        {/* ── Results ────────────────────────────────────────────────────── */}
        <div>
          {!result ? (
            <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '64px 28px', textAlign: 'center' }}>
              <div style={{ width: '52px', height: '52px', borderRadius: '12px', background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 16px' }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '28px', height: '28px' }}>
                  <path d="M12 2L2 7l10 5 10-5-10-5Z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <p style={{ fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '6px' }}>Enter a student profile</p>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '320px', margin: '0 auto' }}>
                Set the sliders to reflect the student's current standing, then click Generate Roadmap to see which skills will move the needle most.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

              {/* Probability ring */}
              <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px' }}>
                <ProbabilityRing value={result.current_probability} />
              </div>

              {/* Ranked skill cards */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {result.recommendations.map((item, i) => (
                  <RoadmapCard key={i} rank={i} item={item} />
                ))}
              </div>

              {/* Alternative pathways */}
              {result.alternative_pathways?.length > 0 && (
                <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 24px' }}>
                  <p style={{ fontSize: '11px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '14px' }}>
                    Alternative pathways for {result.program}
                  </p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {result.alternative_pathways.map((p, i) => (
                      <div key={i} style={{ display: 'flex', gap: '10px', alignItems: 'flex-start' }}>
                        <div style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#2563eb', flexShrink: 0, marginTop: '6px' }} />
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5' }}>{p}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
