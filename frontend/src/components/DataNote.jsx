/**
 * A visible provenance / caveat line.
 *
 * Exists because some figures in this app are honest but easy to over-read:
 * most importantly the graduate fit classification, which is near-uniform
 * across fields and must not be presented as a ranking. Where the API returns
 * `comparable: false` and a `caveat`, the page shows it here rather than
 * leaving the limitation in a docstring the reader will never see.
 *
 * Rendered as one quiet line with a small tag, not a coloured banner: the
 * caveat must be readable, but the figures are what the page is for.
 */
const TAGS = { simulated: 'Simulated', caution: 'Check', info: null }

export default function DataNote({ children, tone = 'info' }) {
  const tag = TAGS[tone] ?? null
  return (
    <p className={`data-note data-note-${tone}`} role={tone === 'caution' ? 'status' : undefined}>
      {tag && <span className="data-note-tag">{tag}</span>}
      <span>{children}</span>
    </p>
  )
}
