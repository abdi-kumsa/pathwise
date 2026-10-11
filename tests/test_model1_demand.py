"""Wave 2.2 — unconstrained demand carries the five DOC1 dimensions."""
from __future__ import annotations

from ml.model1.layer1_demand import DIMENSIONS, forecast_unconstrained
from ml.model1.layer2_constraints import apply_constraints


def test_unconstrained_forecast_groups_on_the_five_dimensions():
    df = forecast_unconstrained(horizon=1)
    assert not df.empty
    for dim in DIMENSIONS:
        assert dim in df.columns, dim
    assert set(df["academic_year"].unique()) == {2026}
    assert df["interval_low"].le(df["unconstrained_demand"]).all()
    assert df["unconstrained_demand"].le(df["interval_high"]).all()


def test_constrained_is_at_or_below_unconstrained_on_generated_data():
    raw = forecast_unconstrained(horizon=1)
    out = apply_constraints(raw)
    assert (out["constrained_enrollment"] <= out["unconstrained_demand"] + 1e-6).all()
    assert out["binding_constraint"].notna().all()
    assert {"unconstrained_demand", "constrained_enrollment", "binding_constraint"} <= set(out.columns)


def test_layer1_estimators_are_scored_on_a_chronological_holdout():
    from ml.model1.compare import compare_estimators
    result = compare_estimators()
    assert result["n_holdout_rows"] > 0
    naive = result["estimators"]["seasonal_naive"]["rmse"]
    ols = result["estimators"]["ols_lags"]["rmse"]
    assert naive is not None and ols is not None
    assert naive >= 0 and ols >= 0
