"""Wave 2 — inspectable constraint layer (M1.L2)."""
from __future__ import annotations

import pandas as pd

from ml.model1.layer2_constraints import (
    CONSTRAINT_ORDER,
    NATURAL_SHARE,
    apply_constraints,
    explain_rules,
)


def test_rule_order_matches_the_documents():
    rules = explain_rules()
    assert rules["learned"] is False
    assert rules["inspectable"] is True
    assert rules["order"] == list(CONSTRAINT_ORDER)
    assert rules["band_directive"]["natural_science"] == NATURAL_SHARE


def test_suspension_zeros_demand_and_binds():
    demand = pd.DataFrame({
        "institution": ["A"], "campus": ["Main"], "region": ["Addis Ababa"],
        "program": ["LLB Law"], "field": ["Law"], "band": ["Social science"],
        "academic_year": [2026], "unconstrained_demand": [400.0],
    })
    quota = pd.DataFrame({
        "institution": ["A"], "campus": ["Main"], "region": ["Addis Ababa"],
        "program": ["LLB Law"], "field": ["Law"], "year": [2025],
        "approved_intake_quota": [500], "available_seats": [500],
        "program_capacity": [500], "program_suspension_flag": [True],
        "strategic_priority_flag": [False],
    })
    exam = pd.DataFrame({
        "field": ["Law"], "year": [2025],
        "exam_pass_rate_pct": [80.0], "band_allocation_ratio": [0.30],
    })
    out = apply_constraints(demand, quota=quota, exam=exam)
    assert float(out["constrained_enrollment"].iloc[0]) == 0.0
    assert out["binding_constraint"].iloc[0] == "program_suspension"


def test_quota_is_the_binding_cap_when_it_is_tightest():
    demand = pd.DataFrame({
        "institution": ["A", "B"], "campus": ["Main", "Main"],
        "region": ["Addis Ababa", "Oromia"],
        "program": ["BSc Civil Engineering", "BA Accounting"],
        "field": ["Engineering & Technology", "Business & Economics"],
        "band": ["Natural science", "Social science"],
        "academic_year": [2026, 2026],
        "unconstrained_demand": [400.0, 400.0],
    })
    quota = pd.DataFrame({
        "institution": ["A", "B"], "campus": ["Main", "Main"],
        "region": ["Addis Ababa", "Oromia"],
        "program": ["BSc Civil Engineering", "BA Accounting"],
        "field": ["Engineering & Technology", "Business & Economics"],
        "year": [2025, 2025],
        "approved_intake_quota": [120, 500],
        "available_seats": [300, 500],
        "program_capacity": [350, 500],
        "program_suspension_flag": [False, False],
        "strategic_priority_flag": [True, False],
    })
    exam = pd.DataFrame({
        "field": ["Engineering & Technology", "Business & Economics"],
        "year": [2025, 2025],
        "exam_pass_rate_pct": [100.0, 100.0],
        "band_allocation_ratio": [0.70, 0.30],
    })
    out = apply_constraints(demand, quota=quota, exam=exam)
    eng = out[out["program"] == "BSc Civil Engineering"].iloc[0]
    assert float(eng["constrained_enrollment"]) == 120.0
    assert eng["binding_constraint"] == "approved_intake_quota"
    assert float(eng["constraint_loss"]) == 280.0


def test_constrained_never_exceeds_unconstrained():
    demand = pd.DataFrame({
        "institution": ["A", "B"], "campus": ["Main", "Main"],
        "region": ["Addis Ababa", "Oromia"],
        "program": ["BSc Civil Engineering", "BA Accounting"],
        "field": ["Engineering & Technology", "Business & Economics"],
        "band": ["Natural science", "Social science"],
        "academic_year": [2026, 2026],
        "unconstrained_demand": [200.0, 200.0],
    })
    quota = pd.DataFrame({
        "institution": ["A", "B"], "campus": ["Main", "Main"],
        "region": ["Addis Ababa", "Oromia"],
        "program": ["BSc Civil Engineering", "BA Accounting"],
        "field": ["Engineering & Technology", "Business & Economics"],
        "year": [2025, 2025],
        "approved_intake_quota": [500, 500],
        "available_seats": [500, 500],
        "program_capacity": [500, 500],
        "program_suspension_flag": [False, False],
        "strategic_priority_flag": [True, False],
    })
    exam = pd.DataFrame({
        "field": ["Engineering & Technology", "Business & Economics"],
        "year": [2025, 2025],
        "exam_pass_rate_pct": [90.0, 90.0],
        "band_allocation_ratio": [0.70, 0.30],
    })
    out = apply_constraints(demand, quota=quota, exam=exam)
    assert (out["constrained_enrollment"] <= out["unconstrained_demand"] + 1e-6).all()
    assert set(out["binding_constraint"]).issubset(set(CONSTRAINT_ORDER) | {"none"})


def test_band_directive_caps_natural_science_at_70_percent():
    demand = pd.DataFrame({
        "institution": ["A", "B"], "campus": ["Main", "Main"],
        "region": ["Addis Ababa", "Oromia"],
        "program": ["BSc Civil Engineering", "BA Accounting"],
        "field": ["Engineering & Technology", "Business & Economics"],
        "band": ["Natural science", "Social science"],
        "academic_year": [2026, 2026],
        "unconstrained_demand": [900.0, 100.0],
    })
    quota = pd.DataFrame({
        "institution": ["A", "B"], "campus": ["Main", "Main"],
        "region": ["Addis Ababa", "Oromia"],
        "program": ["BSc Civil Engineering", "BA Accounting"],
        "field": ["Engineering & Technology", "Business & Economics"],
        "year": [2025, 2025],
        "approved_intake_quota": [5000, 5000],
        "available_seats": [5000, 5000],
        "program_capacity": [5000, 5000],
        "program_suspension_flag": [False, False],
        "strategic_priority_flag": [True, False],
    })
    exam = pd.DataFrame({
        "field": ["Engineering & Technology", "Business & Economics"],
        "year": [2025, 2025],
        "exam_pass_rate_pct": [100.0, 100.0],
        "band_allocation_ratio": [0.70, 0.30],
    })
    out = apply_constraints(demand, quota=quota, exam=exam)
    nat = float(out.loc[out["band"] == "Natural science", "constrained_enrollment"].sum())
    total = float(out["constrained_enrollment"].sum())
    assert nat / total <= NATURAL_SHARE + 1e-6
    assert (out.loc[out["band"] == "Natural science", "binding_constraint"] == "band_allocation").all()


def test_cutoff_binds_when_mean_is_below_the_programme_cutoff():
    demand = pd.DataFrame({
        "institution": ["A"], "campus": ["Main"], "region": ["Addis Ababa"],
        "program": ["MD Medicine"], "field": ["Medicine & Health Sciences"],
        "band": ["Natural science"], "academic_year": [2026],
        "unconstrained_demand": [200.0],
    })
    quota = pd.DataFrame({
        "institution": ["A"], "campus": ["Main"], "region": ["Addis Ababa"],
        "program": ["MD Medicine"], "field": ["Medicine & Health Sciences"],
        "year": [2025], "approved_intake_quota": [500], "available_seats": [500],
        "program_capacity": [500], "program_suspension_flag": [False],
        "strategic_priority_flag": [True],
    })
    exam = pd.DataFrame({
        "field": ["Medicine & Health Sciences"], "year": [2025],
        "exam_pass_rate_pct": [100.0], "band_allocation_ratio": [0.70],
        "exam_score_mean": [40.0], "program_cutoff_score": [80.0],
    })
    out = apply_constraints(demand, quota=quota, exam=exam)
    assert float(out["constrained_enrollment"].iloc[0]) == 100.0
    assert out["binding_constraint"].iloc[0] == "entrance_exam_cutoff"
