/**
 * What "accuracy" can honestly mean on this platform (plan item 2.13).
 *
 * Shown on every page that displays a Model 1–3 forecast. The figures come
 * from a seeded simulation, so backtest errors measure how well an estimator
 * recovers the simulator's own process, not how well it predicts Ethiopia.
 * The claims that do hold are about method: no leakage, selection by
 * backtest, skill against naive baselines, intervals with measured coverage.
 *
 * Rendered as one collapsed line. Pass the API's `accuracy` block to show the
 * per-horizon table (estimator chosen, error reduction, range coverage).
 */
export const ACCURACY_NOTE =
  'Forecast accuracy here is measured on simulated data: backtest errors show how well each ' +
  'method recovers the simulator, not how well it predicts Ethiopia. What holds is the method — ' +
  'each forecast uses whichever of four estimators had the lowest error on past years, and the ' +
  'shaded 90% range is checked against held-out years. Figures become ministry-grade only when ' +
  'the same backtest runs on official MoE / MoLS series.'

const ESTIMATOR = {
  seasonal_naive: 'last observed value',
  historical_mean: 'series mean',
  drift: 'drift',
  pooled_ridge: 'pooled ridge',
}

const TARGET_LABEL = {
  'M1.applications': 'Applications',
  'M2.employment_demand': 'Employment',
  'M2.vacancies': 'Vacancies',
  'M2.skill_shortages': 'Skill-shortage index',
}

// Metrics arrive as fractions (0.89). Guard against a percent already.
const pct = (v) => (v == null ? '—' : `${Math.round(Math.abs(v) <= 1.5 ? v * 100 : v)}%`)

export default function ForecastAccuracyNote({ accuracy }) {
  const blocks = !accuracy
    ? []
    : accuracy.by_horizon
      ? [accuracy]
      : Object.values(accuracy).filter(b => b && b.by_horizon)

  return (
    <details className="accuracy-note">
      <summary>Accuracy is measured against simulated data, not against Ethiopia.</summary>
      <p>{ACCURACY_NOTE}</p>
      {blocks.map(b => (
        <table key={b.target}>
          <thead>
            <tr>
              <th>{TARGET_LABEL[b.target] ?? b.target}</th>
              <th>Estimator chosen</th>
              <th>Error reduction vs last value</th>
              <th>90% range covered</th>
              <th>Backtests</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(b.by_horizon).map(([h, r]) => (
              <tr key={h}>
                <td>{h} {h === '1' ? 'year' : 'years'} ahead</td>
                <td>{ESTIMATOR[r.selected_model] ?? r.selected_model}</td>
                <td>{pct(r.skill_vs_naive)}</td>
                <td>{pct(r.interval_coverage)}</td>
                <td>{r.n_backtest ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ))}
    </details>
  )
}
