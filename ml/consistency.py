"""
Cross-table consistency rules (Phase 5 groundwork — data accuracy).

Rules every fact table must satisfy, whether simulated or official. They catch
the errors that make a forecast wrong without making a file invalid: a funnel
that accepts more students than it offered places, cohort rates summing past
100%, a "lag" column that is not the previous year's value. That last rule is
the one that would have caught the leak behind the near-zero OLS errors.

Each rule returns the number of violating rows. Run them all:

    from ml.consistency import run_rules
    run_rules()          # list of {rule, table, severity, violations, rows, description}

They feed the admin data-quality page (W.ADM.06) and gate official ingestion
in scripts/ingest_official.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ETH_CANDIDATES = (Path("/data/ethiopia"), Path(__file__).resolve().parents[1] / "data" / "ethiopia")
ETH = next((p for p in ETH_CANDIDATES if p.exists()), ETH_CANDIDATES[-1])
_TOL = 1e-6


@dataclass(frozen=True)
class Rule:
    id: str
    table: str
    severity: str
    description: str
    check: Callable[[pd.DataFrame], pd.Series]   # True where a row VIOLATES the rule


def _lag_mismatch(df: pd.DataFrame, keys: list[str], value: str, lag: str, k: int) -> pd.Series:
    if lag not in df.columns or value not in df.columns:
        return pd.Series(False, index=df.index)
    d = df.sort_values([*keys, "year"])
    true_lag = d.groupby(keys)[value].shift(k)
    # Only where both the published lag and the previous year exist.
    both = d[lag].notna() & true_lag.notna()
    bad = both & ((d[lag] - true_lag).abs() > np.maximum(1.0, 0.001 * true_lag.abs()))
    return bad.reindex(df.index, fill_value=False)


def _prior_rolling_mismatch(df: pd.DataFrame, keys: list[str], value: str, col: str, w: int) -> pd.Series:
    if col not in df.columns:
        return pd.Series(False, index=df.index)
    d = df.sort_values([*keys, "year"])
    prior = d.groupby(keys)[value].transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
    both = d[col].notna() & prior.notna()
    bad = both & ((d[col] - prior).abs() > np.maximum(1.0, 0.001 * prior.abs()))
    return bad.reindex(df.index, fill_value=False)


def _cols(df: pd.DataFrame, *names: str) -> bool:
    return all(n in df.columns for n in names)


RULES: tuple[Rule, ...] = (
    Rule("C.FUNNEL.ORDER", "admissions_funnel", "high",
         "accepted offers ≤ offers ≤ applications",
         lambda d: (d["accepted_offers_count"] > d["offers_count"] + _TOL)
         | (d["offers_count"] > d["applications_count"] + _TOL)
         if _cols(d, "accepted_offers_count", "offers_count", "applications_count")
         else pd.Series(False, index=d.index)),
    Rule("C.FUNNEL.YIELD", "admissions_funnel", "moderate",
         "yield rate = accepted ÷ offers × 100 (within 1 point)",
         lambda d: ((d["accepted_offers_count"] / d["offers_count"].where(d["offers_count"] > 0) * 100
                     - d["yield_rate_pct"]).abs() > 1.0).fillna(False)
         if _cols(d, "accepted_offers_count", "offers_count", "yield_rate_pct")
         else pd.Series(False, index=d.index)),
    Rule("C.COHORT.SUM", "cohort_progression", "high",
         "retention + dropout + transfer ≤ 100%",
         lambda d: (d["retention_rate_pct"] + d["dropout_rate_pct"] + d["transfer_rate_pct"] > 100 + _TOL)
         if _cols(d, "retention_rate_pct", "dropout_rate_pct", "transfer_rate_pct")
         else pd.Series(False, index=d.index)),
    Rule("C.COHORT.COMPLETION", "cohort_progression", "moderate",
         "completion rate ≤ retention rate",
         lambda d: (d["completion_rate_pct"] > d["retention_rate_pct"] + _TOL)
         if _cols(d, "completion_rate_pct", "retention_rate_pct")
         else pd.Series(False, index=d.index)),
    Rule("C.CAPACITY.SEATS", "capacity_quota", "moderate",
         "available seats ≤ approved intake quota ≤ programme capacity",
         lambda d: (d["available_seats"] > d["approved_intake_quota"] + _TOL)
         | (d["approved_intake_quota"] > d["program_capacity"] + _TOL)
         if _cols(d, "available_seats", "approved_intake_quota", "program_capacity")
         else pd.Series(False, index=d.index)),
    Rule("C.EXAM.PLACED", "exam_placement", "high",
         "placed ≤ candidates who passed",
         lambda d: (d["placed_count"] > d["exam_candidates_count"] * d["exam_pass_rate_pct"] / 100 + 1)
         if _cols(d, "placed_count", "exam_candidates_count", "exam_pass_rate_pct")
         else pd.Series(False, index=d.index)),
    Rule("C.LAG.ENROLMENT", "enrollment_history", "critical",
         "enrollment_lag_1y / _2y are the published enrolment of 1 / 2 years earlier",
         lambda d: _lag_mismatch(d, ["institution", "program"], "program_enrollment_count", "enrollment_lag_1y", 1)
         | _lag_mismatch(d, ["institution", "program"], "program_enrollment_count", "enrollment_lag_2y", 2)),
    Rule("C.ROLLING.ENROLMENT", "enrollment_history", "critical",
         "enrollment_rolling_3y_avg is the mean of the three previous years (never the current one)",
         lambda d: _prior_rolling_mismatch(d, ["institution", "program"], "program_enrollment_count",
                                           "enrollment_rolling_3y_avg", 3)),
    Rule("C.LAG.EMPLOYMENT", "labour_history", "critical",
         "employment_lag_1y / _2y are the published employment of 1 / 2 years earlier",
         lambda d: _lag_mismatch(d, ["region", "sector"], "employment_level", "employment_lag_1y", 1)
         | _lag_mismatch(d, ["region", "sector"], "employment_level", "employment_lag_2y", 2)),
    Rule("C.GROWTH.EMPLOYMENT", "labour_history", "moderate",
         "employment_growth_pct matches the change in employment_level (within 0.5 points)",
         lambda d: _growth_mismatch(d)),
    Rule("C.RATES.LABOUR", "labour_history", "high",
         "unemployment and participation rates lie within 0–100%",
         lambda d: ~d[["unemployment_rate_pct", "labour_force_participation_pct"]].apply(
             lambda c: c.between(0, 100)).all(axis=1)
         if _cols(d, "unemployment_rate_pct", "labour_force_participation_pct")
         else pd.Series(False, index=d.index)),
    Rule("C.SKILLS.BOUNDS", "skills_demand", "high",
         "skill shortage / oversupply indices lie within 0–1",
         lambda d: ~d[[c for c in ("skill_shortage_index", "skill_oversupply_index") if c in d]].apply(
             lambda c: c.between(0, 1)).all(axis=1)),
    Rule("C.VACANCIES.NONNEG", "vacancies", "high",
         "vacancy counts are non-negative",
         lambda d: (d["vacancy_count"] < 0) if "vacancy_count" in d else pd.Series(False, index=d.index)),
)


def _growth_mismatch(d: pd.DataFrame) -> pd.Series:
    if not _cols(d, "employment_growth_pct", "employment_level"):
        return pd.Series(False, index=d.index)
    s = d.sort_values(["region", "sector", "year"])
    implied = s.groupby(["region", "sector"])["employment_level"].pct_change() * 100
    both = s["employment_growth_pct"].notna() & implied.notna()
    bad = both & ((s["employment_growth_pct"] - implied).abs() > 0.5)
    return bad.reindex(d.index, fill_value=False)


def run_rules(tables: dict[str, pd.DataFrame] | None = None) -> list[dict]:
    """Evaluate every rule. `tables` overrides files (used to vet a new file)."""
    cache: dict[str, pd.DataFrame | None] = dict(tables or {})
    out = []
    for rule in RULES:
        if rule.table not in cache:
            path = ETH / f"{rule.table}.parquet"
            cache[rule.table] = pd.read_parquet(path) if path.exists() else None
        df = cache[rule.table]
        if df is None or df.empty:
            out.append({"rule": rule.id, "table": rule.table, "severity": rule.severity,
                        "description": rule.description, "violations": None, "rows": 0,
                        "status": "missing table"})
            continue
        bad = rule.check(df)
        n = int(bad.sum())
        out.append({"rule": rule.id, "table": rule.table, "severity": rule.severity,
                    "description": rule.description, "violations": n, "rows": int(len(df)),
                    "status": "pass" if n == 0 else "fail"})
    return out
