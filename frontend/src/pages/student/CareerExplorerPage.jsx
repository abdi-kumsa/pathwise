import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, Cell,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import { searchJobs, recommendPrograms } from '../../api/roles'
import {
  SERIES, axisProps, gridProps, tooltipProps, RADIUS_V, RADIUS_H,
  fmtCompact, fmtMoney, fmtPct, fmtDelta, deltaDirection, shortMetro, fmtNum,
} from '../../config/chartTheme'

/**
 * The feature Dr. Endris asked for by name: pick a job you want, get told which
 * department to join for it.
 *
 * The profile inputs are optional. Leave them and the ranking uses each
 * programme's historical placement rate; fill all four and it re-runs the
 * XGBoost model on you specifically. Partial input is treated as none — the
 * API will not invent a default for a question you did not answer.
 */

const SCORE_COLOR = (score) => (score >= 55 ? SERIES[2] : score >= 45 ? SERIES[0] : SERIES[3])

function JobSearch({ value, onPick }) {
  const [query, setQuery] = useState('')
  const [options, setOptions] = useState([])
  const [open, setOpen] = useState(false)
  const [cursor, setCursor] = useState(0)
  const boxRef = useRef(null)

  useEffect(() => {
    const q = query.trim()
    if (!q) { setOptions([]); return }
    let cancelled = false
    const timer = setTimeout(async () => {
      try {
        const data = await searchJobs(q, 8)
        if (!cancelled) { setOptions(data); setCursor(0) }
      } catch { if (!cancelled) setOptions([]) }
    }, 160)
    return () => { cancelled = true; clearTimeout(timer) }
  }, [query])

  useEffect(() => {
    const onClickAway = (e) => {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickAway)
    return () => document.removeEventListener('mousedown', onClickAway)
  }, [])

  const pick = (opt) => {
    setQuery('')
    setOpen(false)
    onPick(opt.job_title)
  }

  return (
    <div ref={boxRef} style={{ position: 'relative' }}>
      <label className="ce-label" htmlFor="job-search">Target job</label>
      <input
        id="job-search"
        className="ce-input"
        placeholder={value || 'e.g. Data Scientist'}
        value={query}
        onChange={e => { setQuery(e.target.value); setOpen(true) }}
        onFocus={() => setOpen(true)}
        onKeyDown={e => {
          if (e.key === 'ArrowDown') { e.preventDefault(); setCursor(c => Math.min(c + 1, options.length - 1)) }
          else if (e.key === 'ArrowUp') { e.preventDefault(); setCursor(c => Math.max(c - 1, 0)) }
          else if (e.key === 'Enter' && options[cursor]) { e.preventDefault(); pick(options[cursor]) }
        }}
        autoComplete="off"
      />
      {open && options.length > 0 && (
        <ul className="ce-options" role="listbox">
          {options.map((o, i) => (
            <li key={o.job_title}>
              <button
                type="button"
                className={`ce-option${i === cursor ? ' active' : ''}`}
                onMouseEnter={() => setCursor(i)}
                onClick={() => pick(o)}
              >
                <span>{o.job_title}</span>
                <span className="ce-option-family">{o.job_family}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function NumberField({ label, value, onChange, min, max, step = 1, suffix = '' }) {
  return (
    <div>
      <label className="ce-label">{label}</label>
      <input
        className="ce-input"
        type="number"
        min={min} max={max} step={step}
        value={value ?? ''}
        placeholder="optional"
        onChange={e => onChange(e.target.value === '' ? null : Number(e.target.value))}
      />
      {suffix && <span className="ce-hint">{suffix}</span>}
    </div>
  )
}

export default function CareerExplorerPage() {
  const [params, setParams] = useSearchParams()
  const jobFromUrl = params.get('job')

  const [job, setJob] = useState(jobFromUrl || 'Data Scientist')
  const [profile, setProfile] = useState({
    gpa: null, internships: null, projects: null, communication_score: null,
  })
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const run = async (targetJob = job, prof = profile) => {
    setLoading(true)
    setError(null)
    try {
      const complete = Object.values(prof).every(v => v !== null && v !== '')
      const data = await recommendPrograms(targetJob, complete ? prof : null, 12)
      setResult(data)
    } catch (e) {
      setError(e?.message ?? 'Could not build recommendations')
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  // Initial load, and whenever the job changes (including via the command bar,
  // which navigates here with ?job=...).
  useEffect(() => {
    run(job, profile)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job])

  useEffect(() => {
    if (jobFromUrl && jobFromUrl !== job) setJob(jobFromUrl)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobFromUrl])

  const pickJob = (title) => {
    setJob(title)
    setParams({ job: title }, { replace: true })
  }

  const demand = result?.demand
  const top = result?.recommendations ?? []
  const profileComplete = Object.values(profile).every(v => v !== null && v !== '')

  return (
    <div>
      <SectionHeader
        title="Career explorer"
        subtitle="Choose the job you want. See which department gets you there, and why."
      />
      <DataNote tone="simulated">
        Simulated structure, not official MoE or MoLS statistics. Placement odds
        still use the leftover US XGBoost path when a full profile is filled in.
      </DataNote>

      {error && <ErrorBanner message={error} onRetry={() => run()} />}

      {/* ── Controls ───────────────────────────────────────────────────────── */}
      <div className="panel" style={{ marginBottom: 20 }}>
        <div className="ce-controls">
          <JobSearch value={job} onPick={pickJob} />
          <NumberField label="GPA" value={profile.gpa} min={0} max={4} step={0.1}
                       onChange={v => setProfile(p => ({ ...p, gpa: v }))} />
          <NumberField label="Internships" value={profile.internships} min={0} max={20}
                       onChange={v => setProfile(p => ({ ...p, internships: v }))} />
          <NumberField label="Projects" value={profile.projects} min={0} max={50}
                       onChange={v => setProfile(p => ({ ...p, projects: v }))} />
          <NumberField label="Communication" value={profile.communication_score} min={1} max={10}
                       suffix="1–10"
                       onChange={v => setProfile(p => ({ ...p, communication_score: v }))} />
          <button className="ce-submit" onClick={() => run()} disabled={loading}>
            {loading ? 'Working…' : 'Update'}
          </button>
        </div>

        <p className="ce-note">
          {profileComplete
            ? 'Your profile is complete — placement odds are predicted for you specifically.'
            : 'Leave the profile blank for general guidance. Fill all four to get odds predicted for you.'}
        </p>
      </div>

      {loading && !result && <LoadingSpinner message="Matching departments…" height={280} />}

      {result && (
        <>
          {/* ── Demand for the target job ────────────────────────────────── */}
          <div className="kpi-grid">
            <KPICard
              label="Openings (2016–2025)"
              value={fmtNum(demand.total_openings)}
              delta={fmtDelta(demand.openings_cagr_pct) + ' / yr'}
              deltaDirection={deltaDirection(demand.openings_cagr_pct)}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18.7 8 13 13.7l-3-3L4 16.5"/></svg>}
            />
            <KPICard
              label="Average salary"
              value={fmtMoney(demand.avg_salary)}
              delta={result.job_family}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 1v22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>}
            />
            <KPICard
              label="Time to fill"
              value={`${demand.time_to_fill_days} days`}
              delta={`${demand.remote_share_pct}% remote`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>}
            />
            <KPICard
              label="Market outlook"
              value={demand.supply_demand_ratio < 1 ? 'Undersupplied' : 'Competitive'}
              delta={`ratio ${demand.supply_demand_ratio}`}
              deltaDirection={demand.supply_demand_ratio < 1 ? 'up' : 'down'}
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 3v18M7 7l-4 7h8ZM17 7l-4 7h8Z"/></svg>}
            />
          </div>

          <div className="card-grid-2" style={{ marginBottom: 20 }}>
            {/* Openings over time — single series, so no legend needed */}
            <div className="panel">
              <p className="panel-title">Openings for {result.job_title}</p>
              <p className="panel-sub">{demand.outlook}</p>
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={demand.series} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="ceDemand" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={SERIES[0]} stopOpacity={0.28} />
                      <stop offset="100%" stopColor={SERIES[0]} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="year" {...axisProps} />
                  <YAxis {...axisProps} tickFormatter={fmtCompact} width={46} />
                  <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), 'Openings']} />
                  <Area isAnimationActive={false} type="monotone" dataKey="openings" stroke={SERIES[0]} strokeWidth={2}
                        fill="url(#ceDemand)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Where the jobs are */}
            <div className="panel">
              <p className="panel-title">Where these jobs are</p>
              <p className="panel-sub">Top metro areas by openings</p>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={demand.top_metros} layout="vertical"
                          margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
                  <CartesianGrid {...gridProps} horizontal={false} vertical />
                  <XAxis type="number" {...axisProps} tickFormatter={fmtCompact} />
                  <YAxis type="category" dataKey="metro" {...axisProps} width={104}
                         tickFormatter={shortMetro}
                         tick={{ fontSize: 10.5, fill: '#64748B' }} />
                  <Tooltip {...tooltipProps} formatter={v => [fmtNum(v), 'Openings']} />
                  <Bar isAnimationActive={false} dataKey="openings" fill={SERIES[0]} radius={RADIUS_H} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* ── The recommendation ───────────────────────────────────────── */}
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Recommended departments</p>
            <p className="panel-sub">
              Ranked for <strong>{result.job_title}</strong>.{' '}
              {result.personalised
                ? 'Placement odds predicted for your profile.'
                : 'Placement odds are each programme’s historical rate.'}
            </p>

            <div className="ce-cards">
              {top.slice(0, 6).map(r => (
                <article key={r.program} className="ce-card">
                  <header className="ce-card-head">
                    <span className="ce-rank">#{r.rank}</span>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <p className="ce-prog">{r.program}</p>
                      <p className="ce-field">
                        {r.field}
                        {r.is_direct_route && <span className="ce-badge">Direct route</span>}
                      </p>
                    </div>
                    <div className="ce-score" style={{ color: SCORE_COLOR(r.score) }}>
                      {r.score.toFixed(0)}
                      <span className="ce-score-unit">/100</span>
                    </div>
                  </header>

                  <p className="ce-why">{r.why}</p>

                  <dl className="ce-stats">
                    <div><dt>Placement odds</dt><dd>{fmtPct(r.placement_probability * 100, 0)}</dd></div>
                    <div><dt>Employed 6mo</dt><dd>{fmtPct(r.employment_rate_pct, 0)}</dd></div>
                    <div><dt>Median salary</dt><dd>{fmtMoney(r.median_salary)}</dd></div>
                    <div><dt>Acceptance</dt><dd>{fmtPct(r.acceptance_rate_pct, 0)}</dd></div>
                    <div><dt>Net price</dt><dd>{fmtMoney(r.net_price)}</dd></div>
                    <div><dt>10-yr ROI</dt><dd>{fmtMoney(r.roi_10yr)}</dd></div>
                  </dl>
                </article>
              ))}
            </div>
          </div>

          {/* ── Why: the factor breakdown for the top pick ───────────────── */}
          {top[0] && (
            <div className="panel">
              <p className="panel-title">Why {top[0].program} ranks first</p>
              <p className="panel-sub">
                Each factor is scaled across all twelve programmes, then weighted.
                Bars show how many of the {top[0].score.toFixed(0)} points each factor contributed.
              </p>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart
                  data={top[0].factors.map(f => ({
                    factor: f.factor.replace(/_/g, ' '),
                    contribution: f.contribution,
                    weight: f.weight,
                  }))}
                  margin={{ top: 4, right: 16, left: 0, bottom: 0 }}
                >
                  <CartesianGrid {...gridProps} />
                  <XAxis dataKey="factor" {...axisProps} tick={{ fontSize: 10.5, fill: '#64748B' }} />
                  <YAxis {...axisProps} width={36} />
                  <Tooltip
                    {...tooltipProps}
                    formatter={(v, _n, p) => [
                      `${v} pts (weight ${(p.payload.weight * 100).toFixed(0)}%)`,
                      'Contribution',
                    ]}
                  />
                  <Bar isAnimationActive={false} dataKey="contribution" radius={RADIUS_V} barSize={44}>
                    {top[0].factors.map((_, i) => (
                      <Cell key={i} fill={SERIES[0]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <p className="ce-method">{result.method}</p>
            </div>
          )}
        </>
      )}

      <style>{`
        .ce-controls {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr 1fr 1fr auto;
          gap: 12px;
          align-items: end;
        }
        .ce-label {
          display: block; font-size: 12px; font-weight: 600;
          color: var(--navy); margin-bottom: 6px;
        }
        .ce-input {
          width: 100%; font-size: 13.5px; padding: 9px 11px;
          border: 1px solid var(--border); border-radius: 9px;
          color: var(--navy); background: var(--white); font-family: inherit;
        }
        .ce-input:focus {
          outline: none; border-color: var(--blue);
          box-shadow: 0 0 0 3px var(--blue-light);
        }
        .ce-hint { font-size: 11px; color: var(--text-muted); }
        .ce-submit {
          padding: 10px 20px; border-radius: 9px; border: none;
          background: var(--blue); color: #fff; font-size: 13.5px;
          font-weight: 600; cursor: pointer;
          height: 38px;
        }
        .ce-submit:disabled { background: #94A3B8; cursor: not-allowed; }
        .ce-note { font-size: 12px; color: var(--text-muted); margin-top: 12px; }

        .ce-options {
          position: absolute; top: 100%; left: 0; right: 0; z-index: 20;
          margin-top: 4px; background: var(--white); list-style: none;
          border: 1px solid var(--border); border-radius: 10px;
          box-shadow: var(--shadow-pop); overflow: hidden; max-height: 260px; overflow-y: auto;
        }
        .ce-option {
          width: 100%; display: flex; justify-content: space-between; gap: 10px;
          padding: 9px 12px; border: none; background: none; cursor: pointer;
          font-family: inherit; font-size: 13px; color: var(--navy); text-align: left;
        }
        .ce-option.active { background: var(--blue-light); }
        .ce-option-family { color: var(--text-muted); font-size: 11.5px; white-space: nowrap; }

        .ce-cards {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
          gap: 14px; margin-top: 16px;
        }
        .ce-card {
          border: 1px solid var(--border); border-radius: 12px;
          padding: 15px 16px; background: #FCFDFE;
        }
        .ce-card-head { display: flex; align-items: flex-start; gap: 10px; }
        .ce-rank {
          font-size: 12px; font-weight: 600;
          color: var(--text-muted); background: var(--white);
          border: 1px solid var(--border); border-radius: 6px; padding: 2px 7px;
          flex-shrink: 0;
        }
        .ce-prog { font-size: 14px; font-weight: 600; color: var(--navy); }
        .ce-field {
          font-size: 11.5px; color: var(--text-muted);
          display: flex; align-items: center; gap: 7px; margin-top: 2px; flex-wrap: wrap;
        }
        .ce-badge {
          background: var(--green-bg); color: var(--green);
          border-radius: 5px; padding: 1px 6px; font-size: 10px; font-weight: 700;
          text-transform: uppercase; letter-spacing: .03em;
        }
        .ce-score {
          font-size: 22px;
          font-weight: 700; line-height: 1; flex-shrink: 0;
        }
        .ce-score-unit { font-size: 11px; color: var(--text-muted); font-weight: 500; }
        .ce-why {
          font-size: 12.5px; color: var(--text-secondary);
          margin: 11px 0 12px; line-height: 1.5;
        }
        .ce-stats {
          display: grid; grid-template-columns: 1fr 1fr; gap: 7px 14px;
          border-top: 1px solid var(--border); padding-top: 11px;
        }
        .ce-stats div { display: flex; justify-content: space-between; gap: 8px; }
        .ce-stats dt { font-size: 11.5px; color: var(--text-muted); }
        .ce-stats dd {
          font-size: 11.5px; color: var(--navy); font-weight: 600;
          font-variant-numeric: tabular-nums;
        }
        .ce-method {
          font-size: 11.5px; color: var(--text-muted);
          margin-top: 12px; line-height: 1.5;
        }

        @media (max-width: 1100px) {
          .ce-controls { grid-template-columns: 1fr 1fr 1fr; }
          .ce-controls > div:first-child { grid-column: 1 / -1; }
          .ce-submit { grid-column: 1 / -1; }
        }
        @media (max-width: 560px) {
          .ce-controls { grid-template-columns: 1fr 1fr; }
          .ce-stats { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  )
}
