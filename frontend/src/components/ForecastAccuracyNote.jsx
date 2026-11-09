import DataNote from './DataNote'

/**
 * What "accuracy" can honestly mean on this platform (plan item 2.13).
 *
 * Shown on every page that displays a Model 1–3 forecast. The figures come
 * from a seeded simulation, so backtest errors measure how well an estimator
 * recovers the simulator's own process — not how well it predicts Ethiopia.
 * The claims that do hold are about method: no leakage, selection by
 * backtest, skill against naive baselines, intervals with measured coverage.
 */
export const ACCURACY_NOTE =
  'Forecast accuracy here is measured on simulated data: backtest errors show how well each ' +
  'method recovers the simulator, not how well it predicts Ethiopia. What holds is the method — ' +
  'each forecast uses whichever of four estimators had the lowest error on past years, and the ' +
  'shaded 90% range is checked against held-out years. Figures become ministry-grade only when ' +
  'the same backtest runs on official MoE / MoLS series.'

export default function ForecastAccuracyNote() {
  return <DataNote tone="simulated">{ACCURACY_NOTE}</DataNote>
}
