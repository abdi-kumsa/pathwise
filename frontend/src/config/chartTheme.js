/**
 * One chart language for the whole app.
 *
 * Before this, every page picked its own hexes inline (#2563eb, #10b981,
 * #ef4444 repeated across a dozen files), so two charts side by side could use
 * the same colour for different things.
 *
 * ── Palette provenance ───────────────────────────────────────────────────────
 *
 * These are not eyeballed. Each set below was run through the data-viz
 * validator against this app's actual chart surface (white, #FFFFFF) and is
 * recorded with its result:
 *
 *   CATEGORICAL (6 slots, adjacent pairs — bars, stacks, lines)
 *     worst adjacent CVD ΔE 8.8 (protan) · worst normal-vision ΔE 20.3
 *     all slots ≥ 3:1 contrast, inside the lightness band, above the chroma floor
 *
 *   CATEGORICAL first 3 slots (all pairs — scatter, dot, bubble)
 *     worst all-pairs CVD ΔE 8.4 (tritan) · worst normal-vision ΔE 28.4
 *     Charts where every mark can sit beside every other must use at most
 *     these three. Past three, fold into "Other" or facet.
 *
 *   ORDINAL blue ramp (funnel stages, composition stacks)
 *     monotone lightness, all ΔL gaps ≥ 0.06, light end 2.11:1 (≥ 2:1 floor)
 *
 * If you change a hex here, re-run the validator — do not reason about it:
 *   node scripts/validate_palette.js "<hex,...>" --mode light --surface "#FFFFFF"
 *
 * ── Rules this file exists to enforce ────────────────────────────────────────
 *
 *  - Colour follows the entity, never its rank. Filtering a series must not
 *    repaint the survivors, so assign from SERIES by index of a stable key.
 *  - Never a dual-axis chart. Two measures of different scale get two charts.
 *  - Status colour never carries meaning alone — always ship the label too.
 *    STATUS.warning and STATUS.serious are deliberately below 3:1 on white;
 *    the text label is the mitigation, not decoration.
 */

// ── Categorical: identity ─────────────────────────────────────────────────────
// Fixed order. Never cycle: a 7th series folds into "Other" or becomes a facet.
export const SERIES = [
  '#2563EB', // 1 blue
  '#EA580C', // 2 orange
  '#0E9F6E', // 3 green
  '#D97706', // 4 amber
  '#DB2777', // 5 magenta
  '#6D28D9', // 6 violet
]

/** Slots safe for charts where any mark can sit beside any other (scatter, dot). */
export const SERIES_ALL_PAIRS = SERIES.slice(0, 3)

// ── Ordinal: ordered magnitude ────────────────────────────────────────────────
// One hue, light → dark. Used for funnel stages and composition stacks.
export const ORDINAL_BLUE = ['#86B6EF', '#3B82F6', '#1D4ED8']

// ── Status: state ─────────────────────────────────────────────────────────────
// Reserved. Never reused as "series 4". Always rendered with a text label.
export const STATUS = {
  good:     '#0CA30C',
  warning:  '#FAB219',
  serious:  '#EC835A',
  critical: '#D03B3B',
}

/** Supply-demand severity → status colour. Always paired with the label text. */
export const SEVERITY_COLOR = {
  critical: STATUS.critical,
  high:     STATUS.serious,
  moderate: STATUS.warning,
  low:      STATUS.good,
}

/** Expansion / investment verdicts. Same rule: colour plus the word, never alone. */
export const VERDICT_COLOR = {
  Expand:            STATUS.good,
  Hold:              STATUS.warning,
  Consolidate:       STATUS.critical,
  Invest:            STATUS.good,
  Sustain:           '#2563EB',
  'Oversupply risk': STATUS.warning,
  Review:            '#64748B',
}

/** Graduate-to-role fit, ordered worst → best so a stack reads in one direction. */
export const FIT_COLOR = {
  Undereducated: ORDINAL_BLUE[0],
  Overeducated:  ORDINAL_BLUE[1],
  Matched:       ORDINAL_BLUE[2],
}

// ── Chrome ────────────────────────────────────────────────────────────────────
// Recessive by design: the data should be the only assertive thing on screen.
export const CHROME = {
  surface:  '#FFFFFF',
  grid:     '#EEF1F6',
  axis:     '#CBD5E1',
  tickFill: '#64748B',
  label:    '#94A3B8',
}

/** Spread onto <XAxis>/<YAxis>. */
export const axisProps = {
  tick:      { fontSize: 11, fill: CHROME.tickFill },
  tickLine:  false,
  axisLine:  { stroke: CHROME.axis },
}

/** Spread onto <CartesianGrid>. Horizontal rules only — vertical ones add noise. */
export const gridProps = {
  strokeDasharray: '3 3',
  stroke:          CHROME.grid,
  vertical:        false,
}

/** Spread onto <Tooltip>. */
export const tooltipProps = {
  cursor: { fill: 'rgba(37, 99, 235, 0.06)' },
  contentStyle: {
    borderRadius:  '10px',
    border:        '1px solid #E6E9F0',
    boxShadow:     '0 8px 24px rgba(15,23,42,0.10)',
    fontSize:      '12.5px',
    fontFamily:    'Inter, sans-serif',
    padding:       '9px 12px',
  },
  labelStyle: { color: '#0F172A', fontWeight: 600, marginBottom: 4 },
}

/**
 * Stacked-bar segments need a 2px gap so adjacent fills do not read as one
 * block. Recharts has no spacer, so the segment is stroked in the surface
 * colour — visually identical, and it works at any bar width.
 */
export const stackGap = {
  stroke:      CHROME.surface,
  strokeWidth: 2,
}

/** Rounded data-end anchored to the baseline. */
export const RADIUS_V = [4, 4, 0, 0]   // vertical bars
export const RADIUS_H = [0, 4, 4, 0]   // horizontal bars

/**
 * Stable colour for a series key.
 * Index into a fixed key list, not into the filtered render order, so hiding
 * one series never recolours the rest.
 */
export function colorFor(key, keys) {
  const i = keys.indexOf(key)
  return SERIES[(i < 0 ? 0 : i) % SERIES.length]
}

// ── Formatters ────────────────────────────────────────────────────────────────

/**
 * Axis-tick abbreviation. Headline figures use fmtNum at full precision; this
 * is for the space-starved places. One decimal below 10 of a unit so adjacent
 * ticks (2,000 and 2,500) never collapse to the same label.
 */
export const fmtCompact = (v) => {
  if (v == null || Number.isNaN(v)) return '—'
  const n = Number(v)
  const scaled = (x, suffix) =>
    (Math.abs(x) < 10 ? x.toFixed(1).replace(/\.0$/, '') : x.toFixed(0)) + suffix
  if (Math.abs(n) >= 1e9) return scaled(n / 1e9, 'B')
  if (Math.abs(n) >= 1e6) return scaled(n / 1e6, 'M')
  if (Math.abs(n) >= 1e3) return scaled(n / 1e3, 'K')
  return String(Math.round(n))
}

export const fmtMoney = (v) =>
  v == null || Number.isNaN(v) ? '—' : '$' + fmtCompact(v)

export const fmtPct = (v, dp = 1) =>
  v == null || Number.isNaN(v) ? '—' : Number(v).toFixed(dp) + '%'

export const fmtNum = (v) =>
  v == null || Number.isNaN(v) ? '—' : Number(v).toLocaleString()

/** Signed percentage, for growth rates where direction is the point. */
export const fmtDelta = (v, dp = 1) => {
  if (v == null || Number.isNaN(v)) return '—'
  const n = Number(v)
  return (n > 0 ? '+' : '') + n.toFixed(dp) + '%'
}

export const deltaDirection = (v) =>
  v == null ? 'neutral' : v > 0 ? 'up' : v < 0 ? 'down' : 'neutral'

/**
 * Shorten a US metro name for an axis tick.
 *
 * The source data uses full CBSA names — "Miami-Fort Lauderdale-West Palm
 * Beach" — which wrap to three lines on a category axis and swamp the plot.
 * The first component is the anchor city and is what a reader recognises;
 * the tooltip still shows the full name.
 */
export const shortMetro = (name) => {
  if (!name) return '—'
  const first = String(name).split('-')[0].trim()
  return first.length > 18 ? first.slice(0, 17) + '…' : first
}
