import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, ReferenceArea, LabelList,
} from 'recharts'

import SectionHeader from '../../components/SectionHeader'
import LoadingSpinner from '../../components/LoadingSpinner'
import ErrorBanner from '../../components/ErrorBanner'
import DataNote from '../../components/DataNote'
import useFetch from '../../hooks/useFetch'
import { getInvestmentQuadrant } from '../../api/roles'
import {
  SERIES, VERDICT_COLOR, axisProps, gridProps,
  fmtPct, fmtDelta, fmtNum,
} from '../../config/chartTheme'

/**
 * "MoE and MoL to see which field or department are emerging that show progress
 * for future investment" — this is the MoE answer.
 *
 * Labour-demand growth against the graduate-supply growth meant to serve it.
 * A field above the demand median and below the supply median is one where new
 * capacity is justified.
 *
 * Colour note: quadrant membership is already encoded by POSITION, and the
 * quadrant backgrounds are tinted, so the dots use a single series colour with
 * direct labels. Colouring nine dots by four categories would have put every
 * hue beside every other — the all-pairs case, which only three categorical
 * slots can clear — for information the axes already carry.
 */

const QUADRANT_TINT = {
  invest:     'rgba(12, 163, 12, 0.055)',
  sustain:    'rgba(37, 99, 235, 0.05)',
  oversupply: 'rgba(250, 178, 25, 0.06)',
  review:     'rgba(100, 116, 139, 0.04)',
}

function QuadrantTooltip({ active, payload }) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  return (
    <div style={{
      background: '#fff', border: '1px solid #E6E9F0', borderRadius: 10,
      boxShadow: '0 8px 24px rgba(15,23,42,0.10)', padding: '11px 13px',
      fontSize: 12.5, maxWidth: 280,
    }}>
      <p style={{ fontWeight: 700, color: '#0F172A', marginBottom: 6 }}>{p.field}</p>
      <p style={{
        display: 'inline-block', fontSize: 10.5, fontWeight: 700,
        textTransform: 'uppercase', letterSpacing: '.04em', borderRadius: 5,
        padding: '2px 7px', marginBottom: 8,
        color: VERDICT_COLOR[p.quadrant], background: VERDICT_COLOR[p.quadrant] + '1A',
      }}>{p.quadrant}</p>
      <p style={{ color: '#475569', lineHeight: 1.5, marginBottom: 8 }}>{p.action}</p>
      <dl style={{ display: 'grid', gridTemplateColumns: 'auto auto', gap: '3px 12px', fontSize: 11.5 }}>
        <dt style={{ color: '#94A3B8' }}>Demand growth</dt>
        <dd style={{ textAlign: 'right', fontWeight: 600 }}>{fmtDelta(p.demand_growth_pct)}/yr</dd>
        <dt style={{ color: '#94A3B8' }}>Supply growth</dt>
        <dd style={{ textAlign: 'right', fontWeight: 600 }}>{fmtDelta(p.supply_growth_pct)}/yr</dd>
        <dt style={{ color: '#94A3B8' }}>Openings</dt>
        <dd style={{ textAlign: 'right', fontWeight: 600 }}>{fmtNum(p.demand_openings)}</dd>
        <dt style={{ color: '#94A3B8' }}>Employment 6mo</dt>
        <dd style={{ textAlign: 'right', fontWeight: 600 }}>{fmtPct(p.employment_rate_pct)}</dd>
      </dl>
    </div>
  )
}

/**
 * Point label that dodges its neighbours.
 *
 * Two fields can land close enough together that a fixed "above the dot"
 * label overlaps the next one — UX Design and Data & Analytics do exactly
 * that. So each label checks the already-placed ones and flips below the dot
 * when the slot above is taken, nudging further if that is taken too.
 */
function FieldLabel({ x, y, value, index, points = [] }) {
  const CX = 44   // half the width a label occupies, in px
  const CY = 13   // one line of vertical clearance

  // Deterministic: only compare against points earlier in the array, so the
  // same field always resolves to the same side across re-renders.
  const placed = points.slice(0, index)
  const collides = (dy) => placed.some((_, i) => {
    const pos = FieldLabel._pos?.[i]
    return pos && Math.abs(pos.x - x) < CX && Math.abs(pos.y - (y + dy)) < CY
  })

  if (index === 0) FieldLabel._pos = []

  let dy = -10                                  // default: above the dot
  if (collides(dy)) dy = 18                     // flip below
  if (collides(dy)) dy = 30                     // push further down
  FieldLabel._pos[index] = { x, y: y + dy }

  return (
    <text
      x={x} y={y + dy}
      textAnchor="middle"
      style={{ fontSize: 10.5, fill: '#475569', fontWeight: 500 }}
    >
      {value}
    </text>
  )
}

export default function InvestmentQuadrantPage() {
  const { data, loading, error, refetch } = useFetch(getInvestmentQuadrant)

  const points = data?.points ?? []
  const dMed = data?.demand_median ?? 0
  const sMed = data?.supply_median ?? 0

  // Pad the axes so no dot sits on the frame.
  const dVals = points.map(p => p.demand_growth_pct)
  const sVals = points.map(p => p.supply_growth_pct)
  const pad = (arr, f = 0.18) => {
    if (!arr.length) return [0, 1]
    const lo = Math.min(...arr), hi = Math.max(...arr)
    const m = Math.max((hi - lo) * f, 1)
    return [Math.floor(lo - m), Math.ceil(hi + m)]
  }
  const [dLo, dHi] = pad(dVals)
  const [sLo, sHi] = pad(sVals)

  const byQuadrant = (name) => points.filter(p => p.quadrant === name)

  return (
    <div>
      <SectionHeader
        title="Investment matrix"
        subtitle="Where labour demand is outpacing the graduates being produced to meet it"
      />

      {error && <ErrorBanner message={error} onRetry={refetch} />}
      {loading && <LoadingSpinner message="Building the investment matrix…" height={420} />}

      {data && points.length > 0 && (
        <>
          <div className="panel" style={{ marginBottom: 20 }}>
            <p className="panel-title">Demand growth vs graduate supply growth</p>
            <p className="panel-sub">
              Compound annual growth 2016–2025. Split at the median of each axis
              ({fmtDelta(dMed)} demand, {fmtDelta(sMed)} supply), so the four
              quadrants always partition the nine fields.
            </p>

            <ResponsiveContainer width="100%" height={430}>
              <ScatterChart margin={{ top: 20, right: 32, left: 8, bottom: 46 }}>
                <CartesianGrid {...gridProps} vertical />

                {/* Quadrant tints — the background carries the verdict, not the dot */}
                <ReferenceArea x1={sLo} x2={sMed} y1={dMed} y2={dHi} fill={QUADRANT_TINT.invest} />
                <ReferenceArea x1={sMed} x2={sHi} y1={dMed} y2={dHi} fill={QUADRANT_TINT.sustain} />
                <ReferenceArea x1={sMed} x2={sHi} y1={dLo} y2={dMed} fill={QUADRANT_TINT.oversupply} />
                <ReferenceArea x1={sLo} x2={sMed} y1={dLo} y2={dMed} fill={QUADRANT_TINT.review} />

                <XAxis
                  type="number" dataKey="supply_growth_pct" domain={[sLo, sHi]}
                  {...axisProps} tickFormatter={v => `${v}%`}
                  label={{ value: 'Graduate supply growth / yr →', position: 'insideBottom',
                           offset: -32, fontSize: 11.5, fill: '#64748B' }}
                />
                <YAxis
                  type="number" dataKey="demand_growth_pct" domain={[dLo, dHi]}
                  {...axisProps} tickFormatter={v => `${v}%`} width={54}
                  label={{ value: 'Labour demand growth / yr →', angle: -90,
                           position: 'insideLeft', offset: 6, fontSize: 11.5, fill: '#64748B',
                           style: { textAnchor: 'middle' } }}
                />
                <ZAxis range={[150, 150]} />

                <ReferenceLine x={sMed} stroke="#CBD5E1" strokeDasharray="4 4" />
                <ReferenceLine y={dMed} stroke="#CBD5E1" strokeDasharray="4 4" />

                <Tooltip content={<QuadrantTooltip />} cursor={{ strokeDasharray: '3 3' }} />

                <Scatter isAnimationActive={false}
                  data={points}
                  fill={SERIES[0]}
                  stroke="#FFFFFF"
                  strokeWidth={2}
                >
                  <LabelList dataKey="field" content={<FieldLabel points={points} />} />
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>

            <div className="quad-legend">
              <span><i style={{ background: 'rgba(12,163,12,0.16)' }} /> Invest — high demand, low supply</span>
              <span><i style={{ background: 'rgba(37,99,235,0.16)' }} /> Sustain — both growing</span>
              <span><i style={{ background: 'rgba(250,178,25,0.20)' }} /> Oversupply risk — supply outpacing demand</span>
              <span><i style={{ background: 'rgba(100,116,139,0.14)' }} /> Review — neither growing</span>
            </div>
          </div>

          {/* ── Verdict columns ────────────────────────────────────────── */}
          <div className="quad-cols">
            {['Invest', 'Sustain', 'Oversupply risk', 'Review'].map(q => {
              const list = byQuadrant(q)
              return (
                <div key={q} className="panel quad-col">
                  <p className="quad-col-title" style={{ color: VERDICT_COLOR[q] }}>
                    {q}
                    <span className="quad-count">{list.length}</span>
                  </p>
                  {list.length === 0 ? (
                    <p className="quad-empty">No fields</p>
                  ) : list.map(p => (
                    <div key={p.field} className="quad-item">
                      <p className="quad-field">{p.field}</p>
                      <p className="quad-nums">
                        demand {fmtDelta(p.demand_growth_pct)} · supply {fmtDelta(p.supply_growth_pct)}
                      </p>
                      <p className="quad-progs">
                        {p.programs.join(', ') || '—'}
                      </p>
                    </div>
                  ))}
                </div>
              )
            })}
          </div>

          <div style={{ marginTop: 20 }}>
            <DataNote>
              Quadrant boundaries are the medians of the nine fields, so membership
              is relative to this cohort rather than an absolute standard. A field in
              “Review” has slow growth on both axes — it is not necessarily small:
              check total openings before acting. {data.dataset_label}.
            </DataNote>
          </div>
        </>
      )}

      <style>{`
        .quad-legend {
          display: flex; flex-wrap: wrap; gap: 8px 20px;
          margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--border);
          font-size: 11.5px; color: var(--text-secondary);
        }
        .quad-legend span { display: flex; align-items: center; gap: 7px; }
        .quad-legend i {
          width: 11px; height: 11px; border-radius: 3px;
          display: inline-block; flex-shrink: 0;
        }
        .quad-cols {
          display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 16px;
        }
        .quad-col { padding: 16px 18px 18px; }
        .quad-col-title {
          font-size: 13px; font-weight: 700;
          display: flex; align-items: center; gap: 8px; margin-bottom: 12px;
        }
        .quad-count {
          background: var(--page); color: var(--text-secondary);
          border-radius: 20px; padding: 1px 8px; font-size: 11px; font-weight: 600;
        }
        .quad-item { padding: 9px 0; border-top: 1px solid #F4F6FA; }
        .quad-item:first-of-type { border-top: none; padding-top: 0; }
        .quad-field { font-size: 13px; font-weight: 600; color: var(--navy); }
        .quad-nums {
          font-size: 11px; color: var(--text-secondary); margin-top: 2px;
          font-variant-numeric: tabular-nums;
        }
        .quad-progs { font-size: 11px; color: var(--text-muted); margin-top: 3px; line-height: 1.45; }
        .quad-empty { font-size: 12px; color: var(--text-muted); }
      `}</style>
    </div>
  )
}
