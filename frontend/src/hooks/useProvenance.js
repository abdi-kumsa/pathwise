/**
 * Read the provenance block off an API payload.
 *
 * Fallback stamp matches the backend middleware: simulated Ethiopian
 * structure, 2016–2025, not official MoE / MoLS / ESS statistics.
 */
export const DEFAULT_PROVENANCE = {
  source: 'Simulated Ethiopian structure',
  tier: 'simulated',
  as_of: '2016–2025',
  method: 'seeded generator in data/ethiopia/generate.py',
  caveat: 'Simulated Ethiopian structure. Not official MoE, MoLS or ESS statistics.',
}

export default function useProvenance(payload, fallback = DEFAULT_PROVENANCE) {
  if (payload && typeof payload === 'object' && payload.provenance) {
    return payload.provenance
  }
  return fallback
}
