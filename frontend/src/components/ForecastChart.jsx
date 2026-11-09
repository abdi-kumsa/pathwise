import { Fragment, useMemo, useState } from 'react'
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
  ResponsiveContainer, LabelList,
} from 'recharts'

import { axisProps, gridProps, tooltipProps, CHROME, fmtNum, fmtCompact } from '../config/chartTheme'

const ACCENT = '#2563EB'
const BAND = 'rgba(37, 99, 235, 0.12)'
const MUTED = '#CBD5E1'

// Counts are the common case; a page forecasting an index passes its own formatter.
const fmtRounded = v => fmtNum(v == null ? v : Math.round(v))

/**
 * Observed history continued by a forecast, with the selected estimator's
 * 90% range.
 *
 *   series: [{ key, history: [{ x, y }], forecast: [{ x, y, low, high }] }]
 *
 * One series is in focus: accent colour, shaded range, end label. The rest
 * are grey, so the chart still reads with six series on it. Chips above the
 * plot change the focus and double as the legend. History and forecast are
 * drawn as separate lines that meet at the last observed point, with a
 * reference line there, so the reader can see where the projection starts.
 */
export default function ForecastChart({
  series, height = 300, yFormatter = fmtRounded, tickFormatter = fmtCompact,
  focus, defaultFocus, onFocus, caption, unit,
}) {
  const [own, setOwn] = useState(defaultFocus ?? null)
  const keys = series.map(s => s.key)
  const active = keys.includes(focus) ? focus : keys.includes(own) ? own : keys[0]
  const pick = k => { setOwn(k); onFocus?.(k) }

  const { data, origin } = useMemo(() => build(series), [series])
  const last = data.length - 1
  const focused = series.find(s => s.key === active)
  const hasBand = !!focused?.forecast.some(p => p.low != null && p.high != null)
  // Room on the right for the end label: the longest series name at ~6.8px a character.
  const longest = Math.max(8, ...keys.map(k => k.length))
  const rightMargin = Math.min(220, 24 + Math.ceil(longest * 6.8))

  if (!series.length) return null

  return (
    <div>
      {series.length > 1 && (
        <div className="fc-chips" role="tablist" aria-label="Series in focus">
          {series.map(s => (
            <button
              key={s.key} type="button" role="tab" aria-selected={s.key === active}
              className={`fc-chip${s.key === active ? ' active' : ''}`}
              onClick={() => pick(s.key)}
            >
              <span className="swatch" />{s.key}
            </button>
          ))}
        </div>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart data={data} margin={{ top: 12, right: rightMargin, left: 0, bottom: 0 }}>
          <CartesianGrid {...gridProps} />
          <XAxis dataKey="x" {...axisProps} />
          <YAxis {...axisProps} tickFormatter={tickFormatter} width={60} />
          <Tooltip {...tooltipProps} formatter={tooltipValue(yFormatter)} />
          {origin != null && (
            <ReferenceLine
              x={origin} stroke={CHROME.axis} strokeDasharray="4 3"
              label={{ value: `observed to ${origin}`, position: 'insideTopLeft', fontSize: 11, fill: CHROME.label }}
            />
          )}
          {series.filter(s => s.key !== active).map(s => (
            <Fragment key={s.key}>
              <Line type="monotone" dataKey={`h:${s.key}`} name={`${s.key}, observed`}
                    stroke={MUTED} strokeWidth={1.5} dot={false} isAnimationActive={false} />
              <Line type="monotone" dataKey={`f:${s.key}`} name={`${s.key}, forecast`}
                    stroke={MUTED} strokeWidth={1.5} strokeDasharray="4 3" dot={false} isAnimationActive={false} />
            </Fragment>
          ))}
          {hasBand && (
            <Area type="monotone" dataKey={`b:${active}`} name="90% range"
                  stroke="none" fill={BAND} isAnimationActive={false} legendType="none" />
          )}
          <Line type="monotone" dataKey={`h:${active}`} name={`${active}, observed`}
                stroke={ACCENT} strokeWidth={2} dot={false} isAnimationActive={false} />
          <Line type="monotone" dataKey={`f:${active}`} name={`${active}, forecast`}
                stroke={ACCENT} strokeWidth={2} strokeDasharray="5 3"
                dot={{ r: 2.5, fill: ACCENT, strokeWidth: 0 }} isAnimationActive={false}>
            <LabelList
              dataKey={`f:${active}`}
              content={(p) => <EndLabel {...p} last={last} text={active} format={yFormatter} />}
            />
          </Line>
        </ComposedChart>
      </ResponsiveContainer>
      <p className="fc-caption">
        Solid line: observed{unit ? ` ${unit}` : ''}. Dashed: forecast.
        {hasBand ? ` Shaded: 90% range for ${active}.` : ''}
        {series.length > 1 ? ' Choose the series in focus above.' : ''}
        {caption ? ` ${caption}` : ''}
      </p>
    </div>
  )
}

function EndLabel({ x, y, value, index, last, text, format }) {
  if (index !== last || value == null) return null
  return (
    <text x={x + 8} y={y} fontSize={11.5} fill={ACCENT} fontWeight={600}>
      <tspan x={x + 8} dy={-2}>{text}</tspan>
      <tspan x={x + 8} dy={13} fontWeight={400} fill={CHROME.tickFill}>{format(value)}</tspan>
    </text>
  )
}

function tooltipValue(format) {
  return (value) => {
    if (Array.isArray(value)) return `${format(value[0])} – ${format(value[1])}`
    return format(value)
  }
}

/** Sum `cols` per value of `key`, ascending by key: the usual step from
 *  per-programme or per-region rows to the series a page charts. */
export function sumBy(list, key, cols) {
  const acc = new Map()
  list.forEach(r => {
    const k = r[key]
    const cur = acc.get(k) ?? Object.fromEntries(cols.map(c => [c, 0]))
    cols.forEach(c => { cur[c] += Number(r[c] || 0) })
    acc.set(k, cur)
  })
  return [...acc.entries()].sort((a, b) => a[0] - b[0]).map(([k, v]) => ({ [key]: k, ...v }))
}

/** Merge every series onto one x axis. The last observed point is repeated as
 *  the first forecast point so the two lines join. */
export function build(series) {
  const xs = new Set()
  series.forEach(s => {
    s.history.forEach(p => xs.add(p.x))
    s.forecast.forEach(p => xs.add(p.x))
  })
  const rows = [...xs].sort((a, b) => a - b).map(x => ({ x }))
  const at = Object.fromEntries(rows.map(r => [r.x, r]))
  let origin = null
  series.forEach(s => {
    s.history.forEach(p => { at[p.x][`h:${s.key}`] = p.y })
    const lastH = s.history.length ? s.history[s.history.length - 1] : null
    if (lastH) {
      at[lastH.x][`f:${s.key}`] = lastH.y
      at[lastH.x][`b:${s.key}`] = [lastH.y, lastH.y]
      origin = origin == null ? lastH.x : Math.max(origin, lastH.x)
    }
    s.forecast.forEach(p => {
      at[p.x][`f:${s.key}`] = p.y
      if (p.low != null && p.high != null) at[p.x][`b:${s.key}`] = [p.low, p.high]
    })
  })
  return { data: rows, origin }
}
