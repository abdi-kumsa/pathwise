"""
M3.1 — expected graduate supply.

A graduating class in year P entered in year P − L, where L is the programme's
time to graduation (M1.C6, ~4–5 years), and graduates at the programme's
completion rate:

    expected_graduates(P) = intake(P − L) × completion_rate

The intake comes from observed enrolment when P − L is in the past, and from
the Layer 2 constrained forecast when it is in the future. With L ≈ 4, the
graduates of the next few years are already enrolled, so a quota change acts
on graduate supply only after L years. Earlier waves multiplied the *same*
year's forecast intake by the completion rate, which counted first-years as
graduates and made policy levers move supply instantly.

`constrained_enrollment` on each row is the period's forecast intake (new
entrants in P), kept because the gap and three-way views show it alongside
graduates.
"""
from __future__ import annotations

import pandas as pd

from ml._memo import memo
from ml.features.model1 import c1_enrollment, c6_cohort
from ml.model1.layer1_demand import forecast_unconstrained
from ml.model1.layer2_constraints import apply_constraints

DEFAULT_COMPLETION = 70.0
DEFAULT_YEARS_TO_GRADUATE = 4
_KEYS = ["institution", "campus", "region", "program"]


def _completion_lookup() -> pd.DataFrame:
    cohort = c6_cohort.frame()
    if cohort.empty:
        return pd.DataFrame(columns=["institution", "program", "region",
                                     "completion_rate_pct", "time_to_graduation_years"])
    keys = [c for c in ("institution", "program", "region") if c in cohort.columns]
    latest = cohort.sort_values("year").groupby(keys, as_index=False, sort=False).last()
    keep = keys + [c for c in ("completion_rate_pct", "time_to_graduation_years", "field")
                   if c in latest.columns]
    return latest[keep]


def _observed_intake() -> pd.DataFrame:
    hist = c1_enrollment.frame()
    cols = [c for c in (*_KEYS, "field", "band", "year", "program_enrollment_count") if c in hist.columns]
    return hist[cols].rename(columns={"program_enrollment_count": "intake"})


def _years_to_graduate(value) -> int:
    try:
        return max(3, int(round(float(value))))
    except (TypeError, ValueError):
        return DEFAULT_YEARS_TO_GRADUATE


def _supply(horizon: int, constrained: pd.DataFrame) -> pd.DataFrame:
    observed = _observed_intake()
    origin = int(observed["year"].max())
    rates = _completion_lookup()

    forecast_intake = constrained.rename(columns={"academic_year": "year"})
    intake_lookup: dict[tuple, tuple[float, str]] = {}
    for r in observed.itertuples(index=False):
        intake_lookup[(r.institution, r.campus, r.region, r.program, int(r.year))] = (
            float(r.intake), "observed")
    for r in forecast_intake.itertuples(index=False):
        intake_lookup[(r.institution, r.campus, r.region, r.program, int(r.year))] = (
            float(r.constrained_enrollment), "forecast")

    rate_cols = [c for c in ("completion_rate_pct", "time_to_graduation_years") if c in rates.columns]
    series = observed[observed["year"] == origin][[*(c for c in (*_KEYS, "field", "band") if c in observed.columns)]]
    series = series.merge(rates[["institution", "program", "region", *rate_cols]],
                          on=["institution", "program", "region"], how="left")

    period_intake = {
        (r.institution, r.campus, r.region, r.program, int(r.year)): float(r.constrained_enrollment)
        for r in forecast_intake.itertuples(index=False)
    }
    rows = []
    for r in series.itertuples(index=False):
        completion = getattr(r, "completion_rate_pct", None)
        completion = DEFAULT_COMPLETION if pd.isna(completion) else min(max(float(completion), 0.0), 100.0)
        # Round first so a reader can recompute graduates from the published rate.
        completion = round(completion, 1)
        lag = _years_to_graduate(getattr(r, "time_to_graduation_years", None))
        for step in range(1, horizon + 1):
            period = origin + step
            cohort_year = period - lag
            key = (r.institution, r.campus, r.region, r.program)
            intake, source = intake_lookup.get((*key, cohort_year), (None, "missing"))
            graduates = 0.0 if intake is None else max(intake * completion / 100.0, 0.0)
            rows.append({
                "institution": r.institution, "campus": r.campus, "region": r.region,
                "program": r.program, "field": getattr(r, "field", None),
                "band": getattr(r, "band", None),
                "academic_year": period, "period": period, "horizon_step": step,
                "constrained_enrollment": round(period_intake.get((*key, period), 0.0), 1),
                "cohort_intake_year": cohort_year,
                "cohort_intake": None if intake is None else round(intake, 1),
                "cohort_intake_source": source,
                "completion_rate_pct": round(completion, 1),
                "time_to_graduation_years": lag,
                "expected_graduates": round(graduates, 1),
            })
    return pd.DataFrame(rows)


@memo
def _baseline_supply(horizon: int) -> pd.DataFrame:
    return _supply(horizon, apply_constraints(forecast_unconstrained(horizon=horizon)))


def graduate_supply(
    horizon: int = 1,
    constrained: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """One row per institution × campus × programme × forecast year.

    `constrained` lets the scenario engine supply its own Layer 2 output; its
    intake reaches graduates only for cohorts that enter after the origin.
    """
    if constrained is None:
        return _baseline_supply(horizon)
    if constrained.empty:
        return constrained
    h = int(constrained["academic_year"].max()) - int(_observed_intake()["year"].max())
    return _supply(max(h, 1), constrained)
