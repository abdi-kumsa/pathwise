/**
 * Page title with an optional one-line subtitle.
 *
 * The subtitle should add information (scope, period, unit), not restate the
 * title. `showLiveIndicator` is kept for the leftover US-model pages, which
 * render a plain note instead of a live-status dot: nothing there is live.
 */
export default function SectionHeader({ title, subtitle, showLiveIndicator = false }) {
  const sub = showLiveIndicator ? 'Leftover US dataset, not live' : subtitle
  return (
    <div className="page-header">
      <h1 className="page-title">{title}</h1>
      {sub && <p className="page-subtitle">{sub}</p>}
    </div>
  )
}
