"""Observed history under the forecasts (frontend design pass, 2026-11-09).

Forecast charts draw the observed series the projection continues. These pin
the properties that make that honest:

* history is the sum of the same panel the engine forecasts, nothing else;
* an institution scope is applied before summing, so a UNIVERSITY caller's
  chart never contains another HEI's totals;
* grouped Model 2 forecasts keep one 90% range per target, never a sum of
  employment and vacancy bounds;
* an occupation grain carries vacancies only — employment has no occupation
  series to stand behind it.
"""
from __future__ import annotations

import numpy as np

from ml import forecasting as F
from ml.model2 import forecast as M2


def test_history_is_the_panel_summed_to_the_requested_dimensions():
    t = F.TARGETS["M1.applications"]
    p = F.panel(t)
    total = F.history("M1.applications")
    assert list(total.columns) == ["year", "value"]
    expected = p.groupby("year")["y"].sum()
    assert np.allclose(total.set_index("year")["value"], expected.loc[total["year"]])

    by_region = F.history("M1.applications", ("region",))
    assert set(by_region.columns) == {"region", "year", "value"}
    assert np.isclose(by_region["value"].sum(), p["y"].sum())


def test_history_scope_applies_before_summing():
    t = F.TARGETS["M1.applications"]
    p = F.panel(t)
    inst = p["institution"].iloc[0]
    scoped = F.history("M1.applications", ("program",), (("institution", inst),))
    assert np.isclose(scoped["value"].sum(), p.loc[p["institution"] == inst, "y"].sum())
    # Dimensions that are not series keys never invent a grouping.
    assert "academic_year" not in F.history("M1.applications", ("academic_year",)).columns


def test_grouped_model2_forecast_keeps_one_range_per_target():
    g = M2.group_forecast(M2.forecast_all(3), ["sector", "period"])
    for col in ("employment_demand", "vacancies"):
        lo, hi = f"{col}_low", f"{col}_high"
        assert lo in g.columns and hi in g.columns
        rows = g.dropna(subset=[col, lo, hi])
        assert len(rows) > 0
        assert (rows[lo] <= rows[col] + 1e-6).all()
        assert (rows[col] <= rows[hi] + 1e-6).all()
    # Employment and vacancy ranges are on different scales and stay apart.
    both = g.dropna(subset=["employment_demand_high", "vacancies_high"])
    assert (both["employment_demand_high"] > both["vacancies_high"]).all()
