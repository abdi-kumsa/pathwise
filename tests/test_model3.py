"""Wave 4 — Model 3 alignment engine: supply, gap, recommendations, pathways, scenarios."""
from __future__ import annotations

from pathlib import Path

from ml.model3.gap import ALIGNMENT_WEIGHTS, alignment_score, supply_demand_gap
from ml.model3.pathways import pathway_graph
from ml.model3.recommend import STUDENT_WEIGHTS, institution_actions, policy_priority, student_alternatives
from ml.model3.scenario import run_scenario
from ml.model3.supply import graduate_supply


def test_graduate_supply_follows_the_cohort_that_entered_years_earlier():
    """Graduates in P = intake in P − time-to-graduation × completion rate."""
    df = graduate_supply(horizon=3)
    assert not df.empty
    assert (df["cohort_intake_year"] == df["period"] - df["time_to_graduation_years"]).all()
    known = df.dropna(subset=["cohort_intake"])
    expected = known["cohort_intake"] * known["completion_rate_pct"] / 100
    assert ((known["expected_graduates"] - expected).abs() <= 0.11).all()
    assert (df["expected_graduates"] >= 0).all()


def test_gap_uses_quartile_severity_not_fixed_thresholds():
    df = supply_demand_gap(horizon=1, group=("field", "period"))
    assert not df.empty
    assert set(df["status"]).issubset({"shortage", "balanced", "oversupply"})
    assert set(df["severity"].astype(int)).issubset({1, 2, 3, 4})
    scored = alignment_score(horizon=1)
    assert scored["weights"].iloc[0] == ALIGNMENT_WEIGHTS
    assert "method" in scored.columns
    assert scored["factors"].iloc[0]
    assert "fit" not in str(scored["factors"].iloc[0]).lower()


def test_student_alternatives_rank_on_real_signal_not_fit():
    df = student_alternatives(horizon=1)
    assert not df.empty
    factors = {f["factor"] for f in df["factors"].iloc[0]}
    assert factors == set(STUDENT_WEIGHTS)
    text = "".join(p.read_text(encoding="utf-8") for p in Path("ml/model3").glob("*.py"))
    assert "placement_status" not in text
    assert "Undereducated" not in text
    assert "Overeducated" not in text
    health = institution_actions(horizon=1)
    assert "action" in health.columns
    assert health["fit_classification_used"].eq(False).all()
    policy = policy_priority(horizon=1)
    assert {"labour_shortage", "national_priority", "student_demand", "feasibility"} <= set(
        {f["factor"] for f in policy["factors"].iloc[0]}
    )


def test_pathway_graph_links_programmes_to_occupations():
    graph = pathway_graph()
    assert graph["programs"]
    assert graph["occupations"]
    assert graph["edges"]
    types = {e["source_type"] for e in graph["edges"]} | {e["target_type"] for e in graph["edges"]}
    assert {"program", "occupation"} <= types


def test_scenario_is_unofficial_and_records_assumptions():
    out = run_scenario(quota_scale=1.5, horizon=1)
    assert out["official_forecast"] is False
    assert out["assumptions"]["quota_scale"] == 1.5
    assert "levers" in out["assumptions"]
    assert set(out["delta"]) == {
        "unconstrained_demand", "constrained_enrollment", "expected_graduates",
    }
