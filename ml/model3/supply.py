"""
M3.1 — expected graduate supply.

Constrained enrollment (Wave 2) × latest observed completion rate (M1.C6).
This is the supply side of every DOC2 gap chart. Completion is applied as a
yield on the forecast intake year, not as a lagged graduating class — the
Ethiopia tables do not yet carry a true cohort-follow identifier.
"""
from __future__ import annotations

import pandas as pd

from ml.features.model1 import c6_cohort
from ml.model1.layer1_demand import forecast_unconstrained
from ml.model1.layer2_constraints import apply_constraints

DEFAULT_COMPLETION = 70.0


def _completion_lookup() -> pd.DataFrame:
    cohort = c6_cohort.frame()
    if cohort.empty:
        return pd.DataFrame(columns=["institution", "program", "region", "completion_rate_pct"])
    keys = [c for c in ("institution", "program", "region") if c in cohort.columns]
    latest = cohort.sort_values("year").groupby(keys, as_index=False, sort=False).last()
    keep = keys + [c for c in ("completion_rate_pct", "time_to_graduation_years", "field") if c in latest.columns]
    return latest[keep]


def graduate_supply(
    horizon: int = 1,
    constrained: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """One row per institution × campus × programme × forecast year."""
    enroll = constrained if constrained is not None else apply_constraints(
        forecast_unconstrained(horizon=horizon)
    )
    if enroll.empty:
        return enroll
    rates = _completion_lookup()
    keys = [c for c in ("institution", "program", "region") if c in enroll.columns and c in rates.columns]
    out = enroll.merge(rates, on=keys, how="left", suffixes=("", "_cohort"))
    completion = out.get("completion_rate_pct", pd.Series(DEFAULT_COMPLETION, index=out.index))
    completion = completion.fillna(DEFAULT_COMPLETION).clip(0, 100)
    out["completion_rate_pct"] = completion.round(1)
    out["expected_graduates"] = (
        out["constrained_enrollment"].astype(float) * completion / 100.0
    ).clip(lower=0).round(1)
    out["period"] = out["academic_year"]
    return out
