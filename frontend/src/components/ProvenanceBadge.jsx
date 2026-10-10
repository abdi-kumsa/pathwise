/**
 * Compact chip for the source + vintage of the data on screen.
 *
 * The shell uses the default simulated Ethiopia stamp. Pages can pass the
 * `provenance` block from an API response via useProvenance().
 */
export default function ProvenanceBadge({ provenance }) {
  if (!provenance) return null

  const label = [provenance.source, provenance.as_of].filter(Boolean).join(' · ')
  const title = [
    provenance.caveat,
    provenance.method,
    provenance.tier ? `tier: ${provenance.tier}` : null,
  ].filter(Boolean).join(' — ')

  return (
    <span
      className="provenance-chip"
      title={title}
      data-tier={provenance.tier || 'unknown'}
    >
      {label || 'Data provenance'}
    </span>
  )
}
