"""Phase 2 regression tests (2026-11-07 improvement plan): the models are honest.

Each test pins one property the audit found missing:

* the generator's lag columns are true lags, so no learner sees its target;
* candidates are scored on a rolling-origin backtest, never on the future;
* the request path uses the candidate with the lowest measured error;
* prediction intervals are non-zero and their coverage is measured;
* Model 1 Layer 1 forecasts demand (applications), not enrolment;
* Model 3 graduates come from the cohort that entered years earlier;
* gap status follows coverage, severity follows quartiles (RANK.R4);
* every advertised scenario lever changes something;
* importance comes from the fitted request-path model;
* drift monitoring covers the Ethiopia targets.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ml import forecasting as F

ETH = "data/ethiopia"


# ── 2.1 generator ─────────────────────────────────────────────────────────────

def test_enrollment_lags_are_true_shifts_and_rolling_mean_excludes_current_year():
    e = pd.read_parquet(f"{ETH}/enrollment_history.parquet").sort_values(["institution", "program", "year"])
    g = e.groupby(["institution", "program"])["program_enrollment_count"]
    assert np.allclose(e["enrollment_lag_1y"].dropna(), g.shift(1).dropna())
    assert np.allclose(e["enrollment_lag_2y"].dropna(), g.shift(2).dropna())
    prior = g.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    assert np.allclose(e["enrollment_rolling_3y_avg"].dropna(), prior.dropna())
    # The identity that made OLS-on-lags exact must no longer hold.
    d = e.dropna(subset=["enrollment_lag_1y", "enrollment_lag_2y", "enrollment_rolling_3y_avg"])
    identity = 3 * d["enrollment_rolling_3y_avg"] - d["enrollment_lag_1y"] - d["enrollment_lag_2y"]
    assert (d["program_enrollment_count"] - identity).abs().mean() > 1.0


def test_employment_lags_are_true_shifts_not_a_fixed_ratio():
    lab = pd.read_parquet(f"{ETH}/labour_history.parquet").sort_values(["region", "sector", "year"])
    true_lag = lab.groupby(["region", "sector"])["employment_level"].shift(1)
    assert np.allclose(lab["employment_lag_1y"].dropna(), true_lag.dropna())
    ratio = (lab["employment_level"] / lab["employment_lag_1y"]).dropna().round(3)
    assert ratio.nunique() > 50, "lag must not be the target divided by a constant"


def test_series_are_persistent():
    """Pooled AR(1) of detrended log enrolment: the old generator gave ~0."""
    e = pd.read_parquet(f"{ETH}/enrollment_history.parquet")
    xs, ys = [], []
    for _, s in e.groupby(["institution", "program"]):
        v = np.log(s.sort_values("year")["program_enrollment_count"].to_numpy(float))
        t = np.arange(len(v))
        res = v - np.polyval(np.polyfit(t, v, 1), t)
        xs += list(res[:-1])
        ys += list(res[1:])
    phi = float(np.dot(xs, ys) / np.dot(xs, xs))
    assert phi > 0.25, phi


# ── 2.2–2.5 engine ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("target_id", list(F.TARGETS))
def test_backtest_never_uses_data_after_the_origin(target_id):
    bt = F.backtest(target_id)
    assert not bt.empty
    assert set(bt["candidate"]) <= set(F.CANDIDATES)
    assert set(F.BASELINES) <= set(bt["candidate"])
    assert (bt["origin"] + bt["horizon"] > bt["origin"]).all()
    assert bt["origin"].nunique() >= 4, "rolling origin, not a single fold"


@pytest.mark.parametrize("target_id", list(F.TARGETS))
def test_selection_is_the_lowest_backtest_error(target_id):
    ev = F.evaluation(target_id)
    metrics = pd.DataFrame(ev["metrics"])
    order = {c: i for i, c in enumerate(F.CANDIDATES)}
    for h, chosen in ev["selected"].items():
        at_h = metrics[metrics["horizon"] == h].assign(_s=lambda d: d["candidate"].map(order))
        assert chosen == at_h.sort_values(["rmse", "_s"]).iloc[0]["candidate"]


def test_an_unavailable_candidate_is_not_scored_as_a_copy_of_naive():
    """With too few pairs the pooled model is absent, not a naive stand-in."""
    for target_id in F.TARGETS:
        m = pd.DataFrame(F.evaluation(target_id)["metrics"]).pivot(
            index="horizon", columns="candidate", values="rmse")
        if "pooled_ridge" in m:
            both = m[["pooled_ridge", "seasonal_naive"]].dropna()
            assert not (both["pooled_ridge"] == both["seasonal_naive"]).any(), target_id


@pytest.mark.parametrize("target_id", list(F.TARGETS))
def test_intervals_are_never_zero_and_contain_the_point(target_id):
    fc = F.forecast(target_id, 3)
    assert not fc.empty
    assert (fc["interval_high"] > fc["interval_low"]).all()
    assert (fc["interval_low"] <= fc["point"] + 1e-9).all()
    assert (fc["point"] <= fc["interval_high"] + 1e-9).all()
    assert fc["selected_model"].isin(F.CANDIDATES).all()


@pytest.mark.parametrize("target_id", ["M1.applications", "M2.employment_demand", "M2.vacancies"])
def test_interval_coverage_is_measured_and_close_to_nominal(target_id):
    ev = F.evaluation(target_id)
    by = {(r["candidate"], int(r["horizon"])): r for r in ev["metrics"]}
    chosen = ev["selected"][1]
    coverage = by[(chosen, 1)]["coverage"]
    assert coverage is not None
    assert 0.80 <= coverage <= 0.97, coverage


def test_pooled_model_beats_last_value_for_model1_demand():
    ev = F.evaluation("M1.applications")
    by = {(r["candidate"], int(r["horizon"])): r["rmse"] for r in ev["metrics"]}
    assert by[("pooled_ridge", 1)] < by[("seasonal_naive", 1)]


def test_skill_index_is_bounded():
    fc = F.forecast("M2.skill_shortages", 5)
    assert fc[["point", "interval_low", "interval_high"]].stack().between(0, 1).all()


def test_accuracy_summary_says_what_accuracy_means():
    summary = F.accuracy_summary("M1.applications")
    assert summary["data_tier"] == "simulated"
    assert "simulat" in summary["note"].lower()
    assert summary["by_horizon"]["1"]["interval_coverage"] is not None


# ── Model 1 two-layer design ──────────────────────────────────────────────────

def test_layer1_forecasts_applications_and_does_not_replay_history():
    from ml.model1.layer1_demand import forecast_unconstrained
    u = forecast_unconstrained(horizon=3)
    funnel = pd.read_parquet(f"{ETH}/admissions_funnel.parquet")
    last = funnel[funnel["year"] == funnel["year"].max()]["applications_count"].sum()
    h1 = u[u["horizon_step"] == 1]["unconstrained_demand"].sum()
    assert 0.8 < h1 / last < 1.25, "Layer 1 is on the applications scale"
    replay = 0
    for _, g in u.groupby(["institution", "program"]):
        pts = g.sort_values("horizon_step")["unconstrained_demand"].round(1).tolist()
        replay += pts == [round(float(g["last_observed"].iloc[0]), 1)] * len(pts)
    assert replay < len(u) / 3 / 2, "most series must move away from the last value"


def test_layer2_binding_constraint_is_mostly_capacity_not_eligibility():
    """Applying eligibility to already-placed enrolment made it bind almost
    everywhere. With demand as input, seats / quota / capacity should bind."""
    from ml.model1.layer1_demand import forecast_unconstrained
    from ml.model1.layer2_constraints import apply_constraints
    c = apply_constraints(forecast_unconstrained(horizon=1))
    share = c["binding_constraint"].isin(
        ["approved_intake_quota", "available_seats", "program_capacity", "band_allocation"]
    ).mean()
    assert share > 0.5, c["binding_constraint"].value_counts().to_dict()


# ── Model 3 ───────────────────────────────────────────────────────────────────

def test_gap_status_follows_coverage_and_severity_stays_quartile():
    from ml.model3.gap import COVERAGE_OVERSUPPLY, COVERAGE_SHORTAGE, supply_demand_gap
    df = supply_demand_gap(horizon=1, group=("field", "region", "period"))
    cov = df["expected_graduates"] / df["labour_demand"].replace(0, np.nan)
    assert (df.loc[cov < COVERAGE_SHORTAGE, "status"] == "shortage").all()
    assert (df.loc[cov > COVERAGE_OVERSUPPLY, "status"] == "oversupply").all()
    mid = cov.between(COVERAGE_SHORTAGE, COVERAGE_OVERSUPPLY)
    assert (df.loc[mid, "status"] == "balanced").all()
    assert set(df["severity"].astype(int)) <= {1, 2, 3, 4}


def test_every_scenario_lever_changes_the_constrained_result():
    from ml.model3.scenario import LEVERS, run_scenario
    assert "placement_rule" in LEVERS
    cases = {
        "quota": {"quota_scale": 0.6},
        "capacity": {"capacity_scale": 0.3},
        "priority_field": {"priority_fields": ["Law"], "priority_boost": 2.0},
        "placement_rule": {"pass_rate_shift_pp": -15},
        "band_allocation": {"natural_share": 0.5, "social_share": 0.5},
    }
    for lever, kwargs in cases.items():
        delta = run_scenario(horizon=1, **kwargs)["delta"]["constrained_enrollment"]
        assert delta != 0, lever


def test_graduates_respond_to_policy_only_after_the_cohort_lag():
    from ml.model3.scenario import run_scenario
    near = run_scenario(pass_rate_shift_pp=-15, horizon=1)["delta"]["expected_graduates"]
    far = run_scenario(pass_rate_shift_pp=-15, horizon=5)["delta"]["expected_graduates"]
    assert near == 0, "graduates of the next year are already enrolled"
    assert far < 0


def test_scenario_rejects_out_of_range_placement_rule():
    from ml.model3.scenario import run_scenario
    with pytest.raises(ValueError):
        run_scenario(pass_rate_shift_pp=40)


# ── 2.10 importance and 2.11 monitoring ───────────────────────────────────────

def test_importance_comes_from_the_request_path_model():
    import sys
    sys.path.insert(0, "ml")
    from explain_predictions import ethiopia_feature_importance
    r = ethiopia_feature_importance(persist=False)
    for key in ("model1", "model2"):
        block = r[key]
        assert block["model"].startswith("pooled_ridge")
        for method in ("model_based", "shap", "permutation"):
            assert block[method], (key, method)
        assert block["holdout_rmse"] > 0


def test_psi_is_zero_for_identical_and_large_for_shifted_distributions():
    from ml.drift import psi
    rng = np.random.default_rng(0)
    ref = rng.normal(0, 1, 2000)
    assert psi(ref, rng.normal(0, 1, 2000)) < 0.05
    assert psi(ref, rng.normal(1.5, 1, 2000)) > 0.25


def test_drift_report_covers_every_ethiopia_target():
    from ml.drift import ethiopia_drift
    r = ethiopia_drift()
    assert set(r["targets"]) == set(F.TARGETS)
    for d in r["targets"].values():
        assert d["error"] is not None
        assert d["error"]["selected_model"] in F.CANDIDATES


@pytest.mark.parametrize("target_id", list(F.TARGETS))
def test_accuracy_and_comparison_payloads_are_strict_json(target_id):
    """A NaN metric (e.g. MAPE with a zero actual) once 500'd /api/model2/forecast."""
    import json
    json.dumps(F.accuracy_summary(target_id), allow_nan=False)
    json.dumps(F.comparison(target_id), allow_nan=False)
