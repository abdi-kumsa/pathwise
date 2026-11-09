#!/usr/bin/env python3
"""
Wave 1.2 — simulated Ethiopian fact tables for every DOC1 attribute.

    python data/ethiopia/generate.py
    python data/ethiopia/generate.py --validate

Seeded, deterministic, 2016–2025. Structure is Ethiopian (regions, HEIs, MoE
bands, ETB, ESSLCE, industrial parks). Magnitudes are simulated and must never
be presented as official MoE / MoLS / ESS statistics.

Time-series design (Phase 2 of the 2026-11-07 improvement plan):

* Every forecast target is a persistent process: a series-specific level and
  trend times exp(AR(1) deviation), so this year carries information about
  next year. The previous generator drew each year independently, which left
  nothing for a lag model to learn.
* Every lag column is a true lag of the published series (`shift`). Rolling
  means cover the *previous* years only. The previous generator computed
  `enrollment_rolling_3y_avg` including the current year and set
  `employment_lag_1y = employment / 1.02`, both of which leaked the target.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
_REF = Path(__file__).resolve().parent / "reference"
if str(_REF) not in sys.path:
    sys.path.insert(0, str(_REF))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dimensions import (  # noqa: E402
    FIELDS, HEIS, INDUSTRIAL_PARKS, REGIONS, SECTORS, YEARS,
    esslce_pass_uplift, shock_factor,
)

OUT = Path(__file__).resolve().parent
RNG = np.random.default_rng(42)
PROVENANCE = "simulated"


def _write(name: str, df: pd.DataFrame) -> None:
    df = df.copy()
    df["provenance"] = PROVENANCE
    path = OUT / f"{name}.parquet"
    df.to_parquet(path, index=False)
    df.to_csv(OUT / f"{name}.csv", index=False)
    print(f"  {name:28s} {len(df):5d} rows  {len(df.columns):3d} cols")


def _ar1(n: int, phi: float, sigma: float) -> np.ndarray:
    """Stationary AR(1) deviations: u_t = phi * u_(t-1) + e_t."""
    u = np.empty(n)
    u[0] = RNG.normal(0, sigma / np.sqrt(1 - phi ** 2))
    for t in range(1, n):
        u[t] = phi * u[t - 1] + RNG.normal(0, sigma)
    return u


# Persistence of each simulated series. Chosen so year-on-year variation is of
# the same size as before (enrolment CV ~ 0.16) but autocorrelated.
# Stationary spread is sigma / sqrt(1 - phi^2): ~0.16 for enrolment, ~0.10 for
# employment, ~0.20 for vacancies.
ENROL_PHI, ENROL_SIGMA = 0.85, 0.084
EMP_PHI, EMP_SIGMA = 0.85, 0.05
VAC_PHI, VAC_SIGMA = 0.75, 0.13
SKILL_PHI, SKILL_SIGMA = 0.75, 0.065


def _base_panel() -> list[dict]:
    rows = []
    for hei in HEIS:
        for field in FIELDS:
            base = max(80.0, RNG.normal(220, 35))
            slope = 0.025 + RNG.normal(0, 0.01) + (0.01 if field["band"] == "Natural science" else 0)
            dev = _ar1(len(YEARS), ENROL_PHI, ENROL_SIGMA)
            for i, year in enumerate(YEARS):
                shock = shock_factor(hei["region"], year)
                trend = 1.0 + slope * (year - 2016)
                enrol = int(max(40, base * trend * shock * np.exp(dev[i])))
                rows.append({
                    "institution": hei["name"],
                    "institution_type": hei["type"],
                    "generation": hei["generation"],
                    "campus": hei["campus"],
                    "region": hei["region"],
                    "program": field["program"],
                    "field": field["field"],
                    "band": field["band"],
                    "stem": field["stem"],
                    "occupation": field["occupation"],
                    "sector": field["sector"],
                    "year": year,
                    "enrollment": enrol,
                })
    return rows


def build_enrollment_history(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    df = df.sort_values(["institution", "program", "year"])
    g = df.groupby(["institution", "program"], sort=False)["enrollment"]
    df["program_enrollment_count"] = df["enrollment"]
    df["enrollment_lag_1y"] = g.shift(1)
    df["enrollment_lag_2y"] = g.shift(2)
    # Rolling means of the *previous* years: knowable before year t is observed.
    df["enrollment_rolling_3y_avg"] = g.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    df["enrollment_rolling_5y_avg"] = g.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    # Observed growth *into* year t. Describes the year; never a learner input.
    df["enrollment_growth_rate_pct"] = g.pct_change() * 100
    campus = df.groupby(["institution", "campus", "year"])["enrollment"].transform("sum")
    region = df.groupby(["region", "year"])["enrollment"].transform("sum")
    df["campus_enrollment_count"] = campus
    df["region_enrollment_count"] = region
    return df.drop(columns=["enrollment"])


def build_admissions_funnel(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "campus", "region", "program", "field", "year",
               "program_enrollment_count"]].copy()
    seats = (df["program_enrollment_count"] * RNG.uniform(0.95, 1.15, len(df))).astype(int)
    # Applicants per place is a property of the programme, so it is drawn once
    # per series. Applications then inherit the persistence of enrolment.
    ratio = df.groupby(["institution", "program"])["year"].transform(
        lambda s: RNG.uniform(1.8, 3.0)
    )
    apps = (df["program_enrollment_count"] * ratio
            * np.exp(RNG.normal(0, 0.06, len(df)))).astype(int)
    offers = np.minimum(apps, (seats * RNG.uniform(0.9, 1.05, len(df))).astype(int))
    accepted = np.minimum(offers, df["program_enrollment_count"].astype(int))
    df["applications_count"] = apps
    df["offers_count"] = offers
    df["accepted_offers_count"] = accepted
    df["yield_rate_pct"] = np.where(offers > 0, accepted / offers * 100, 0)
    df["applicants_per_seat"] = np.where(seats > 0, apps / seats, 0)
    df["first_choice_demand_count"] = (apps * RNG.uniform(0.35, 0.6, len(df))).astype(int)
    return df.drop(columns=["program_enrollment_count"])


def build_exam_placement(hist: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for year in YEARS:
        for field in FIELDS:
            base_pass = 48.0 + esslce_pass_uplift(year) + (4 if field["stem"] else 0)
            pass_rate = float(np.clip(base_pass + RNG.normal(0, 2.2), 30, 85))
            candidates = int(RNG.normal(18000 if field["stem"] else 14000, 1500))
            mean = 52 + esslce_pass_uplift(year) * 0.4 + RNG.normal(0, 1.5)
            rows.append({
                "year": year, "field": field["field"], "band": field["band"],
                "exam_candidates_count": candidates,
                "exam_pass_rate_pct": pass_rate,
                "exam_score_mean": mean,
                "exam_score_sd": 11.5,
                "exam_score_p25": mean - 8,
                "exam_score_p50": mean,
                "exam_score_p75": mean + 8,
                "program_cutoff_score": mean + (6 if field["stem"] else 2),
                "placed_count": int(candidates * pass_rate / 100 * 0.72),
                "placement_rate_pct": pass_rate * 0.72,
                "field_allocation_count": int(candidates * pass_rate / 100 * 0.72),
                "band_allocation_ratio": 0.70 if field["band"] == "Natural science" else 0.30,
            })
    return pd.DataFrame(rows)


def build_capacity_quota(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "campus", "region", "program", "field", "band", "year",
               "program_enrollment_count"]].copy()
    quota = (df["program_enrollment_count"] * RNG.uniform(0.92, 1.08, len(df))).astype(int)
    df["approved_intake_quota"] = quota
    df["available_seats"] = (quota * RNG.uniform(0.88, 1.0, len(df))).astype(int)
    df["program_capacity"] = (quota * RNG.uniform(1.05, 1.25, len(df))).astype(int)
    df["program_expansion_flag"] = (df["year"] >= 2022) & (df["band"] == "Natural science")
    df["program_suspension_flag"] = False
    df["strategic_priority_flag"] = df["band"] == "Natural science"
    return df.drop(columns=["program_enrollment_count", "band"])


def build_demographics() -> pd.DataFrame:
    rows = []
    for region in REGIONS:
        pop = 4_200_000 if region["name"] == "Oromia" else (1_200_000 if region["type"] == "city" else 2_400_000)
        for year in YEARS:
            shock = shock_factor(region["name"], year)
            youth = int(pop * 0.22 * (1 + 0.022 * (year - 2016)) * shock)
            rows.append({
                "region": region["name"], "year": year,
                "grade12_completers_count": int(youth * 0.045),
                "university_age_population": youth,
                "regional_youth_population": int(youth * 1.35),
                "net_internal_migration": int(RNG.normal(0, 8000) + (12000 if region["name"] == "Addis Ababa" else -1500)),
            })
    return pd.DataFrame(rows)


def build_cohort(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "program", "field", "region", "year"]].copy()
    retain = np.clip(RNG.normal(82, 4, len(df)), 60, 96)
    # Dropout and transfer split what retention leaves, so the three rates
    # never sum past 100% (the remainder is students who stop out). Drawing
    # them independently, as before, broke that in ~60% of rows — caught by
    # rule C.COHORT.SUM in ml/consistency.py.
    remainder = 100 - retain
    drop = remainder * RNG.uniform(0.45, 0.65, len(df))      # shares sum to at most 0.95
    transfer = remainder * RNG.uniform(0.15, 0.30, len(df))
    df["retention_rate_pct"] = retain
    df["dropout_rate_pct"] = drop
    df["transfer_rate_pct"] = transfer
    df["completion_rate_pct"] = np.clip(retain - 8, 50, 90)
    df["time_to_graduation_years"] = np.clip(RNG.normal(4.3, 0.35, len(df)), 3.5, 6.5)
    return df


def build_outcomes(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "program", "field", "region", "year"]].copy()
    emp = np.clip(RNG.normal(61, 8, len(df)), 25, 90)
    df["graduate_employment_rate_pct"] = emp
    df["graduate_unemployment_rate_pct"] = np.clip(100 - emp - 12, 4, 50)
    df["median_earnings_etb"] = (RNG.normal(9200, 1800, len(df)) * 12).astype(int)
    df["vacancy_demand_by_field"] = RNG.integers(80, 900, len(df))
    df["skills_shortage_signal"] = np.clip((70 - emp) / 10, -2, 3)
    return df


def build_institution_capacity(hist: pd.DataFrame) -> pd.DataFrame:
    keys = hist[["institution", "campus", "region", "program", "year"]].drop_duplicates()
    df = keys.copy()
    df["faculty_student_ratio"] = np.clip(RNG.normal(18, 4, len(df)), 8, 40)
    df["laboratory_count"] = RNG.integers(2, 18, len(df))
    df["classroom_count"] = RNG.integers(12, 80, len(df))
    df["accreditation_status"] = np.where(RNG.random(len(df)) > 0.12, "accredited", "probation")
    df["program_quality_index"] = np.clip(RNG.normal(0.62, 0.12, len(df)), 0.2, 0.95)
    return df


def build_finance(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "program", "field", "year"]].copy()
    public = df["institution"].map(lambda n: next(h["type"] for h in HEIS if h["name"] == n))
    fee = np.where(public == "public", RNG.integers(800, 2500, len(df)), RNG.integers(25000, 80000, len(df)))
    df["tuition_fee_etb"] = fee
    df["stipend_etb"] = np.where(public == "public", RNG.integers(0, 4000, len(df)), 0)
    df["scholarship_availability"] = RNG.uniform(0.05, 0.35, len(df))
    df["cost_sharing_loan_etb"] = np.where(public == "public", (fee * 0.8).astype(int), 0)
    return df


def build_macro_regional() -> pd.DataFrame:
    rows = []
    for region in REGIONS:
        for year in YEARS:
            infl = 12 + (year - 2016) * 1.1 + RNG.normal(0, 1.4)
            rows.append({
                "region": region["name"], "year": year,
                "inflation_rate_pct": infl,
                "household_income_proxy_etb": int(18000 * (1 + 0.07 * (year - 2016)) * shock_factor(region["name"], year)),
                "youth_unemployment_rate_pct": float(np.clip(22 + RNG.normal(0, 3), 10, 45)),
                "regional_socioeconomic_index": float(np.clip(0.45 + RNG.normal(0, 0.08), 0.15, 0.85)),
            })
    return pd.DataFrame(rows)


def build_labour_history() -> pd.DataFrame:
    rows = []
    for region in REGIONS:
        for sector in SECTORS:
            base = 40_000 * RNG.uniform(0.7, 1.3)
            dev = _ar1(len(YEARS), EMP_PHI, EMP_SIGMA)
            for i, year in enumerate(YEARS):
                shock = shock_factor(region["name"], year)
                park_boost = 1.0
                for park in INDUSTRIAL_PARKS:
                    if park["region"] == region["name"] and year >= park["opened"] and sector == "Manufacturing":
                        park_boost += 0.18
                emp = int(base * shock * park_boost * (1 + 0.02 * (year - 2016)) * np.exp(dev[i]))
                rows.append({
                    "region": region["name"], "sector": sector, "year": year,
                    "employment_level": emp,
                    "unemployment_rate_pct": float(np.clip(17 + RNG.normal(0, 2), 6, 35)),
                    "youth_unemployment_rate_pct": float(np.clip(24 + RNG.normal(0, 3), 10, 50)),
                    "sector_employment": emp,
                    "job_creation_count": int(emp * 0.04),
                    "labour_force_participation_pct": float(np.clip(78 + RNG.normal(0, 2), 60, 90)),
                })
    df = pd.DataFrame(rows).sort_values(["region", "sector", "year"])
    g = df.groupby(["region", "sector"], sort=False)["employment_level"]
    # True lags and observed growth — previously employment / 1.02 and / 1.05,
    # which made the "lag" a same-year function of the target.
    df["employment_lag_1y"] = g.shift(1)
    df["employment_lag_2y"] = g.shift(2)
    df["employment_growth_pct"] = g.pct_change() * 100
    return df.reset_index(drop=True)


def build_sector_output(labour: pd.DataFrame) -> pd.DataFrame:
    df = labour[["region", "sector", "year", "employment_level"]].copy()
    df["sector_value_added_etb"] = (df["employment_level"] * RNG.uniform(18000, 42000, len(df))).astype(int)
    df["sector_growth_rate_pct"] = RNG.normal(4.2, 2.1, len(df))
    df["sector_output_index"] = 100 * (1 + 0.03 * (df["year"] - 2016))
    df["business_formation_count"] = RNG.integers(40, 400, len(df))
    df["sector_investment_etb"] = (df["sector_value_added_etb"] * 0.12).astype(int)
    df["employment_intensity"] = df["employment_level"] / (df["sector_value_added_etb"] / 1_000_000)
    return df.drop(columns=["employment_level"])


def build_formal_informal(labour: pd.DataFrame) -> pd.DataFrame:
    df = labour[["region", "sector", "year", "employment_level"]].copy()
    agri = df["sector"] == "Agriculture"
    formal_share = np.where(agri, 0.18, 0.42)
    df["formal_wage_employment"] = (df["employment_level"] * formal_share).astype(int)
    df["informal_employment"] = (df["employment_level"] * (0.55 if True else 0) * np.where(agri, 1.1, 0.7)).astype(int)
    df["self_employment"] = (df["employment_level"] * 0.22).astype(int)
    df["underemployment"] = (df["employment_level"] * 0.14).astype(int)
    df["microenterprise_activity"] = RNG.integers(200, 5000, len(df))
    df["sector_absorption_rate"] = np.clip(formal_share + RNG.normal(0, 0.05, len(df)), 0.05, 0.9)
    return df.drop(columns=["employment_level"])


def build_vacancies(hist: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for field in FIELDS:
        for region in REGIONS:
            base = max(60.0, RNG.normal(180, 40))
            dev = _ar1(len(YEARS), VAC_PHI, VAC_SIGMA)
            for i, year in enumerate(YEARS):
                trend = 1 + 0.03 * (year - 2016)
                vac = int(max(10, base * trend * shock_factor(region["name"], year) * np.exp(dev[i])))
                rows.append({
                    "region": region["name"], "year": year,
                    "occupation": field["occupation"],
                    "occupation_frequency": vac,
                    "vacancy_count": vac,
                    "required_education": "bachelor",
                    "required_experience_years": int(RNG.integers(0, 5)),
                    "hiring_trend_pct": float(RNG.normal(3.0, 2.5)),
                    "time_to_fill_days": float(np.clip(RNG.normal(48, 12), 14, 120)),
                    "sector": field["sector"],
                    "field": field["field"],
                })
    return pd.DataFrame(rows)


def build_skills() -> pd.DataFrame:
    rows = []
    for field in FIELDS:
        mu = float(np.clip(RNG.normal(0.35, 0.08), 0.1, 0.7))
        shortage = mu
        for year in YEARS:
            shortage = float(np.clip(mu + SKILL_PHI * (shortage - mu) + RNG.normal(0, SKILL_SIGMA), 0, 1))
            rows.append({
                "field": field["field"], "year": year,
                "technical_skill_demand": float(np.clip(RNG.normal(0.7 if field["stem"] else 0.45, 0.1), 0.1, 1)),
                "digital_skill_demand": float(np.clip(RNG.normal(0.65, 0.12), 0.1, 1)),
                "soft_skill_demand": float(np.clip(RNG.normal(0.6, 0.08), 0.2, 1)),
                "emerging_skill_demand": float(np.clip(RNG.normal(0.4 + 0.03 * (year - 2016), 0.1), 0.05, 1)),
                "skill_shortage_index": shortage,
                "skill_oversupply_index": float(np.clip(RNG.normal(0.2, 0.1), 0, 1)),
            })
    return pd.DataFrame(rows)


def build_public_hiring() -> pd.DataFrame:
    rows = []
    for region in REGIONS:
        for year in YEARS:
            freeze = year in (2020, 2021)
            rows.append({
                "region": region["name"], "year": year,
                "civil_service_hiring_plan": int(RNG.integers(200, 4000) * (0.4 if freeze else 1)),
                "hiring_policy_state": "freeze" if freeze else "expansion",
                "public_project_count": int(RNG.integers(2, 18)),
                "megaproject_staffing_demand": int(RNG.integers(50, 2500)),
            })
    return pd.DataFrame(rows)


def build_fdi() -> pd.DataFrame:
    rows = []
    for park in INDUSTRIAL_PARKS:
        for year in YEARS:
            open_ = year >= park["opened"]
            rows.append({
                "region": park["region"], "year": year,
                "industrial_park": park["name"],
                "industrial_park_operational_flag": open_,
                "fdi_inflow_usd": int((40_000_000 if open_ else 4_000_000) * RNG.uniform(0.6, 1.4)),
                "new_investment_project_count": int(RNG.integers(1, 12) if open_ else 0),
                "factory_expansion_count": int(RNG.integers(0, 6) if open_ else 0),
                "expected_employment": int(RNG.integers(400, 8000) if open_ else 0),
                "private_investment_pipeline_etb": int(RNG.integers(20_000_000, 400_000_000) if open_ else 0),
            })
    return pd.DataFrame(rows)


def build_macro_financial() -> pd.DataFrame:
    rows = []
    for year in YEARS:
        rows.append({
            "year": year,
            "gdp_growth_rate_pct": float(6.2 - 0.15 * (year - 2016) + RNG.normal(0, 0.8)),
            "cpi_index": 100 * (1.14 ** (year - 2016)),
            "inflation_rate_pct": float(12 + 1.2 * (year - 2016) + RNG.normal(0, 1.5)),
            "exchange_rate_etb_usd": float(22 + 4.5 * (year - 2016)),
            "forex_reserve_months": float(np.clip(3.8 - 0.15 * (year - 2016) + RNG.normal(0, 0.3), 1.2, 6)),
            "gross_investment_etb": int(180_000_000_000 * (1.06 ** (year - 2016))),
            "interest_rate_pct": float(12 + 0.4 * (year - 2016)),
        })
    return pd.DataFrame(rows)


def build_labour_demographics() -> pd.DataFrame:
    rows = []
    for region in REGIONS:
        for year in YEARS:
            shock = shock_factor(region["name"], year)
            rows.append({
                "region": region["name"], "year": year,
                "working_age_population": int(1_100_000 * shock * (1.02 ** (year - 2016))),
                "education_level_distribution": "mixed",
                "skilled_emigration_count": int(RNG.integers(200, 4000)),
                "return_migration_count": int(RNG.integers(80, 1200)),
                "regional_absorption_rate": float(np.clip(RNG.normal(0.48, 0.1), 0.15, 0.85)),
            })
    return pd.DataFrame(rows)


def build_shocks() -> pd.DataFrame:
    rows = []
    for region in REGIONS:
        for year in YEARS:
            rows.append({
                "region": region["name"], "year": year,
                "agricultural_season": "meher" if year % 2 == 0 else "belg",
                "hiring_season_index": float(0.6 + 0.2 * np.sin(year)),
                "commodity_price_index": float(100 * (1.06 ** (year - 2016)) * RNG.uniform(0.9, 1.1)),
                "external_shock_flag": bool(region["tigray_shock"] and year in (2021, 2022)) or year == 2020,
            })
    return pd.DataFrame(rows)


def build_jobs_compat(vacancies: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """Column shape the existing labour dashboards already read."""
    grad = outcomes.groupby(["field", "year"])["vacancy_demand_by_field"].mean()
    rows = []
    rid = 0
    for r in vacancies.itertuples(index=False):
        rid += 1
        grads = int(grad.get((r.field, r.year), 200))
        rows.append({
            "record_id": rid, "year": r.year, "month": 6, "quarter": 2,
            "job_title": r.occupation, "job_family": r.field,
            "soc_code": f"ETH-{abs(int.from_bytes(r.occupation.encode(), 'little')) % 1000:03d}",
            "skill_cluster": r.field, "country": "Ethiopia",
            "state_province": r.region, "metro_area": r.region,
            "remote_allowed": False, "posting_industry": r.sector,
            "relevant_graduates_count": grads,
            "bootcamp_completions": int(grads * 0.08),
            "supply_demand_ratio": grads / max(r.vacancy_count, 1),
            "time_to_fill_days": r.time_to_fill_days,
            "job_openings_count": r.vacancy_count,
            "demand_growth_rate_pct": r.hiring_trend_pct,
            "avg_salary_usd": 9200 * 12,
            "avg_salary_etb": 9200 * 12,
            "company_size": "medium",
        })
    return pd.DataFrame(rows)


def build_enrollment_compat(hist: pd.DataFrame, funnel: pd.DataFrame, finance: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    m = hist.merge(funnel, on=["institution", "campus", "region", "program", "field", "year"], how="left")
    m = m.merge(finance, on=["institution", "program", "field", "year"], how="left")
    m = m.merge(outcomes, on=["institution", "program", "field", "region", "year"], how="left")
    stem = {f["program"]: f["stem"] for f in FIELDS}
    out = pd.DataFrame({
        "year": m["year"],
        "program_name": m["program"],
        "field_of_study": m["field"],
        "stem_designated": m["program"].map(stem).astype(int),
        "accreditation_status": "accredited",
        "institution_name": m["institution"],
        "institution_type": m["institution"].map(lambda n: next(h["type"] for h in HEIS if h["name"] == n)),
        "institution_state": m["region"],
        "campus_setting": m["campus"],
        "tuition_usd": m["tuition_fee_etb"],
        "tuition_etb": m["tuition_fee_etb"],
        "net_price": m["tuition_fee_etb"] * 0.7,
        "scholarship_availability": m["scholarship_availability"],
        "roi_10yr_usd": m["median_earnings_etb"] * 8,
        "employment_rate_6mo_pct": m["graduate_employment_rate_pct"],
        "enrollment_count": m["program_enrollment_count"],
        "applications_count": m["applications_count"],
        "acceptance_rate_pct": np.where(m["applications_count"] > 0, m["offers_count"] / m["applications_count"] * 100, 0),
        "yield_rate_pct": m["yield_rate_pct"],
        "us_news_ranking": 0,
        "program_level": "bachelor",
        "delivery_mode": "in-person",
        "inquiry_count": (m["applications_count"] * 1.4).astype(int),
        "marketing_spend_usd": (m["program_enrollment_count"] * 120).astype(int),
        "competitor_programs_count": 7,
        "competitor_avg_tuition_usd": m["tuition_fee_etb"] * 1.05,
        "median_salary_field_usd": m["median_earnings_etb"],
    })
    return out


def write_reference() -> None:
    ref = OUT / "reference"
    ref.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(REGIONS).to_csv(ref / "regions.csv", index=False)
    pd.DataFrame(HEIS).to_csv(ref / "heis.csv", index=False)
    pd.DataFrame(FIELDS).to_csv(ref / "fields.csv", index=False)
    pd.DataFrame(INDUSTRIAL_PARKS).to_csv(ref / "industrial_parks.csv", index=False)
    print("  reference dimensions written")


def generate() -> dict[str, pd.DataFrame]:
    print("Generating Ethiopia fact tables (simulated, 2016–2025)")
    write_reference()
    panel = pd.DataFrame(_base_panel())
    hist = build_enrollment_history(panel)
    funnel = build_admissions_funnel(hist)
    exam = build_exam_placement(hist)
    quota = build_capacity_quota(hist)
    demo = build_demographics()
    cohort = build_cohort(hist)
    outcomes = build_outcomes(hist)
    icap = build_institution_capacity(hist)
    finance = build_finance(hist)
    macro_r = build_macro_regional()
    labour = build_labour_history()
    sector = build_sector_output(labour)
    formal = build_formal_informal(labour)
    vac = build_vacancies(hist)
    skills = build_skills()
    public = build_public_hiring()
    fdi = build_fdi()
    macro_f = build_macro_financial()
    lab_dem = build_labour_demographics()
    shocks = build_shocks()
    jobs = build_jobs_compat(vac, outcomes)
    enrol_c = build_enrollment_compat(hist, funnel, finance, outcomes)

    tables = {
        "enrollment_history": hist, "admissions_funnel": funnel,
        "exam_placement": exam, "capacity_quota": quota,
        "demographics": demo, "cohort_progression": cohort,
        "graduate_outcomes": outcomes, "institution_capacity": icap,
        "finance_support": finance, "macro_regional": macro_r,
        "labour_history": labour, "sector_output": sector,
        "formal_informal": formal, "vacancies": vac,
        "skills_demand": skills, "public_hiring": public,
        "fdi_industrial": fdi, "macro_financial": macro_f,
        "labour_demographics": lab_dem, "shocks_seasonality": shocks,
        "jobs_compat": jobs, "enrollment_compat": enrol_c,
    }
    for name, df in tables.items():
        _write(name, df)
    return tables


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()
    generate()
    if args.validate:
        from backend.services._validate import validate_ethiopia
        errors = validate_ethiopia()
        if errors:
            print("VALIDATION FAILED")
            for e in errors:
                print(" ", e)
            return 1
        print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
