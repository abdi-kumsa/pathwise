import { ORDINAL_BLUE, STATUS } from '../config/chartTheme'

/** Fourteen dashboard regions keyed to data/ethiopia/reference/dimensions.py.
 *  Layout is schematic — not a CSA administrative map. */
export const ETHIOPIA_REGIONS = [
  { name: 'Tigray', x: 168, y: 10, w: 92, h: 52 },
  { name: 'Afar', x: 268, y: 42, w: 78, h: 88 },
  { name: 'Amhara', x: 132, y: 68, w: 128, h: 78 },
  { name: 'Benishangul-Gumuz', x: 36, y: 88, w: 90, h: 68 },
  { name: 'Oromia', x: 88, y: 154, w: 196, h: 118 },
  { name: 'Addis Ababa', x: 158, y: 186, w: 52, h: 34 },
  { name: 'Gambela', x: 18, y: 198, w: 68, h: 68 },
  { name: 'Dire Dawa', x: 304, y: 138, w: 52, h: 28 },
  { name: 'Harari', x: 304, y: 172, w: 44, h: 32 },
  { name: 'Somali', x: 252, y: 210, w: 128, h: 132 },
  { name: 'South West Ethiopia', x: 48, y: 278, w: 82, h: 58 },
  { name: 'Central Ethiopia', x: 136, y: 282, w: 82, h: 48 },
  { name: 'Sidama', x: 178, y: 334, w: 70, h: 42 },
  { name: 'South Ethiopia', x: 88, y: 338, w: 92, h: 68 },
]

function fillFor(row, max) {
  if (row?.status === 'shortage') return STATUS.serious
  if (row?.status === 'oversupply') return STATUS.warning
  if (row?.status === 'balanced') return STATUS.good
  const v = Number(row?.value || 0)
  if (!max || max <= 0) return ORDINAL_BLUE[0]
  const t = v / max
  if (t < 0.34) return ORDINAL_BLUE[0]
  if (t < 0.67) return ORDINAL_BLUE[1]
  return ORDINAL_BLUE[2]
}

export default function EthiopiaRegionMap({
  regions = [],
  selected,
  onSelect,
  valueLabel = 'value',
}) {
  const byName = Object.fromEntries(regions.map(r => [r.name, r]))
  const max = Math.max(0, ...regions.map(r => Number(r.value || 0)))

  return (
    <svg viewBox="0 0 400 430" role="img" aria-label="Ethiopia regions (schematic)"
         style={{ width: '100%', height: 'auto', maxHeight: 420 }}>
      {ETHIOPIA_REGIONS.map(tile => {
        const row = byName[tile.name] || { name: tile.name, value: 0 }
        const active = selected === tile.name
        const fill = fillFor(row, max)
        const fg = fill === ORDINAL_BLUE[2] || fill === STATUS.serious ? '#FFFFFF' : '#0F172A'
        return (
          <g key={tile.name}>
            <rect
              data-testid={`region-${tile.name}`}
              x={tile.x} y={tile.y} width={tile.w} height={tile.h} rx={8}
              fill={fill}
              stroke={active ? '#0F172A' : '#FFFFFF'}
              strokeWidth={active ? 2.5 : 1.5}
              style={{ cursor: onSelect ? 'pointer' : 'default' }}
              onClick={() => onSelect && onSelect(tile.name)}
            >
              <title>{`${tile.name}: ${row.value ?? '—'} ${valueLabel}${row.status ? ` (${row.status})` : ''}`}</title>
            </rect>
            <text
              x={tile.x + tile.w / 2} y={tile.y + tile.h / 2}
              textAnchor="middle" dominantBaseline="middle"
              fill={fg} fontSize={tile.w < 55 ? 7 : 9} fontWeight={600}
              style={{ pointerEvents: 'none', fontFamily: 'Inter, sans-serif' }}
            >
              {tile.name.length > 16 ? tile.name.split(' ')[0] : tile.name}
            </text>
          </g>
        )
      })}
    </svg>
  )
}
