import { useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import KPICard from '../../components/KPICard'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getMismatch } from '../../api/roles'
import {
  FIT_COLOR, tooltipProps, RADIUS_H, stackGap,
  fmtNum, fmtPct,
} from '../../config/chartTheme'

/**
 * Graduate-to-role fit — Matched / Overeducated / Undereducated.
 *
 * Presented as a SYSTEM-WIDE statistic, deliberately. The API returns
 * `comparable: false` because the distribution varies by only a few percentage
 * points across every field and programme in this dataset. So:
 *
 *   - the headline is one stacked bar for the whole system, not nine
 *   - the per-field and per-programme figures live in a plain table, sorted
 *     alphabetically rather than by match rate, so the page never implies a
 *     ranking the data cannot support
 *   - the observed spread is stated on the page, so a reader can judge for
 *     themselves how little separates the groups
 *
 * Charting these as a league table would be presenting sampling noise as a
 * finding. The mismatch signal that does vary is on the Supply & demand page.
 */

const ORDER = ['Undereducated', 'Overeducated', 'Matched']

export default function SkillsMismatchPage() {
  const [view, setView] = useState('field')

  const { data, loading, error, refetch } = useFetch(
    () => Promise.all([getMismatch('overview'), getMismatch(view)])
      .then(([overview, detail]) => ({ overview, detail })),
    [view]
  )

  const o = data?.overview
  const detail = data?.detail
  const rows = detail?.fields ?? detail?.programs ?? []
  const rowKey = view === 'field' ? 'field' : 'program'

  // One bar, whole system. Stacked worst → best so it reads in one direction.
  const systemBar = o ? [Object.fromEntries([
    ['name', 'All placed graduates'],
    ...o.breakdown.map(b => [b.status, b.count]),
  ])] : []

  return (
    <div>
      <SectionHeader
        title="Skills mismatch"
        subtitle="Whether graduates land roles that match the credential they hold"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Loading fit classification…" height={300} />}

      {o && (
        <>
          <div className="kpi-grid">
            <KPICard
              label="Placed graduates"
              value={fmtNum(o.total_placed)}
              delta={`${fmtNum(o.total_unplaced)} not placed`}
              deltaDirection="neutral"
              icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M20 6 9 17l-5-5"/></svg>}
            />
            {o.breakdown.map(b => (
              <KPICard
                key={b.status}
                label={b.status}
                value={fmtPct(b.share_pct)}
                delta={fmtNum(b.count) + ' graduates'}
                deltaDirection={b.status === 'Matched' ? 'up' : 'neutral'}
                icon={<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M22 10 12 5 2 10l10 5 10-5ZM6 12v5c0 1 3 3 6 3s6-2 6-3v-5"/></svg>}
              />
            ))}
          </div>

          {/* ── The honest headline ─────────────────────────────────────── */}
          <div className="panel" style={{ marginBottom: 16 }}>
            <p className="panel-title">System-wide credential fit</p>
            <p className="panel-sub">{o.headline}</p>

            <ResponsiveContainer width="100%" height={120}>
              <BarChart data={systemBar} layout="vertical" stackOffset="expand"
                        margin={{ top: 8, right: 16, left: 8, bottom: 0 }}>
                <XAxis type="number" hide domain={[0, 1]} />
                <YAxis type="category" dataKey="name" hide />
                <Tooltip
                  {...tooltipProps}
                  formatter={(v, name) => [`${fmtNum(v)} (${fmtPct(v / o.total_placed * 100)})`, name]}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
                {ORDER.map((status, i) => (
                  <Bar isAnimationActive={false}
                    key={status}
                    dataKey={status}
                    stackId="fit"
                    fill={FIT_COLOR[status]}
                    barSize={54}
                    radius={i === ORDER.length - 1 ? RADIUS_H : 0}
                    {...stackGap}
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div style={{ marginBottom: 20 }}>
            <DataNote tone="caution">
              <strong>Read this as a system total, not a comparison.</strong>{' '}
              {o.caveat}
              {detail?.spread_pct != null && (
                <> The observed spread across {view === 'field' ? 'fields' : 'programmes'} is
                  just <strong>{detail.spread_pct} percentage points</strong>.</>
              )}
            </DataNote>
          </div>

          {/* ── Detail, as a table rather than a ranked chart ───────────── */}
          <div className="panel">
            <div className="mm-head">
              <div>
                <p className="panel-title">Breakdown by {view === 'field' ? 'field' : 'programme'}</p>
                <p className="panel-sub">
                  Listed alphabetically, not ranked — see the note above.
                </p>
              </div>
              <div className="mm-toggle" role="group" aria-label="Breakdown level">
                <button className={view === 'field' ? 'active' : ''} onClick={() => setView('field')}>
                  By field
                </button>
                <button className={view === 'program' ? 'active' : ''} onClick={() => setView('program')}>
                  By programme
                </button>
              </div>
            </div>

            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>{view === 'field' ? 'Field' : 'Programme'}</th>
                    <th>Placed</th>
                    <th>Undereducated</th>
                    <th>Overeducated</th>
                    <th>Matched</th>
                    <th>Match rate</th>
                  </tr>
                </thead>
                <tbody>
                  {[...rows].sort((a, b) => String(a[rowKey]).localeCompare(String(b[rowKey]))).map(r => (
                    <tr key={r[rowKey]}>
                      <td style={{ textAlign: 'left', fontWeight: 500 }}>{r[rowKey]}</td>
                      <td className="num">{fmtNum(r.total)}</td>
                      <td className="num">{fmtNum(r.undereducated)}</td>
                      <td className="num">{fmtNum(r.overeducated)}</td>
                      <td className="num">{fmtNum(r.matched)}</td>
                      <td className="num">{fmtPct(r.match_rate_pct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      <style>{`
        .mm-head {
          display: flex; align-items: flex-start; justify-content: space-between;
          gap: 16px; flex-wrap: wrap; margin-bottom: 4px;
        }
        .mm-toggle { display: flex; background: var(--page); border-radius: 9px; padding: 3px; }
        .mm-toggle button {
          border: none; background: none; padding: 7px 14px; border-radius: 7px;
          font-size: 12.5px; font-weight: 500; color: var(--text-secondary);
          cursor: pointer; font-family: inherit; white-space: nowrap;
        }
        .mm-toggle button.active {
          background: var(--white); color: var(--navy); font-weight: 600;
          box-shadow: var(--shadow-card);
        }
        .table-scroll th {
          text-align: right; padding: 8px 12px; font-size: 11px; font-weight: 600;
          color: var(--text-muted); text-transform: uppercase; letter-spacing: .04em;
          border-bottom: 1px solid var(--border); white-space: nowrap;
        }
        .table-scroll td {
          padding: 9px 12px; border-bottom: 1px solid #F4F6FA;
          color: var(--navy); text-align: right;
        }
        .table-scroll td.num { font-variant-numeric: tabular-nums; }
      `}</style>
    </div>
  )
}
