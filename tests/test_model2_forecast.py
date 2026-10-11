"""Wave 3.2–3.4 — Model 2 forecast targets, absorption shares, structural breaks."""
from __future__ import annotations

from ml.model2.forecast import DIMENSIONS, TARGETS, forecast_all, forecast_employment
from ml.model2.formal_informal import forecast_absorption
from ml.model2.skills import skills_shortage
from ml.model2.structural_breaks import annotate, park_openings


def test_forecast_emits_the_five_targets_and_four_dimensions():
    df = forecast_all(horizon=1)
    assert not df.empty
    for target in TARGETS:
        assert target in df.columns, target
    for dim in DIMENSIONS:
        assert dim in df.columns, dim
    assert set(df["period"].dropna().unique()) == {2026}


def test_employment_forecast_carries_break_attribution():
    emp = forecast_employment(horizon=1)
    assert "break_applied" in emp.columns
    assert "break_types" in emp.columns
    assert emp["employment_demand"].notna().all()
    assert (emp["employment_demand"] >= 0).all()


def test_absorption_shares_sum_to_one_and_are_not_from_job_boards():
    df = forecast_absorption(horizon=1)
    assert not df.empty
    share_cols = [
        "share_formal", "share_informal", "share_self_employment", "share_underemployment",
    ]
    summed = df[share_cols].sum(axis=1)
    assert ((summed - 1.0).abs() < 1e-6).all()
    assert df["not_from_job_board"].all()


def test_skills_map_onto_the_moe_programme_list():
    df = skills_shortage(horizon=1)
    assert df["program"].notna().all()
    assert df["field"].nunique() >= 8
    assert "net_pressure" in df.columns


def test_estimators_are_scored_on_a_chronological_holdout():
    from ml.model2.compare import compare_estimators
    result = compare_estimators()
    assert result["n_holdout_rows"] > 0
    naive = result["estimators"]["seasonal_naive"]["rmse"]
    ols = result["estimators"]["ols_lags"]["rmse"]
    assert naive is not None and ols is not None
    assert naive >= 0 and ols >= 0
    assert len(result["targets"]) == 5
    ids = [t["id"] for t in result["targets"]]
    assert ids == [
        "M2.employment_demand",
        "M2.employment_growth",
        "M2.vacancies",
        "M2.occupational_demand",
        "M2.skill_shortages",
    ]
    assert "occupational_demand_method" in result


def test_industrial_park_opening_is_a_named_structural_break():
    parks = park_openings()
    assert not parks.empty
    row = parks.iloc[0]
    info = annotate(row["region"], int(row["year"]))
    assert info["break_applied"] is True
    assert "industrial_park_opening" in info["break_types"]
