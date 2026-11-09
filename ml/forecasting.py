"""
Shared forecasting engine for the Ethiopia Model 1 and Model 2 targets.

Replaces per-series OLS-on-lags (5 parameters fitted to 6 rows per series,
selected by name rather than by error, intervals of width zero). For every
target the engine:

1. Builds a panel of series (keys x year x y).
2. Scores four candidates on a rolling-origin backtest — every origin year
   from ORIGIN_START to the second-last observed year, every horizon that
   still has an observed target. No random split; nothing after the origin is
   ever seen by a candidate.

       seasonal_naive   last observed value
       historical_mean  mean of the series up to the origin
       drift            the series' own linear trend, extrapolated
       pooled_ridge     one model shared by every series of the target:
                        predicts the change from the last value from (a) the
                        latest change and (b) the distance of the last value
                        from the series' own mean. Captures persistence and
                        mean reversion without a parameter per series.

3. Selects, per horizon, the candidate with the lowest backtest RMSE. The
   choice is a measured fact recorded on every forecast row, not a name.
4. Builds prediction intervals from that candidate's backtest residuals at
   that horizon (empirical 5th / 95th percentiles), and reports their
   coverage measured leave-one-origin-out, so the stated 90% is checked
   rather than assumed. An interval is never narrower than the residuals
   observed in the backtest, and never zero.

Positive count targets are modelled in logs; bounded indices (0-1) on their
own scale and clipped to the bounds.

All results are memoised (ml/_memo.py); inputs change only when a parquet is
replaced.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from ml._memo import memo

CANDIDATES = ("seasonal_naive", "historical_mean", "drift", "pooled_ridge")
BASELINES = ("seasonal_naive", "historical_mean")
ORIGIN_START = 2019          # first origin: at least four history years
MAX_HORIZON = 5
INTERVAL_LEVEL = 0.90
_Q_LO, _Q_HI = (1 - INTERVAL_LEVEL) / 2, 1 - (1 - INTERVAL_LEVEL) / 2
_MIN_HISTORY = 3             # observations a series needs at the origin
_RIDGE_ALPHA = 1.0
_EPS = 1e-6


@dataclass(frozen=True)
class Target:
    id: str
    label: str
    keys: tuple[str, ...]
    ycol: str
    frame: Callable[[], pd.DataFrame]
    log: bool = True
    lower: float | None = 0.0
    upper: float | None = None
    carry: tuple[str, ...] = ()      # descriptive columns copied onto forecasts


# ── transforms ────────────────────────────────────────────────────────────────

def _fwd(y: np.ndarray, t: Target) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    return np.log(np.maximum(y, _EPS)) if t.log else y


def _inv(z: np.ndarray | float, t: Target) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    y = np.exp(z) if t.log else z
    lo = -np.inf if t.lower is None else t.lower
    hi = np.inf if t.upper is None else t.upper
    return np.clip(y, lo, hi)


# ── panel ─────────────────────────────────────────────────────────────────────

def panel(t: Target) -> pd.DataFrame:
    """keys + year + y, one row per series-year, sorted, no missing target."""
    df = t.frame()
    cols = [c for c in (*t.keys, *t.carry) if c in df.columns]
    out = df[[*cols, "year", t.ycol]].rename(columns={t.ycol: "y"})
    out = out.dropna(subset=["y"])
    out = out.drop_duplicates(subset=[*t.keys, "year"])
    return out.sort_values([*t.keys, "year"]).reset_index(drop=True)


def _series(p: pd.DataFrame, t: Target):
    for key, s in p.groupby(list(t.keys), sort=False):
        key = key if isinstance(key, tuple) else (key,)
        yield key, s["year"].to_numpy(dtype=int), s["y"].to_numpy(dtype=float), s


def observed(df: pd.DataFrame, ycol: str, keys, dimensions=(), where=()) -> pd.DataFrame:
    """Sum an observed column to `dimensions` + year.

    `where` is (column, value) pairs applied before summing, so an institution
    scope holds even when the result is not grouped by institution. Dimensions
    that are not series keys are ignored rather than inventing a grouping.
    """
    out = df.dropna(subset=[ycol])
    for col, val in tuple(where or ()):
        if col in out.columns:
            out = out[out[col] == val]
    dims = [d for d in (dimensions or ()) if d in keys and d in out.columns]
    out = out.groupby([*dims, "year"], as_index=False)[ycol].sum()
    return (out.rename(columns={ycol: "value"})
               .sort_values([*dims, "year"]).reset_index(drop=True))


@memo
def history(target_id: str, dimensions=(), where=()) -> pd.DataFrame:
    """The observed series a forecast continues, summed to `dimensions`.

    Forecast charts draw this under the forecast so the reader sees what the
    projection extends, not three floating points.
    """
    t = TARGETS[target_id]
    return observed(panel(t), "y", t.keys, tuple(dimensions or ()), tuple(where or ()))


# ── candidates ────────────────────────────────────────────────────────────────

def _features(z: np.ndarray) -> np.ndarray:
    """Pooled-model inputs at the last point of z (needs len(z) >= 2)."""
    return np.array([z[-1] - z[-2], z[-1] - z.mean()])


FEATURE_NAMES = ("latest_change", "distance_from_series_mean")


def _fit_pooled(p: pd.DataFrame, t: Target, cutoff: int, horizons) -> dict[int, Ridge]:
    """One ridge per horizon on every (series, origin<=cutoff-h) pair."""
    X = {h: [] for h in horizons}
    Y = {h: [] for h in horizons}
    for _, years, y, _ in _series(p, t):
        z = _fwd(y, t)
        for i in range(_MIN_HISTORY - 1, len(years)):
            for h in horizons:
                j = i + h
                if j >= len(years) or years[j] > cutoff or years[j] - years[i] != h:
                    continue
                X[h].append(_features(z[: i + 1]))
                Y[h].append(z[j] - z[i])
    models = {}
    for h in horizons:
        if len(Y[h]) >= 10:
            models[h] = Ridge(alpha=_RIDGE_ALPHA).fit(np.array(X[h]), np.array(Y[h]))
    return models


def _predict_all(z: np.ndarray, years: np.ndarray, h: int, pooled: dict) -> dict[str, float]:
    """Every candidate's forecast of z at years[-1] + h, in transform space."""
    out = {
        "seasonal_naive": float(z[-1]),
        "historical_mean": float(z.mean()),
    }
    if len(z) >= 3:
        slope, intercept = np.polyfit(years.astype(float), z, 1)
        out["drift"] = float(intercept + slope * (years[-1] + h))
    else:
        out["drift"] = float(z[-1])
    model = pooled.get(h)
    # Too few training pairs at this horizon: the pooled model is unavailable,
    # and is left out rather than silently standing in for the naive forecast.
    if model is not None:
        out["pooled_ridge"] = float(z[-1] + model.predict(_features(z).reshape(1, -1))[0])
    return out


# ── backtest ──────────────────────────────────────────────────────────────────

@memo
def backtest(target_id: str) -> pd.DataFrame:
    """Rolling-origin backtest. One row per series x origin x horizon x candidate."""
    t = TARGETS[target_id]
    p = panel(t)
    last = int(p["year"].max())
    horizons = tuple(range(1, MAX_HORIZON + 1))
    rows = []
    for origin in range(ORIGIN_START, last):
        pooled = _fit_pooled(p, t, origin, horizons)
        for key, years, y, _ in _series(p, t):
            mask = years <= origin
            if mask.sum() < _MIN_HISTORY:
                continue
            hy, hz = years[mask], _fwd(y[mask], t)
            for h in horizons:
                hit = np.where(years == origin + h)[0]
                if not len(hit):
                    continue
                actual = float(y[hit[0]])
                actual_z = float(_fwd(np.array([actual]), t)[0])
                for cand, pred_z in _predict_all(hz, hy, h, pooled).items():
                    rows.append({
                        "series": key, "origin": origin, "horizon": h, "candidate": cand,
                        "actual": actual, "pred": float(_inv(pred_z, t)),
                        "resid_z": actual_z - pred_z,
                    })
    return pd.DataFrame(rows)


def _metrics(bt: pd.DataFrame) -> pd.DataFrame:
    err = bt["actual"] - bt["pred"]
    denom = bt["actual"].abs().where(bt["actual"].abs() > _EPS)
    g = bt.assign(sq=err ** 2, ab=err.abs(), ape=(err.abs() / denom) * 100)
    out = g.groupby(["candidate", "horizon"]).agg(
        rmse=("sq", lambda s: float(np.sqrt(s.mean()))),
        mae=("ab", "mean"),
        mape=("ape", "mean"),
        n=("sq", "size"),
        origins=("origin", "nunique"),
    ).reset_index()
    return out


def _coverage(bt: pd.DataFrame) -> pd.DataFrame:
    """Leave-one-origin-out empirical coverage of the 90% interval."""
    rows = []
    for (cand, h), g in bt.groupby(["candidate", "horizon"]):
        hits, total = 0, 0
        for origin, held in g.groupby("origin"):
            rest = g[g["origin"] != origin]["resid_z"]
            if len(rest) < 10:
                continue
            lo, hi = np.quantile(rest, [_Q_LO, _Q_HI])
            inside = (held["resid_z"] >= lo) & (held["resid_z"] <= hi)
            hits += int(inside.sum())
            total += len(held)
        rows.append({
            "candidate": cand, "horizon": h,
            "coverage": round(hits / total, 3) if total else None,
            "coverage_n": total,
        })
    return pd.DataFrame(rows)


@memo
def evaluation(target_id: str) -> dict:
    """Backtest metrics, per-horizon selection, interval quantiles, coverage."""
    bt = backtest(target_id)
    if bt.empty:
        return {"target": target_id, "metrics": [], "selected": {}, "quantiles": {}}
    m = _metrics(bt).merge(_coverage(bt), on=["candidate", "horizon"], how="left")
    selected, quantiles = {}, {}
    # Ties go to the simpler candidate, in the order CANDIDATES lists them.
    simplicity = {c: i for i, c in enumerate(CANDIDATES)}
    for h, g in m.groupby("horizon"):
        g = g.assign(_simple=g["candidate"].map(simplicity))
        best = g.sort_values(["rmse", "_simple"]).iloc[0]
        selected[int(h)] = str(best["candidate"])
    for (cand, h), g in bt.groupby(["candidate", "horizon"]):
        q = np.quantile(g["resid_z"], [_Q_LO, _Q_HI])
        quantiles[(str(cand), int(h))] = (float(q[0]), float(q[1]))
    naive = m[m["candidate"] == "seasonal_naive"].set_index("horizon")["rmse"]
    m["skill_vs_naive"] = [
        round(1 - r / naive[h], 3) if naive.get(h) else None
        for r, h in zip(m["rmse"], m["horizon"])
    ]
    m = m.round(4)
    # JSON has no NaN: an undefined metric (e.g. MAPE with a zero actual) is null.
    records = [
        {k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in row.items()}
        for row in m.to_dict(orient="records")
    ]
    return {
        "target": target_id,
        "metrics": records,
        "selected": selected,
        "quantiles": quantiles,
    }


# ── forecast ──────────────────────────────────────────────────────────────────

def _selection(ev: dict, h: int) -> tuple[str, tuple[float, float]]:
    sel = ev["selected"]
    hh = h if h in sel else max(sel) if sel else h
    cand = sel.get(hh, "seasonal_naive")
    q = ev["quantiles"].get((cand, hh))
    if q is None:
        q = (-0.25, 0.25) if TARGETS[ev["target"]].log else (-0.1, 0.1)
    return cand, q


@memo
def forecast(target_id: str, horizon: int = 3) -> pd.DataFrame:
    """Forecast every series `horizon` years past its last observation."""
    t = TARGETS[target_id]
    p = panel(t)
    origin = int(p["year"].max())
    horizons = tuple(range(1, max(horizon, 1) + 1))
    pooled = _fit_pooled(p, t, origin, horizons)
    ev = evaluation(target_id)
    rows = []
    for key, years, y, s in _series(p, t):
        if len(years) < _MIN_HISTORY or years[-1] != origin:
            continue
        z = _fwd(y, t)
        carry = {c: s[c].iloc[-1] for c in t.carry if c in s.columns}
        for h in horizons:
            preds = _predict_all(z, years, h, pooled)
            cand, (qlo, qhi) = _selection(ev, h)
            if cand not in preds:      # selected candidate unavailable at this horizon
                cand, (qlo, qhi) = "seasonal_naive", ev["quantiles"].get(("seasonal_naive", h), (qlo, qhi))
            point_z = preds[cand]
            rows.append({
                **dict(zip(t.keys, key)), **carry,
                "year": origin + h,
                "horizon_step": h,
                "last_observed": float(y[-1]),
                "point": round(float(_inv(point_z, t)), 4),
                "interval_low": round(float(_inv(point_z + qlo, t)), 4),
                "interval_high": round(float(_inv(point_z + qhi, t)), 4),
                "interval_level": INTERVAL_LEVEL,
                "selected_model": cand,
                **{c: (round(float(_inv(preds[c], t)), 4) if c in preds else None)
                   for c in CANDIDATES},
            })
    return pd.DataFrame(rows)


def comparison(target_id: str) -> dict:
    """PROC.S4 payload for one target: metrics by candidate and horizon."""
    t = TARGETS[target_id]
    ev = evaluation(target_id)
    metrics = ev["metrics"]
    by_h = {}
    for row in metrics:
        by_h.setdefault(int(row["horizon"]), {})[row["candidate"]] = {
            k: row.get(k) for k in ("rmse", "mae", "mape", "n", "origins",
                                    "coverage", "coverage_n", "skill_vs_naive")
        }
    h1 = by_h.get(1, {})
    bt = backtest(target_id)
    return {
        "id": t.id,
        "label": t.label,
        "target": t.ycol,
        "scale": "log" if t.log else "level",
        "candidates": list(CANDIDATES),
        "baselines": list(BASELINES),
        "split": (
            f"rolling origin {ORIGIN_START}–{int(bt['origin'].max()) if not bt.empty else '?'}, "
            f"horizons 1–{MAX_HORIZON}; a candidate never sees data after its origin"
        ),
        "n_holdout_rows": int(len(bt[bt["candidate"] == "seasonal_naive"])) if not bt.empty else 0,
        "estimators": {c: {"rmse": (h1.get(c) or {}).get("rmse"), "mae": (h1.get(c) or {}).get("mae")}
                       for c in CANDIDATES},
        "by_horizon": {str(h): v for h, v in sorted(by_h.items())},
        "selected_by_horizon": {str(h): c for h, c in sorted(ev["selected"].items())},
        "selected_for_request_path": (
            "lowest backtest RMSE at each horizon: "
            + ", ".join(f"h{h} {c}" for h, c in sorted(ev["selected"].items()))
        ),
        "interval": {
            "level": INTERVAL_LEVEL,
            "method": "empirical 5th/95th percentile of the selected candidate's backtest residuals",
            "coverage_method": "leave-one-origin-out",
        },
    }


ACCURACY_NOTE = (
    "Accuracy is measured on simulated data: backtest errors show how well each "
    "estimator recovers the simulator's process, not how well it predicts Ethiopia. "
    "What holds is the method: no leakage, the lowest-error candidate chosen per "
    "horizon, skill reported against naive baselines, and 90% intervals whose "
    "coverage is checked on held-out years. Errors become ministry-relevant only "
    "when the same backtest runs on official MoE / MoLS series."
)


def accuracy_summary(target_id: str) -> dict:
    """Compact, quotable accuracy block attached to forecast responses."""
    ev = evaluation(target_id)
    by = {(r["candidate"], int(r["horizon"])): r for r in ev["metrics"]}
    horizons = {}
    for h, cand in sorted(ev["selected"].items()):
        r = by.get((cand, h), {})
        horizons[str(h)] = {
            "selected_model": cand,
            "rmse": r.get("rmse"),
            "skill_vs_naive": r.get("skill_vs_naive"),
            "interval_coverage": r.get("coverage"),
            "n_backtest": r.get("n"),
        }
    return {
        "target": target_id,
        "interval_level": INTERVAL_LEVEL,
        "by_horizon": horizons,
        "data_tier": "simulated",
        "note": ACCURACY_NOTE,
    }


def pooled_pairs(target_id: str, horizon: int = 1) -> pd.DataFrame:
    """The pooled model's training pairs for one horizon, with the target year.

    Used for post-training importance (PROC.S5): fit on early years, explain on
    later ones, exactly as the backtest does.
    """
    t = TARGETS[target_id]
    p = panel(t)
    rows = []
    for key, years, y, _ in _series(p, t):
        z = _fwd(y, t)
        for i in range(_MIN_HISTORY - 1, len(years) - horizon):
            j = i + horizon
            if years[j] - years[i] != horizon:
                continue
            f = _features(z[: i + 1])
            rows.append({
                "series": key, "origin": int(years[i]), "target_year": int(years[j]),
                FEATURE_NAMES[0]: f[0], FEATURE_NAMES[1]: f[1], "change": z[j] - z[i],
            })
    return pd.DataFrame(rows)


# ── targets ───────────────────────────────────────────────────────────────────

def _m1_applications() -> pd.DataFrame:
    from ml.features.model1 import c1_enrollment, c2_funnel
    hist = c1_enrollment.frame()
    funnel = c2_funnel.frame()
    keys = [c for c in ("institution", "campus", "region", "program", "field", "year")
            if c in hist.columns and c in funnel.columns]
    out = funnel.merge(hist[[*keys, *(c for c in ("band",) if c in hist.columns)]],
                       on=keys, how="left")
    return out


def _m2_employment() -> pd.DataFrame:
    from ml.features.model2 import c1_labour
    return c1_labour.frame()


def _m2_vacancies() -> pd.DataFrame:
    from ml.features.model2 import c4_vacancies
    return c4_vacancies.frame()


def _m2_skills() -> pd.DataFrame:
    from ml.features.model2 import c5_skills
    return c5_skills.frame()


TARGETS: dict[str, Target] = {
    "M1.applications": Target(
        id="M1.applications",
        label="Unconstrained student demand (applications) by HEI × programme",
        keys=("institution", "campus", "region", "program"),
        ycol="applications_count",
        frame=_m1_applications,
        carry=("field", "band"),
    ),
    "M2.employment_demand": Target(
        id="M2.employment_demand",
        label="Employment level by region × sector",
        keys=("region", "sector"),
        ycol="employment_level",
        frame=_m2_employment,
    ),
    "M2.vacancies": Target(
        id="M2.vacancies",
        label="Vacancies by region × occupation",
        keys=("region", "occupation"),
        ycol="vacancy_count",
        frame=_m2_vacancies,
        carry=("sector", "field"),
    ),
    "M2.skill_shortages": Target(
        id="M2.skill_shortages",
        label="Skill-shortage index by field (0–1)",
        keys=("field",),
        ycol="skill_shortage_index",
        frame=_m2_skills,
        log=False,
        lower=0.0,
        upper=1.0,
    ),
}
