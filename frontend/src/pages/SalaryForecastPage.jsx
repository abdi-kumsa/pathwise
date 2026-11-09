import { useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import SectionHeader from '../components/SectionHeader'
import KPICard from '../components/KPICard'
import ErrorBanner from '../components/ErrorBanner'
import LoadingSpinner from '../components/LoadingSpinner'
import DataNote from '../components/DataNote'
import useFetch from '../hooks/useFetch'
import { getSalaryForecast, predictSalary } from '../api/salary'

const PROGRAMS = [
  'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
  'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
  'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
  'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

const SHORT = n =>
  n.replace('MS ', '').replace('BS ', '').replace('MBA ', '').replace('Certificate ', '')

const fmt = n => '$' + Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 })
const fmtK = n => '$' + (n / 1000).toFixed(0) + 'K'

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

export default function SalaryForecastPage() {
  const { data, loading, error, refetch } = useFetch(() => getSalaryForecast())

  const programs = data?.programs ?? []
  const overallAvg = data?.overall_avg_salary ?? 0
  const topProgram = data?.top_program ?? '—'

  const bestValue = [...programs].sort(
    (a, b) => (b.avg_salary * b.placement_rate / 100) - (a.avg_salary * a.placement_rate / 100)
  )[0]?.program ?? '—'

  const chartData = programs.map(p => ({
    name:    SHORT(p.program),
    Avg:     Math.round(p.avg_salary / 1000),
    Median:  Math.round(p.median_salary / 1000),
    Rate:    p.placement_rate,
  }))

  // ── Individual predictor ──────────────────────────────────────────────────
  const [form, setForm] = useState({
    gpa: 3.2, internships: 1, projects: 3, communication_score: 6,
    program: 'MS Data Science',
  })
  const [prediction, setPrediction] = useState(null)
  const [predLoading, setPredLoading] = useState(false)
  const [predError, setPredError] = useState(null)

  const handlePredict = async () => {
    setPredLoading(true)
    setPredError(null)
    try {
      const result = await predictSalary(form)
      setPrediction(result)
    } catch (e) {
      setPredError(e?.response?.data?.detail ?? e?.message ?? 'Prediction failed')
    } finally {
      setPredLoading(false)
    }
  }

  const vsAvg = prediction && prediction.program_avg_salary > 0
    ? prediction.predicted_salary - prediction.program_avg_salary
    : null

  return (
    <div>
      <SectionHeader
        title="Salary forecast"
        subtitle="Early-career salary predictions by programme — XGBoost regression model"
        showLiveIndicator
      />
      <DataNote tone="caution">
        This page is the leftover US placement / salary / LSTM path. It is not
        an Ethiopia Model 1 or Model 2 score.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={refetch} />}

      {/* ── KPI strip ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <KPICard
          label="Top earning programme"
          value={loading ? '—' : SHORT(topProgram)}
          delta={loading ? '' : fmt(programs[0]?.avg_salary) + ' avg'}
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
        />
        <KPICard
          label="Platform avg salary"
          value={loading ? '—' : fmtK(overallAvg)}
          delta="All placed graduates"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="12" width="4" height="8" rx="1"/><rect x="10" y="8" width="4" height="12" rx="1"/><rect x="17" y="4" width="4" height="16" rx="1"/></svg>}
        />
        <KPICard
          label="Best salary + placement"
          value={loading ? '—' : SHORT(bestValue)}
          delta="Highest combined score"
          deltaDirection="up"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
        />
        <KPICard
          label="Programmes tracked"
          value={loading ? '—' : programs.length}
          delta="All 12 programmes"
          deltaDirection="neutral"
          icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/></svg>}
        />
      </div>

      {/* ── Charts ─────────────────────────────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
            Avg Salary by Programme ($K)
          </p>
          {loading ? <LoadingSpinner message="Loading salary data…" height={300} /> : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 20, left: 108, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} unit="K" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} width={108} />
                <Tooltip formatter={v => ['$' + v + 'K', 'Avg Salary']} />
                <Bar isAnimationActive={false} dataKey="Avg" fill="#2563eb" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '20px 22px 24px' }}>
          <p style={{ fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '16px' }}>
            Median Salary by Programme ($K)
          </p>
          {loading ? <LoadingSpinner message="Loading salary data…" height={300} /> : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 20, left: 108, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                <XAxis type="number" tick={{ fontSize: 11, fill: '#64748b' }} unit="K" />
                <YAxis type="category" dataKey="name" tick={{ fontSize: 10, fill: '#64748b' }} width={108} />
                <Tooltip formatter={v => ['$' + v + 'K', 'Median Salary']} />
                <Bar isAnimationActive={false} dataKey="Median" fill="#0ea5e9" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* ── Individual predictor ───────────────────────────────────────────── */}
      <div style={{ background: 'var(--white)', border: '1px solid var(--border)', borderRadius: '14px', padding: '24px 28px' }}>
        <p style={{ fontSize: '15px', fontWeight: '700', color: 'var(--navy)', marginBottom: '4px' }}>
          Individual salary predictor
        </p>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '24px' }}>
          Adjust the profile to see a personalised early-career salary estimate with 80% confidence range.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '32px', alignItems: 'start' }}>
          <div>
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

            {predError && <p style={{ fontSize: '13px', color: '#ef4444', marginBottom: '12px' }}>{predError}</p>}

            <button
              onClick={handlePredict}
              disabled={predLoading}
              style={{
                width: '100%', padding: '12px', borderRadius: '10px', border: 'none',
                background: predLoading ? '#94a3b8' : '#2563eb', color: 'white',
                fontSize: '14px', fontWeight: '600', cursor: predLoading ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s',
              }}
            >
              {predLoading ? 'Predicting…' : 'Predict Salary'}
            </button>
          </div>

          <div>
            {!prediction ? (
              <div style={{ background: '#f8fafc', borderRadius: '14px', padding: '48px 28px', textAlign: 'center', border: '1px dashed var(--border)' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: '12px', background: '#eff6ff', color: '#2563eb', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 14px' }}>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: '26px', height: '26px' }}>
                    <path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                  </svg>
                </div>
                <p style={{ fontSize: '14px', fontWeight: '600', color: 'var(--navy)', marginBottom: '6px' }}>Set a profile and predict</p>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Adjust the sliders then click Predict Salary to see the XGBoost estimate.</p>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                {/* Main prediction */}
                <div style={{ background: '#eff6ff', borderRadius: '14px', padding: '28px', textAlign: 'center', border: '1px solid #dbeafe' }}>
                  <p style={{ fontSize: '12px', fontWeight: '600', color: '#6b7280', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '10px' }}>
                    Predicted Salary
                  </p>
                  <p style={{ fontSize: '48px', fontWeight: '700', color: '#1d4ed8', lineHeight: 1, marginBottom: '8px' }}>
                    {fmt(prediction.predicted_salary)}
                  </p>
                  <p style={{ fontSize: '13px', color: '#6b7280' }}>
                    80% confidence range: {fmt(prediction.confidence_low)} – {fmt(prediction.confidence_high)}
                  </p>
                </div>

                {/* Comparison to programme avg */}
                {prediction.program_avg_salary > 0 && (
                  <div style={{ background: 'var(--white)', borderRadius: '12px', padding: '18px 20px', border: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '2px' }}>
                        {form.program} avg salary
                      </p>
                      <p style={{ fontSize: '20px', fontWeight: '600', color: 'var(--navy)' }}>
                        {fmt(prediction.program_avg_salary)}
                      </p>
                    </div>
                    {vsAvg !== null && (
                      <span style={{
                        padding: '6px 14px', borderRadius: '20px', fontSize: '13px', fontWeight: '700',
                        background: vsAvg >= 0 ? '#ecfdf5' : '#fef2f2',
                        color:      vsAvg >= 0 ? '#10b981'  : '#ef4444',
                      }}>
                        {vsAvg >= 0 ? '+' : ''}{fmt(vsAvg)} vs avg
                      </span>
                    )}
                  </div>
                )}

                <button
                  onClick={() => setPrediction(null)}
                  style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline', padding: 0, textAlign: 'left' }}
                >
                  Reset
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
