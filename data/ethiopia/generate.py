#!/usr/bin/env python3
"""
Simulated Ethiopian fact tables for every DOC1 attribute, calibrated to
published figures.

    python data/ethiopia/generate.py
    python data/ethiopia/generate.py --validate

Seeded and deterministic, 2016–2025. The tables are SIMULATED: no row is an
official MoE / MoLS / ESS record. What changed in November 2026 is that every
magnitude and every shape now comes from `reference/calibration.yaml`, where
each figure carries its source and a confidence tier:

* National exam: candidates 254k (2016) -> 896k (2022) -> 586k (2025); stream
  pass rates collapse from ~50-80% to 3-9% after the 2022 reform; direct and
  remedial placement are separate.
* Public intake follows the national placement series (~130-150k before 2022,
  ~80-95k after), shared among the 17 modelled public universities by size and
  field mix, and cut by dated disruptions: Mekelle and Aksum admit nobody in
  2022-2023 (Tigray war), Wollo is hit in 2021-22, the Amhara conflict from 2023.
* Programmes exist only where the institution teaches them (no medicine at
  AASTU; private universities cannot teach law or teacher education).
* Labour: region x sector employment from regional population and the 2021 LFS
  sector structure; urban unemployment by region (Tigray 17% -> 74% in 2022);
  industrial-park jobs with the Jan 2022 AGOA cut; COVID, war and drought shocks.
* Macro: real GDP growth, inflation, the 2024 birr float, reserves.

Column semantics are unchanged: `program_enrollment_count` is the annual
first-year intake of a programme (Model 1 Layer 2 and Model 3 cohort supply
read it that way). New columns: `students_on_roll_count`,
`admission_eligible_pct`, `remedial_placed_count`, `shock_type`.

Time-series design (Phase 2 of the 2026-11-07 improvement plan) is kept: every
forecast target is persistent (AR(1) deviations), and lag columns are true
lags; rolling means cover previous years only.
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

import calibration as C  # noqa: E402
from dimensions import (  # noqa: E402
    FIELDS, HEIS, INDUSTRIAL_PARKS, REGIONS, SECTORS, YEARS, shock_factor,
)

OUT = Path(__file__).resolve().parent
RNG = np.random.default_rng(42)
PROVENANCE = "simulated"
REFORM_YEAR = 2022
PRE_YEARS = list(range(2010, 2016))          # intake history for students-on-roll only
NATURAL = [f["field"] for f in FIELDS if f["band"] == "Natural science"]
SOCIAL = [f["field"] for f in FIELDS if f["band"] != "Natural science"]
FIELD = {f["field"]: f for f in FIELDS}
HEI = {h["name"]: h for h in HEIS}
PUBLIC = [h["name"] for h in HEIS if h["type"] == "public"]
PRIVATE = [h["name"] for h in HEIS if h["type"] == "private"]
REGION_NAMES = [r["name"] for r in REGIONS]


def _write(name: str, df: pd.DataFrame) -> None:
    df = df.copy()
    df = df.replace([np.inf, -np.inf], np.nan)
    df["provenance"] = PROVENANCE
    df.to_parquet(OUT / f"{name}.parquet", index=False)
    df.to_csv(OUT / f"{name}.csv", index=False)
    print(f"  {name:28s} {len(df):5d} rows  {len(df.columns):3d} cols")


def _ar1(n: int, phi: float, sigma: float) -> np.ndarray:
    """Stationary AR(1) deviations: u_t = phi * u_(t-1) + e_t."""
    u = np.empty(n)
    u[0] = RNG.normal(0, sigma / np.sqrt(1 - phi ** 2))
    for t in range(1, n):
        u[t] = phi * u[t - 1] + RNG.normal(0, sigma)
    return u


# Persistence of the simulated deviations around the calibrated paths.
INTAKE_PHI, INTAKE_SIGMA = 0.7, 0.05
APPS_PHI, APPS_SIGMA = 0.8, 0.06
EMP_PHI, EMP_SIGMA = 0.85, 0.03
VAC_PHI, VAC_SIGMA = 0.75, 0.10
SKILL_PHI, SKILL_SIGMA = 0.75, 0.04


# ── calibrated national series ────────────────────────────────────────────────

def _years(path: str, years=YEARS) -> dict[int, float]:
    return C.series(path, years)


CAND = _years("exam.candidates")
PLACEMENT = _years("exam.public_placement")
CPI_INFL = _years("macro.inflation_pct")
GDP_G = _years("macro.gdp_growth_pct")
FX = _years("macro.etb_per_usd")
RESERVES = _years("macro.fx_reserve_months")
URBAN_UNEMP = _years("labour.urban_unemployment_pct")
GRAD_EMP = _years("employment.graduate_employment_national")
CIVIL_ENTRY = _years("labour.graduates.civil_service_entry_bachelor_etb_month")


def _wage_all() -> dict[int, float]:
    pts = {int(k): float(v) for k, v in C.get("employment.mean_monthly_wage_etb")["all"].items()}
    known = sorted(pts)
    out = {}
    for y in YEARS:
        lo = max([k for k in known if k <= y], default=known[0])
        hi = min([k for k in known if k >= y], default=known[-1])
        out[y] = pts[lo] if lo == hi else pts[lo] + (y - lo) / (hi - lo) * (pts[hi] - pts[lo])
    return out


WAGE = _wage_all()


def _cpi_index() -> dict[int, float]:
    idx, level = {}, 100.0
    for y in YEARS:
        if y > YEARS[0]:
            level *= 1 + CPI_INFL[y] / 100
        idx[y] = level
    return idx


CPI = _cpi_index()


def _natural_share(year: int) -> float:
    ns = C.get("exam.natural_share")
    if year in ns:
        return float(ns[year]["value"])
    return float(ns["pre_reform"]["value"]) if year < REFORM_YEAR else 0.5


def _pass_rate(year: int, band: str) -> float:
    rec = C.get("exam.pass_rate_pct")[year]
    return float(rec["natural" if band == "Natural science" else "social"])


# ── population ────────────────────────────────────────────────────────────────

def _population() -> dict[tuple[str, int], float]:
    base = C.get("population.regions_2022.values")
    g = C.get("population.growth_pct")
    out = {}
    for r in REGION_NAMES:
        rate = float(g["values"].get(r, g["default"])) / 100
        for y in YEARS:
            out[(r, y)] = float(base[r]) * (1 + rate) ** (y - 2022)
    return out


POP = _population()
URBAN_2007 = C.get("population.urban_share_2007.values")


def _urban_share(region: str, year: int) -> float:
    """Regional urban share scaled so the national path follows 19.6% -> 24.1%."""
    nat = C.series("population.urban_share_national", YEARS)[year]
    u07 = float(URBAN_2007[region])
    if u07 >= 0.999:
        return 1.0
    return float(min(0.95, u07 * nat / 0.162))


# ── higher education: who teaches what, and how much ─────────────────────────

NOT_OFFERED = {k: set(v) for k, v in C.get("programmes.not_offered").items()}
SPEC = C.get("programmes.specialisation.values")
WEIGHT = C.get("programmes.intake_weight.values")
BASE_MIX = C.get("higher_education.field_mix_public_2015.values")
MODELLED_SHARE = float(C.get("programmes.modelled_public_share.value"))
INTAKE_DISRUPT = C.get("programmes.intake_disruption.values")
LENGTH = C.get("higher_education.programme_length_years")
ATTRITION = C.get("higher_education.attrition_over_programme")


def _offered(inst: str, field: str) -> bool:
    return field not in NOT_OFFERED.get(inst, set())


def _field_mix(inst: str, year: int) -> dict[str, float]:
    """Share of an institution's intake by field. National drift: health and
    business gain, engineering loses (HESAA 2024/25 vs ESAA 2014/15)."""
    drift = {"Medicine & Health Sciences": 1 + 0.04 * (year - 2016),
             "Business & Economics": 1 + 0.02 * (year - 2016),
             "Engineering & Technology": 1 - 0.015 * (year - 2016)}
    raw = {}
    for f in FIELD:
        if not _offered(inst, f):
            continue
        raw[f] = float(BASE_MIX[f]) * float(SPEC.get(inst, {}).get(f, 1.0)) * drift.get(f, 1.0)
    total = sum(raw.values())
    return {f: v / total for f, v in raw.items()}


def _intake_factor(inst: str, year: int) -> float:
    return float(INTAKE_DISRUPT.get(inst, {}).get(year, 1.0))


def _program_length(field: str) -> int:
    return int(LENGTH.get(field, LENGTH["default"]))


def _attrition(inst: str) -> float:
    return float(ATTRITION["by_institution"].get(inst, ATTRITION["overall"]))


def _private_intake(inst: str, year: int) -> float:
    pts = {int(k): float(v) for k, v in C.get("programmes.private_intake")[inst].items()}
    known = sorted(pts)
    lo = max([k for k in known if k <= year], default=known[0])
    hi = min([k for k in known if k >= year], default=known[-1])
    return pts[lo] if lo == hi else pts[lo] + (year - lo) / (hi - lo) * (pts[hi] - pts[lo])


def _placement(year: int) -> float:
    if year in PLACEMENT:
        return PLACEMENT[year]
    return PLACEMENT[YEARS[0]] * 0.97 ** (YEARS[0] - year)      # pre-2016 history, gentle growth


def _intake_panel() -> pd.DataFrame:
    """First-year intake by institution x programme x year, plus the planned
    intake (what the quota would have been without disruption)."""
    all_years = PRE_YEARS + YEARS
    rows = []
    devs = {}
    for inst in PUBLIC + PRIVATE:
        for f in FIELD:
            if _offered(inst, f):
                devs[(inst, f)] = _ar1(len(all_years), INTAKE_PHI, INTAKE_SIGMA)
    for yi, year in enumerate(all_years):
        total = _placement(year) * MODELLED_SHARE
        disrupted = {h: float(WEIGHT[h]) * _intake_factor(h, year) for h in PUBLIC}
        planned = {h: float(WEIGHT[h]) for h in PUBLIC}
        sd, sp = sum(disrupted.values()), sum(planned.values())
        for inst in PUBLIC + PRIVATE:
            mix = _field_mix(inst, max(year, YEARS[0]))
            if inst in PUBLIC:
                inst_total = total * disrupted[inst] / sd
                inst_plan = total * planned[inst] / sp
            else:
                inst_total = inst_plan = _private_intake(inst, max(year, YEARS[0]))
            for f, share in mix.items():
                noise = float(np.exp(devs[(inst, f)][yi]))
                intake = int(round(inst_total * share * noise)) if inst_total > 0 else 0
                rows.append({"institution": inst, "field": f, "year": year,
                             "intake": intake, "planned": inst_plan * share})
    return pd.DataFrame(rows)


# ── exam ──────────────────────────────────────────────────────────────────────

def _seat_mix(year: int) -> dict[str, float]:
    """National public seat mix by field (all modelled public institutions)."""
    acc = {f: 0.0 for f in FIELD}
    for inst in PUBLIC:
        for f, s in _field_mix(inst, year).items():
            acc[f] += float(WEIGHT[inst]) * s
    total = sum(acc.values())
    return {f: v / total for f, v in acc.items()}


def build_exam_placement() -> pd.DataFrame:
    rows = []
    for year in YEARS:
        cand = CAND[year]
        ns = _natural_share(year)
        seat = _seat_mix(year)
        nat_seat = sum(seat[f] for f in NATURAL)
        placement = PLACEMENT[year]
        direct_total = 0.0
        recs = []
        for f in FIELD:
            band = FIELD[f]["band"]
            stream_cand = cand * (ns if band == "Natural science" else 1 - ns)
            within = seat[f] / (nat_seat if band == "Natural science" else 1 - nat_seat)
            cand_f = stream_cand * within
            pr = round(float(np.clip(_pass_rate(year, band) + RNG.normal(0, 0.15 if year >= REFORM_YEAR else 1.2), 0.3, 95)), 2)
            cand_f = float(round(cand_f))
            passers = np.floor(cand_f * pr / 100)       # from the published (rounded) figures
            if year < REFORM_YEAR:
                direct = float(np.floor(min(passers, placement * seat[f])))
            else:
                direct = passers                          # every passer is placed directly
            direct_total += direct
            recs.append((f, band, cand_f, pr, passers, direct))
        remedial_total = max(0.0, placement - direct_total)
        for f, band, cand_f, pr, passers, direct in recs:
            remedial = remedial_total * seat[f]
            eligible_pool = (passers if year < REFORM_YEAR else direct + remedial) * 1.05
            mean = (52.0 + RNG.normal(0, 1.2)) if year < REFORM_YEAR else (31.0 + 1.6 * (year - REFORM_YEAR) + RNG.normal(0, 0.8))
            cutoff = (mean + (5 if band == "Natural science" else 2)) if year < REFORM_YEAR else 50.0
            placed = int(direct)
            rows.append({
                "year": year, "field": f, "band": band,
                "exam_candidates_count": int(round(cand_f)),
                "exam_pass_rate_pct": round(pr, 2),
                "exam_score_mean": round(mean, 2),
                "exam_score_sd": 11.5,
                "exam_score_p25": round(mean - 7.8, 2),
                "exam_score_p50": round(mean, 2),
                "exam_score_p75": round(mean + 7.8, 2),
                "program_cutoff_score": round(cutoff, 2),
                "placed_count": placed,
                "remedial_placed_count": int(round(remedial)),
                "placement_rate_pct": round((placed + remedial) / cand_f * 100, 3),
                "admission_eligible_pct": round(min(100.0, eligible_pool / cand_f * 100), 3),
                "field_allocation_count": int(round(placed + remedial)),
                "band_allocation_ratio": 0.70 if band == "Natural science" else 0.30,
            })
    return pd.DataFrame(rows)


# ── higher education tables ───────────────────────────────────────────────────

def build_enrollment_history(intake: pd.DataFrame) -> pd.DataFrame:
    df = intake[intake["year"].isin(YEARS)].copy()
    df["program_enrollment_count"] = df["intake"]
    # students on roll: intake of the last L years, thinned by attrition, and
    # zero while a campus is closed (Tigray students were transferred out)
    full = intake.set_index(["institution", "field", "year"])["intake"]
    on_roll = []
    for r in df.itertuples(index=False):
        L = _program_length(r.field)
        a = 1 - (1 - _attrition(r.institution)) ** (1 / L)
        total = 0.0
        for k in range(L + 1):                    # +1: repeaters and late finishers
            y = r.year - k
            got = full.get((r.institution, r.field, y))
            if got is None:
                continue
            total += float(got) * (1 - a) ** k * (0.35 if k == L else 1.0)
        ops = shock_factor(HEI[r.institution]["region"], r.year, r.institution)
        if HEI[r.institution]["region"] == "Tigray":
            total *= ops
        on_roll.append(int(round(total)))
    df["students_on_roll_count"] = on_roll
    meta = []
    for r in df.itertuples(index=False):
        h, f = HEI[r.institution], FIELD[r.field]
        meta.append({"institution_type": h["type"], "generation": h["generation"], "campus": h["campus"],
                     "region": h["region"], "program": f["program"], "band": f["band"], "stem": f["stem"],
                     "occupation": f["occupation"], "sector": f["sector"]})
    df = pd.concat([df.reset_index(drop=True), pd.DataFrame(meta)], axis=1)
    df = df.sort_values(["institution", "program", "year"]).reset_index(drop=True)
    g = df.groupby(["institution", "program"], sort=False)["program_enrollment_count"]
    df["enrollment_lag_1y"] = g.shift(1)
    df["enrollment_lag_2y"] = g.shift(2)
    df["enrollment_rolling_3y_avg"] = g.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    df["enrollment_rolling_5y_avg"] = g.transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
    df["enrollment_growth_rate_pct"] = g.pct_change() * 100
    df["campus_enrollment_count"] = df.groupby(["institution", "campus", "year"])["program_enrollment_count"].transform("sum")
    df["region_enrollment_count"] = df.groupby(["region", "year"])["program_enrollment_count"].transform("sum")
    cols = ["institution", "institution_type", "generation", "campus", "region", "program", "field", "band",
            "stem", "occupation", "sector", "year", "program_enrollment_count", "students_on_roll_count",
            "enrollment_lag_1y", "enrollment_lag_2y", "enrollment_rolling_3y_avg", "enrollment_rolling_5y_avg",
            "enrollment_growth_rate_pct", "campus_enrollment_count", "region_enrollment_count"]
    return df[cols]


# How applicants spread across fields within their stream, relative to seats.
APPLICANT_PREFERENCE = {
    "Medicine & Health Sciences": 1.8, "Engineering & Technology": 1.0,
    "Natural & Computational Sciences": 0.85, "Agriculture & Life Sciences": 0.55,
    "Business & Economics": 1.5, "Law": 1.3, "Social Sciences & Humanities": 0.8, "Education": 0.5,
}


def build_admissions_funnel(hist: pd.DataFrame, quota: pd.DataFrame) -> pd.DataFrame:
    """Applications are drawn from the whole candidate pool of the stream, so
    they scale with the exam cohort (254k -> 896k -> 586k) while seats do not:
    applicants per seat jumps after 2021."""
    df = hist[["institution", "campus", "region", "program", "field", "band", "year",
               "program_enrollment_count"]].copy()
    df = df.merge(quota[["institution", "program", "year", "available_seats"]],
                  on=["institution", "program", "year"], how="left")
    # demand weight of each (institution, field): planned size x preference, within stream
    weights = {}
    for inst in PUBLIC + PRIVATE:
        size = float(WEIGHT.get(inst, 0)) or _private_intake(inst, 2020) * 4
        for f, s in _field_mix(inst, 2020).items():
            weights[(inst, f)] = size * s * APPLICANT_PREFERENCE[f]
    stream_tot = {band: sum(w for (i, f), w in weights.items() if FIELD[f]["band"] == band)
                  for band in ("Natural science", "Social science")}
    devs = {k: _ar1(len(YEARS), APPS_PHI, APPS_SIGMA) for k in weights}
    apps = []
    for r in df.itertuples(index=False):
        k = (r.institution, r.field)
        band = FIELD[r.field]["band"]
        ns = _natural_share(r.year)
        stream = CAND[r.year] * (ns if band == "Natural science" else 1 - ns)
        share = weights[k] / stream_tot[band]
        f = _intake_factor(r.institution, r.year) if r.institution in PUBLIC else 1.0
        a = stream * MODELLED_SHARE * share * f * float(np.exp(devs[k][YEARS.index(r.year)]))
        apps.append(int(round(max(a, r.program_enrollment_count * 1.02 if f > 0 else 0))))
    df["applications_count"] = apps
    intake = df["program_enrollment_count"].astype(int)
    offers = np.minimum(df["applications_count"],
                        np.ceil(intake * RNG.uniform(1.02, 1.12, len(df))).astype(int))
    offers = np.where(intake == 0, 0, offers)
    df["offers_count"] = offers.astype(int)
    df["accepted_offers_count"] = np.minimum(intake, df["offers_count"]).astype(int)
    df["yield_rate_pct"] = np.where(df["offers_count"] > 0,
                                    df["accepted_offers_count"] / df["offers_count"].where(df["offers_count"] > 0) * 100, 0.0)
    seats = df["available_seats"].fillna(0)
    df["applicants_per_seat"] = np.where(seats > 0, df["applications_count"] / seats.where(seats > 0), 0.0)
    df["first_choice_demand_count"] = (df["applications_count"] * RNG.uniform(0.35, 0.6, len(df))).astype(int)
    return df.drop(columns=["program_enrollment_count", "available_seats", "band"])


def build_capacity_quota(hist: pd.DataFrame, intake: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "campus", "region", "program", "field", "band", "year",
               "program_enrollment_count"]].copy()
    plan = intake.set_index(["institution", "field", "year"])["planned"]
    planned = np.array([plan[(r.institution, r.field, r.year)] for r in df.itertuples(index=False)])
    actual = df["program_enrollment_count"].to_numpy(dtype=float)
    factor = np.array([_intake_factor(i, y) if i in PUBLIC else 1.0 for i, y in zip(df["institution"], df["year"])])
    quota = np.maximum(planned * RNG.uniform(0.97, 1.06, len(df)), actual)
    seats = np.minimum(quota, np.maximum(actual * RNG.uniform(1.0, 1.05, len(df)),
                                         quota * factor * RNG.uniform(0.9, 1.0, len(df))))
    seats = np.where(factor == 0, 0, seats)
    df["approved_intake_quota"] = np.round(quota).astype(int)
    df["available_seats"] = np.minimum(np.round(seats), df["approved_intake_quota"]).astype(int)
    df["program_capacity"] = np.round(quota * RNG.uniform(1.08, 1.25, len(df))).astype(int)
    df["program_expansion_flag"] = (df["year"] >= 2020) & df["field"].isin(["Medicine & Health Sciences", "Natural & Computational Sciences"])
    df["program_suspension_flag"] = factor == 0
    df["strategic_priority_flag"] = df["band"] == "Natural science"
    return df.drop(columns=["program_enrollment_count", "band"])


def build_cohort(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "program", "field", "region", "year"]].copy()
    ret, drop, trans, comp, ttg = [], [], [], [], []
    for r in df.itertuples(index=False):
        L = _program_length(r.field)
        annual = 1 - (1 - _attrition(r.institution)) ** (1 / L)
        ops = shock_factor(r.region, r.year, r.institution)
        if r.year == 2020:
            annual *= 1.35                                  # COVID closure year
        annual *= 1 + 0.6 * (1 - ops) if r.year != 2020 else 1
        a = float(np.clip(annual * 100 + RNG.normal(0, 0.8), 1.5, 45))
        moved = 0.0
        if r.region == "Tigray" and ops < 0.5:
            moved = (1 - ops) * 70                          # students transferred to other universities
        d = a * RNG.uniform(0.55, 0.7)
        t = a * RNG.uniform(0.15, 0.25) + moved
        keep = float(np.clip(100 - a - moved, 0, 99))
        ret.append(keep)
        drop.append(d)
        trans.append(min(t, 100 - keep - d))
        completion = (1 - _attrition(r.institution)) * 100 * (0.85 + 0.15 * ops) + RNG.normal(0, 1.5)
        comp.append(float(np.clip(min(completion, keep - 0.5), 0, 98)))
        delay = 0.0
        if r.year in (2021, 2022):
            delay += 0.5                                     # COVID cohorts graduate late
        if r.region == "Tigray" and r.year >= 2022:
            delay += 1.5 if r.year <= 2024 else 1.0
        if r.region == "Amhara" and r.year >= 2024:
            delay += 0.3
        ttg.append(round(L + 0.3 + delay + RNG.normal(0, 0.15), 2))
    df["retention_rate_pct"] = ret
    df["dropout_rate_pct"] = drop
    df["transfer_rate_pct"] = trans
    df["completion_rate_pct"] = comp
    df["time_to_graduation_years"] = ttg
    return df


REGION_EMP_ADJ = {
    "Tigray": {2020: 0.95, 2021: 0.55, 2022: 0.35, 2023: 0.45, 2024: 0.6, 2025: 0.7},
    "Amhara": {2021: 0.94, 2024: 0.9, 2025: 0.92},
    "Afar": {2021: 0.93, 2022: 0.94},
}
REGION_BASE_ADJ = {"Addis Ababa": 1.08, "Dire Dawa": 1.02, "Harari": 1.02, "Somali": 0.92,
                   "Afar": 0.92, "Gambela": 0.9, "Benishangul-Gumuz": 0.93}
EARN_PREMIUM = {"Medicine & Health Sciences": 1.25, "Engineering & Technology": 1.15,
                "Natural & Computational Sciences": 1.2, "Business & Economics": 1.1, "Law": 1.1,
                "Agriculture & Life Sciences": 0.95, "Education": 0.95, "Social Sciences & Humanities": 0.9}


def build_outcomes(hist: pd.DataFrame, vacancies: pd.DataFrame, skills: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "program", "field", "region", "year"]].copy()
    rel = C.get("employment.graduate_employment_by_field.relative_to_national")
    vac = vacancies.groupby(["field", "region", "year"])["vacancy_count"].sum()
    short = skills.set_index(["field", "year"])["skill_shortage_index"]
    emp, unemp, earn, vd, sig = [], [], [], [], []
    for r in df.itertuples(index=False):
        e = GRAD_EMP[r.year] * float(rel[r.field]) * REGION_BASE_ADJ.get(r.region, 1.0)
        e *= REGION_EMP_ADJ.get(r.region, {}).get(r.year, 1.0)
        e = float(np.clip(e + RNG.normal(0, 2.5), 12, 96))
        emp.append(e)
        unemp.append(float(np.clip(100 - e - RNG.uniform(6, 12), 2, 85)))
        monthly = CIVIL_ENTRY[r.year] * EARN_PREMIUM[r.field] * (1.15 if r.region == "Addis Ababa" else 1.0)
        earn.append(int(monthly * 12 * RNG.uniform(1.05, 1.35)))
        vd.append(int(vac.get((r.field, r.region, r.year), 0)))
        sig.append(float(np.clip((float(short[(r.field, r.year)]) - 0.35) * 6 + (60 - e) / 15, -2, 3)))
    df["graduate_employment_rate_pct"] = emp
    df["graduate_unemployment_rate_pct"] = unemp
    df["median_earnings_etb"] = earn
    df["vacancy_demand_by_field"] = vd
    df["skills_shortage_signal"] = sig
    return df


DIFFERENTIATION = C.get("higher_education.differentiation")


def build_institution_capacity(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "campus", "region", "program", "year", "students_on_roll_count"]].copy()
    research = set(DIFFERENTIATION["research"])
    q_base = {i: (0.72 if i in research else 0.66 if i in DIFFERENTIATION["science_technology"] else 0.6) for i in HEI}
    ratio, labs, rooms, acc, qual = [], [], [], [], []
    for r in df.itertuples(index=False):
        ops = shock_factor(r.region, r.year, r.institution)
        ratio.append(float(np.clip(RNG.normal(24 if r.institution not in research else 19, 2.5), 10, 45)))
        size = max(r.students_on_roll_count, 1)
        labs.append(int(max(1, size / 220 * (0.4 if r.region == "Tigray" and r.year >= 2021 else 1))))
        rooms.append(int(max(4, size / 45)))
        war = r.region == "Tigray" and r.year in (2021, 2022, 2023)
        acc.append("probation" if war or RNG.random() < 0.06 else "accredited")
        qual.append(float(np.clip(q_base[r.institution] - (0.18 if war else 0) - 0.08 * (1 - max(ops, 0.45))
                                  + RNG.normal(0, 0.04), 0.2, 0.95)))
    df["faculty_student_ratio"] = ratio
    df["laboratory_count"] = labs
    df["classroom_count"] = rooms
    df["accreditation_status"] = acc
    df["program_quality_index"] = qual
    return df.drop(columns=["students_on_roll_count"])


SPEND_2020 = float(C.get("finance.spending_per_student_etb.value"))
TUITION_SHARE = float(C.get("finance.cost_sharing.tuition_share"))
MEAL = C.series("finance.meal_allowance_etb_per_day", YEARS)
FIELD_COST = {"Medicine & Health Sciences": 1.6, "Engineering & Technology": 1.25,
              "Natural & Computational Sciences": 1.1, "Agriculture & Life Sciences": 1.1}


def build_finance(hist: pd.DataFrame) -> pd.DataFrame:
    df = hist[["institution", "program", "field", "year"]].copy()
    unity = {int(k): float(v) for k, v in C.get("finance.private_tuition_etb_semester.Unity University").items()}
    fee, stip, sch, loan = [], [], [], []
    for r in df.itertuples(index=False):
        cost = FIELD_COST.get(r.field, 1.0)
        if HEI[r.institution]["type"] == "public":
            spend = SPEND_2020 * CPI[r.year] / CPI[2020]
            tuition = spend * TUITION_SHARE * cost
            if r.institution == "Addis Ababa University" and r.year >= 2025:
                tuition = 36000 * (4.6 if r.field == "Medicine & Health Sciences" else cost)
            food = MEAL[r.year] * 300
            fee.append(int(tuition))
            stip.append(int(food))
            sch.append(float(np.clip(RNG.normal(0.75, 0.05), 0.5, 0.95)))
            loan.append(int(tuition + food))
        else:
            per_sem = unity[2024] * (CPI[r.year] / CPI[2024]) if r.year < 2025 else unity[2025]
            mult = 1.0 if r.institution == "Unity University" else 0.85
            fee.append(int(per_sem * 2 * mult * cost))
            stip.append(0)
            sch.append(float(np.clip(RNG.normal(0.1, 0.03), 0.02, 0.25)))
            loan.append(0)
    df["tuition_fee_etb"] = fee
    df["stipend_etb"] = stip
    df["scholarship_availability"] = sch
    df["cost_sharing_loan_etb"] = loan
    return df


# ── regional economy and labour ───────────────────────────────────────────────

def _regional_unemployment(region: str, year: int) -> float:
    reg = C.get("labour.regional_urban_unemployment_pct.values")
    national = URBAN_UNEMP[year]
    if region == "Tigray":
        path = {2016: 19, 2017: 19, 2018: 18, 2019: 17, 2020: 24, 2021: 55, 2022: 74.1, 2023: 66, 2024: 54, 2025: 46}
        return float(path[year])
    if region in reg:
        base = float(reg[region]) / URBAN_UNEMP[2021]
        if region == "Benishangul-Gumuz":
            base = 0.6
        return float(np.clip(national * base, 3, 60))
    factor = {"Amhara": 0.95, "Oromia": 0.97, "Sidama": 0.9, "South Ethiopia": 0.88,
              "South West Ethiopia": 0.86, "Central Ethiopia": 0.9, "Afar": 0.85,
              "Gambela": 1.05, "Harari": 1.0}.get(region, 1.0)
    shock = {("Amhara", 2021): 1.12, ("Amhara", 2024): 1.15, ("Amhara", 2025): 1.12,
             ("Afar", 2021): 1.1, ("Afar", 2022): 1.08}.get((region, year), 1.0)
    return float(np.clip(national * factor * shock, 3, 60))


def build_macro_regional() -> pd.DataFrame:
    rows = []
    level = {"Addis Ababa": 1.55, "Dire Dawa": 1.15, "Harari": 1.12, "Gambela": 0.82, "Afar": 0.8,
             "Somali": 0.8, "Benishangul-Gumuz": 0.85}
    drought = {("Somali", 2021): 0.9, ("Somali", 2022): 0.82, ("Somali", 2023): 0.88,
               ("Afar", 2022): 0.85, ("Afar", 2023): 0.9, ("Oromia", 2022): 0.95}
    war = {("Tigray", 2021): 0.45, ("Tigray", 2022): 0.32, ("Tigray", 2023): 0.5,
           ("Tigray", 2024): 0.65, ("Tigray", 2025): 0.72, ("Amhara", 2021): 0.9,
           ("Amhara", 2024): 0.88, ("Amhara", 2025): 0.9, ("Afar", 2021): 0.88}
    for region in REGION_NAMES:
        for year in YEARS:
            infl = CPI_INFL[year] + (12 if region == "Tigray" and year in (2021, 2022) else 0) + RNG.normal(0, 1.2)
            income = WAGE[year] * 12 * level.get(region, 0.95) * drought.get((region, year), 1) * war.get((region, year), 1)
            ses = 0.62 if region == "Addis Ababa" else 0.45 * level.get(region, 0.95)
            if (region, year) in war:
                ses *= war[(region, year)] ** 0.5
            rows.append({
                "region": region, "year": year,
                "inflation_rate_pct": round(float(infl), 2),
                "household_income_proxy_etb": int(income),
                "youth_unemployment_rate_pct": round(float(np.clip(_regional_unemployment(region, year) * 1.3, 4, 95)), 2),
                "regional_socioeconomic_index": round(float(np.clip(ses + RNG.normal(0, 0.02), 0.08, 0.9)), 3),
            })
    return pd.DataFrame(rows)


def _sector_shares(year: int) -> dict[str, float]:
    """National employment share of each modelled sector (LFS 2013 -> 2021,
    continued at half the pace after 2021)."""
    emp = C.get("employment.by_sector_thousands.values")
    tot = C.get("employment.by_sector_thousands.total")
    out = {}
    for s in SECTORS:
        a = float(emp[s][2013]) / tot[2013]
        b = float(emp[s][2021]) / tot[2021]
        if year <= 2021:
            out[s] = a + (b - a) * (year - 2013) / 8
        else:
            out[s] = b + (b - a) / 8 * 0.5 * (year - 2021)
    return out


URBAN_MULT = {"Agriculture": 0.129 / 0.771, "Manufacturing": 4.8, "Construction": 4.8}
SERVICE_MULT = 0.703 / 0.194


def _region_sector_share(region: str, sector: str, year: int) -> float:
    nat = _sector_shares(year)[sector]
    u_nat = 0.213
    m = URBAN_MULT.get(sector, SERVICE_MULT)
    rural = nat / (1 - u_nat + m * u_nat)
    u = _urban_share(region, year)
    return rural * (1 - u) + rural * m * u


def _park_jobs() -> dict[tuple[str, int], float]:
    """Employment by park and year: published anchors, interpolated, with the
    AGOA cut (Jan 2022) and the Mekelle closure."""
    anchors = {
        "Hawassa Industrial Park": {2016: 3000, 2018: 24000, 2021: 29975, 2022: 25654, 2023: 22000, 2025: 23500},
        "Bole Lemi": {2014: 9100, 2018: 15000, 2021: 17100, 2022: 16003, 2025: 16800},
        "Eastern Industrial Zone": {2010: 2000, 2018: 14906, 2021: 18000, 2025: 19500},
        "Adama Industrial Park": {2018: 1500, 2021: 6300, 2022: 5400, 2025: 6200},
        "Kombolcha Industrial Park": {2017: 1200, 2018: 3800, 2020: 4200, 2021: 2600, 2022: 3300, 2025: 4000},
        "Mekelle Industrial Park": {2017: 1500, 2018: 3800, 2020: 2000, 2021: 700, 2022: 0, 2023: 300, 2024: 1000, 2025: 1500},
        "Dire Dawa Industrial Park": {2018: 600, 2021: 2200, 2025: 2800},
        "Debre Berhan Industrial Park": {2019: 800, 2021: 2500, 2025: 3500},
        "Jimma Industrial Park": {2019: 300, 2021: 1500, 2025: 2200},
        "Bahir Dar Industrial Park": {2020: 300, 2021: 1000, 2023: 1100, 2024: 900, 2025: 1000},
    }
    out = {}
    for p in INDUSTRIAL_PARKS:
        a = anchors[p["name"]]
        known = sorted(a)
        for y in YEARS:
            if y < p["opened"]:
                out[(p["name"], y)] = 0.0
                continue
            lo = max([k for k in known if k <= y], default=None)
            hi = min([k for k in known if k >= y], default=None)
            if lo is None:
                v = a[hi] * 0.5
            elif hi is None:
                v = a[lo]
            elif lo == hi:
                v = a[lo]
            else:
                v = a[lo] + (y - lo) / (hi - lo) * (a[hi] - a[lo])
            out[(p["name"], y)] = float(v)
    return out


PARK_JOBS = _park_jobs()


def _labour_shock(region: str, sector: str, year: int) -> float:
    f = 1.0
    if year == 2020 and sector != "Agriculture":
        f *= 0.97
    tigray = {2021: 0.6, 2022: 0.45, 2023: 0.6, 2024: 0.75, 2025: 0.82}
    if region == "Tigray" and year in tigray:
        f *= tigray[year] if sector != "Agriculture" else {2021: 0.6, 2022: 0.5, 2023: 0.55, 2024: 0.7, 2025: 0.8}[year]
    amhara = {2021: 0.93, 2024: 0.92, 2025: 0.94}
    if region == "Amhara" and year in amhara:
        f *= amhara[year]
    if region == "Afar" and year in (2021, 2022):
        f *= 0.9
    if region == "Benishangul-Gumuz" and year in (2020, 2021):
        f *= 0.95
    if sector == "Agriculture":
        drought = {("Somali", 2021): 0.9, ("Somali", 2022): 0.82, ("Somali", 2023): 0.88,
                   ("Afar", 2022): 0.85, ("Afar", 2023): 0.9, ("Oromia", 2022): 0.95,
                   ("Afar", 2016): 0.9, ("Somali", 2016): 0.9, ("Somali", 2017): 0.88}
        f *= drought.get((region, year), 1.0)
    return f


def build_labour_history() -> pd.DataFrame:
    rows = []
    emp_to_pop = {y: 0.36 * (1 + 0.002 * (y - 2021)) for y in YEARS}
    participation = float(C.get("labour.participation_2021.value"))
    freeze = set(C.get("public_sector.hiring_freeze.years"))
    for region in REGION_NAMES:
        for sector in SECTORS:
            dev = _ar1(len(YEARS), EMP_PHI, EMP_SIGMA)
            prev_public = None
            for i, year in enumerate(YEARS):
                base = POP[(region, year)] * emp_to_pop[year] * _region_sector_share(region, sector, year)
                if sector == "Manufacturing":
                    base += sum(PARK_JOBS[(p["name"], year)] for p in INDUSTRIAL_PARKS if p["region"] == region)
                emp = base * _labour_shock(region, sector, year) * float(np.exp(dev[i]))
                if sector in ("Public administration", "Education") and year in freeze and prev_public:
                    emp = prev_public * RNG.uniform(0.995, 1.005)       # hiring freeze: flat headcount
                prev_public = emp
                ur = _regional_unemployment(region, year)
                if sector == "Agriculture":
                    ur *= 0.35
                elif sector in ("Public administration", "Education", "Health"):
                    ur *= 0.6
                rows.append({
                    "region": region, "sector": sector, "year": year,
                    "employment_level": int(round(emp)),
                    "unemployment_rate_pct": round(float(np.clip(ur + RNG.normal(0, 0.6), 0.5, 90)), 2),
                    "youth_unemployment_rate_pct": round(float(np.clip(ur * 1.3 + RNG.normal(0, 1), 1, 95)), 2),
                    "sector_employment": int(round(emp)),
                    "labour_force_participation_pct": round(float(np.clip(
                        participation * (0.85 if region == "Tigray" and year in (2021, 2022) else 1)
                        + RNG.normal(0, 1.2), 35, 90)), 2),
                })
    df = pd.DataFrame(rows).sort_values(["region", "sector", "year"])
    g = df.groupby(["region", "sector"], sort=False)["employment_level"]
    df["employment_lag_1y"] = g.shift(1)
    df["employment_lag_2y"] = g.shift(2)
    df["employment_growth_pct"] = g.pct_change() * 100
    growth = (df["employment_level"] - df["employment_lag_1y"]).clip(lower=0).fillna(0)
    df["job_creation_count"] = (growth + df["employment_level"] * 0.03).round().astype(int)
    cols = ["region", "sector", "year", "employment_level", "unemployment_rate_pct", "youth_unemployment_rate_pct",
            "sector_employment", "job_creation_count", "labour_force_participation_pct",
            "employment_lag_1y", "employment_lag_2y", "employment_growth_pct"]
    return df[cols].reset_index(drop=True)


PRODUCTIVITY_2016 = {"Agriculture": 11000, "Manufacturing": 62000, "Construction": 70000, "ICT": 210000,
                     "Finance": 260000, "Public administration": 60000, "Education": 48000, "Health": 55000}


def build_sector_output(labour: pd.DataFrame) -> pd.DataFrame:
    df = labour[["region", "sector", "year", "employment_level"]].copy()
    real = {}
    level = 100.0
    for y in YEARS:
        if y > YEARS[0]:
            level *= 1 + GDP_G[y] / 100
        real[y] = level
    va, growth, index = [], [], []
    for r in df.itertuples(index=False):
        prod = PRODUCTIVITY_2016[r.sector] * (real[r.year] / 100) ** 0.6 * CPI[r.year] / 100
        va.append(int(r.employment_level * prod))
        shock = _labour_shock(r.region, r.sector, r.year)
        growth.append(round(float(GDP_G[r.year] * (0.7 if r.sector == "Agriculture" else 1.15)
                                  * shock - (1 - shock) * 30 + RNG.normal(0, 0.8)), 2))
        index.append(round(float(real[r.year] * shock), 2))
    df["sector_value_added_etb"] = va
    df["sector_growth_rate_pct"] = growth
    df["sector_output_index"] = index
    df["business_formation_count"] = (df["employment_level"] * np.where(df["sector"] == "Agriculture", 0.0004, 0.004)
                                      * RNG.uniform(0.8, 1.2, len(df))).astype(int)
    df["sector_investment_etb"] = (df["sector_value_added_etb"] * 0.22).astype(int)
    df["employment_intensity"] = df["employment_level"] / (df["sector_value_added_etb"] / 1_000_000)
    return df.drop(columns=["employment_level"])


FORMAL_SHARE = {"Agriculture": 0.03, "Manufacturing": 0.45, "Construction": 0.3, "Finance": 0.95,
                "ICT": 0.8, "Public administration": 1.0, "Education": 0.9, "Health": 0.85}
SELF_SHARE = {"Agriculture": 0.55, "Manufacturing": 0.25, "Construction": 0.2, "Finance": 0.03,
              "ICT": 0.12, "Public administration": 0.0, "Education": 0.03, "Health": 0.06}


def build_formal_informal(labour: pd.DataFrame) -> pd.DataFrame:
    df = labour[["region", "sector", "year", "employment_level"]].copy()
    formal = df["sector"].map(FORMAL_SHARE) * (1 + 0.004 * (df["year"] - 2016))
    formal = formal.clip(upper=1.0)
    e = df["employment_level"]
    df["formal_wage_employment"] = (e * formal).astype(int)
    df["informal_employment"] = (e * (1 - formal)).astype(int)
    df["self_employment"] = (e * df["sector"].map(SELF_SHARE)).astype(int)
    under = np.where(df["sector"] == "Agriculture", 0.22, 0.12) * (1 + (df["region"] == "Tigray") * (df["year"] >= 2021) * 0.8)
    df["underemployment"] = (e * under).astype(int)
    df["microenterprise_activity"] = (e * (1 - formal) * 0.02 * RNG.uniform(0.8, 1.2, len(df))).astype(int)
    df["sector_absorption_rate"] = np.clip(formal + RNG.normal(0, 0.02, len(df)), 0.01, 1.0)
    return df.drop(columns=["employment_level"])


# National vacancies open to new graduates in 2025, per occupation (calibration.yaml).
VACANCY_2025 = {k: float(v) for k, v in C.get("employment.graduate_entry_vacancies_2025.values").items()}
PUBLIC_OCCUPATIONS = {"Secondary Teacher", "Social Worker", "Legal Officer"}
FILL_DAYS = {"Accountant": 30, "Civil Engineer": 50, "General Practitioner": 70, "Software Developer": 55,
             "Social Worker": 35, "Legal Officer": 40, "Secondary Teacher": 45, "Agronomist": 40}


def _modelled_share_by_field(hist: pd.DataFrame) -> dict[str, float]:
    """Share of each field's national students that the 19 modelled
    institutions hold (2025): modelled students on roll / (all-HE enrolment x
    field mix, HESAA 2024/25). Vacancies are national; graduates come only
    from the modelled institutions, so demand is scaled to the same scope
    before the two are compared. Without this every field reads as a
    shortage, and business (41.5% of all students, mostly private) as the
    worst one, the opposite of the evidence."""
    total = float(C.get("higher_education.all_he_2025.value"))
    mix = C.get("higher_education.field_mix_all_he_2025.values")
    roll = hist[hist["year"] == YEARS[-1]].groupby("field")["students_on_roll_count"].sum()
    return {f: float(np.clip(roll.get(f, 0) / (total * float(mix[f])), 0.03, 0.95)) for f in FIELD}


def build_vacancies(hist: pd.DataFrame) -> pd.DataFrame:
    """Vacancies for graduates of the modelled institutions: national postings
    (MoLS LMI 2025) x the share of the field's graduates these institutions
    produce (see _modelled_share_by_field)."""
    scope = _modelled_share_by_field(hist)
    rows = []
    real = {}
    level = 1.0
    for y in reversed(YEARS):
        real[y] = level
        level /= 1 + GDP_G[y] / 100
    freeze = set(C.get("public_sector.hiring_freeze.years"))
    urban_weight = {r: POP[(r, 2022)] * _urban_share(r, 2022) for r in REGION_NAMES}
    urban_weight["Addis Ababa"] *= 2.2                     # formal vacancies concentrate in the capital
    tot_w = sum(urban_weight.values())
    for f in FIELDS:
        occ = f["occupation"]
        for region in REGION_NAMES:
            dev = _ar1(len(YEARS), VAC_PHI, VAC_SIGMA)
            prev = None
            for i, year in enumerate(YEARS):
                v = VACANCY_2025[occ] * scope[f["field"]] * real[year] * urban_weight[region] / tot_w
                if year == 2020:
                    v *= 0.8
                if occ in PUBLIC_OCCUPATIONS and year in freeze:
                    v *= 0.45
                v *= _labour_shock(region, f["sector"], year) ** 2
                v = max(0, int(round(v * float(np.exp(dev[i])))))
                trend = ((v / prev - 1) * 100) if prev else 0.0
                prev = v or prev
                exp_years = int(RNG.choice([0, 1, 2, 3, 4, 5], p=[0.1, 0.09, 0.25, 0.22, 0.2, 0.14]))
                rows.append({
                    "region": region, "year": year, "occupation": occ,
                    "occupation_frequency": v, "vacancy_count": v,
                    "required_education": "bachelor",
                    "required_experience_years": exp_years,
                    "hiring_trend_pct": round(float(np.clip(trend, -80, 200)), 2),
                    "time_to_fill_days": round(float(np.clip(RNG.normal(FILL_DAYS[occ], 6), 10, 150)), 1),
                    "sector": f["sector"], "field": f["field"],
                })
    return pd.DataFrame(rows)


def build_skills() -> pd.DataFrame:
    rows = []
    levels = C.get("employment.skill_shortage_level.values")
    for f in FIELDS:
        mu0 = float(levels[f["field"]])
        trend = {"Natural & Computational Sciences": 0.012, "Medicine & Health Sciences": 0.004,
                 "Social Sciences & Humanities": -0.006, "Business & Economics": -0.004}.get(f["field"], 0.0)
        shortage = mu0
        for year in YEARS:
            mu = mu0 + trend * (year - 2016)
            shortage = float(np.clip(mu + SKILL_PHI * (shortage - mu) + RNG.normal(0, SKILL_SIGMA), 0, 1))
            rows.append({
                "field": f["field"], "year": year,
                "technical_skill_demand": round(float(np.clip(RNG.normal(0.72 if f["stem"] else 0.45, 0.04), 0.1, 1)), 3),
                "digital_skill_demand": round(float(np.clip(0.45 + 0.03 * (year - 2016) + RNG.normal(0, 0.03), 0.1, 1)), 3),
                "soft_skill_demand": round(float(np.clip(RNG.normal(0.6, 0.04), 0.2, 1)), 3),
                "emerging_skill_demand": round(float(np.clip(0.3 + 0.035 * (year - 2016) + RNG.normal(0, 0.03), 0.05, 1)), 3),
                "skill_shortage_index": round(shortage, 4),
                "skill_oversupply_index": round(float(np.clip(0.75 - shortage + RNG.normal(0, 0.03), 0, 1)), 4),
            })
    return pd.DataFrame(rows)


def build_public_hiring() -> pd.DataFrame:
    rows = []
    stock = C.series("labour.civil_service.total", list(range(2015, 2026)))
    freeze = set(C.get("public_sector.hiring_freeze.years"))
    cap = C.series("public_sector.capital_budget_etb_bn", YEARS)
    mega = C.get("public_sector.megaprojects")
    pop_tot = {y: sum(POP[(r, y)] for r in REGION_NAMES) for y in YEARS}
    for region in REGION_NAMES:
        for year in YEARS:
            share = POP[(region, year)] / pop_tot[year] * (1.6 if region == "Addis Ababa" else 1.0)
            hires = max(stock[year] - stock[year - 1], 0) + stock[year] * 0.02        # growth + replacement
            state = "expansion"
            if year in freeze:
                hires *= 0.1
                state = "freeze"
            if region == "Tigray" and year in (2021, 2022):
                hires, state = 0, "freeze"                 # federal transfers frozen
            staffing = 150
            for m in mega:
                if m["region"] == region and m["start"] <= year and (m["end"] is None or year <= m["end"]):
                    staffing += int(m["workforce"])
            rows.append({
                "region": region, "year": year,
                "civil_service_hiring_plan": int(hires * share * RNG.uniform(0.9, 1.1)),
                "hiring_policy_state": state,
                "public_project_count": int(max(1, cap[year] / 10 * POP[(region, year)] / pop_tot[year] * 40
                                                 * (0.2 if region == "Tigray" and year in (2021, 2022) else 1))),
                "megaproject_staffing_demand": staffing,
            })
    return pd.DataFrame(rows)


def build_fdi() -> pd.DataFrame:
    rows = []
    fdi = C.series("investment.fdi_inflow_usd_bn", YEARS)
    licences = C.series("investment.investment_licences", YEARS)
    park_total = {y: sum(PARK_JOBS[(p["name"], y)] for p in INDUSTRIAL_PARKS) or 1 for y in YEARS}
    for park in INDUSTRIAL_PARKS:
        for year in YEARS:
            jobs = PARK_JOBS[(park["name"], year)]
            closed = park["name"] == "Mekelle Industrial Park" and year in (2021, 2022, 2023)
            open_ = year >= park["opened"] and not closed
            share = jobs / park_total[year]
            inflow = fdi[year] * 1e9 * 0.18 * share if open_ else 0
            rows.append({
                "region": park["region"], "year": year,
                "industrial_park": park["name"],
                "industrial_park_operational_flag": bool(open_),
                "fdi_inflow_usd": int(inflow * RNG.uniform(0.85, 1.15)),
                "new_investment_project_count": int(round(licences[year] * 0.3 * share)) if open_ else 0,
                "factory_expansion_count": int(round(share * 25 * RNG.uniform(0.6, 1.4))) if open_ else 0,
                "expected_employment": int(jobs),
                "private_investment_pipeline_etb": int(inflow * FX[year] * 0.4) if open_ else 0,
            })
    return pd.DataFrame(rows)


def build_macro_financial() -> pd.DataFrame:
    rows = []
    gdp_nominal = 1.53e12
    rate = {2016: 12.25, 2017: 12.25, 2018: 12.5, 2019: 12.75, 2020: 12.5, 2021: 13.0, 2022: 13.5,
            2023: 15.0, 2024: 17.0, 2025: 16.5}
    for year in YEARS:
        if year > YEARS[0]:
            gdp_nominal *= (1 + GDP_G[year] / 100) * (1 + CPI_INFL[year] / 100)
        rows.append({
            "year": year,
            "gdp_growth_rate_pct": GDP_G[year],
            "cpi_index": round(CPI[year], 2),
            "inflation_rate_pct": CPI_INFL[year],
            "exchange_rate_etb_usd": FX[year],
            "forex_reserve_months": RESERVES[year],
            "gross_investment_etb": int(gdp_nominal * (0.33 - 0.009 * (year - 2016))),
            "interest_rate_pct": rate[year],
        })
    return pd.DataFrame(rows)


RETURN_SHARE = {"Amhara": 0.28, "Oromia": 0.36, "Tigray": 0.1, "South Ethiopia": 0.07, "Central Ethiopia": 0.06,
                "Sidama": 0.03, "Addis Ababa": 0.04, "Somali": 0.02, "Afar": 0.01, "Dire Dawa": 0.01,
                "South West Ethiopia": 0.01, "Harari": 0.005, "Benishangul-Gumuz": 0.005, "Gambela": 0.005}


def build_labour_demographics() -> pd.DataFrame:
    rows = []
    returns = {y: 80000.0 for y in range(2016, 2023)}
    returns.update(C.series("labour.migration.returns_from_saudi", [2023, 2024, 2025]))
    for region in REGION_NAMES:
        for year in YEARS:
            skilled = 9000 * (1 + 0.06 * (year - 2016)) * POP[(region, year)] * _urban_share(region, year) / 25e6
            rows.append({
                "region": region, "year": year,
                "working_age_population": int(POP[(region, year)] * 0.56),
                "education_level_distribution": "mixed",
                "skilled_emigration_count": int(skilled * RNG.uniform(0.85, 1.15)),
                "return_migration_count": int(returns[year] * RETURN_SHARE[region] * RNG.uniform(0.9, 1.1)),
                "regional_absorption_rate": round(float(np.clip(
                    (1 - _regional_unemployment(region, year) / 100) * 0.6 + RNG.normal(0, 0.02), 0.05, 0.9)), 3),
            })
    return pd.DataFrame(rows)


def _shock_types(region: str, year: int) -> list[str]:
    kinds = []
    if year == 2020:
        kinds.append("covid")
    if region == "Tigray" and year in (2021, 2022, 2023):
        kinds.append("conflict")
    if region == "Amhara" and year in (2021, 2023, 2024, 2025):
        kinds.append("conflict")
    if region == "Afar" and year in (2021, 2022):
        kinds.append("conflict")
    if region == "Benishangul-Gumuz" and year in (2020, 2021):
        kinds.append("conflict")
    for s in C.get("agriculture.shocks"):
        if s["year"] == year and region in s["regions"] and ("drought" in s["event"] or "Nino" in s["event"]):
            kinds.append("drought")
    if region in ("Sidama", "Addis Ababa", "Tigray") and year == 2022:
        kinds.append("trade_shock")              # AGOA suspension hit the parks here
    return sorted(set(kinds))


def build_shocks() -> pd.DataFrame:
    rows = []
    for region in REGION_NAMES:
        for year in YEARS:
            kinds = _shock_types(region, year)
            rows.append({
                "region": region, "year": year,
                "agricultural_season": "meher",
                "hiring_season_index": round(float(0.7 - (0.15 if "conflict" in kinds else 0) + RNG.normal(0, 0.03)), 3),
                "commodity_price_index": round(float(CPI[year] * (1.12 if "drought" in kinds else 1.0)), 2),
                "external_shock_flag": bool(kinds),
                "shock_type": ",".join(kinds),
            })
    return pd.DataFrame(rows)


def build_demographics() -> pd.DataFrame:
    rows = []
    share = C.get("population.exam_taker_share.values")
    part = C.get("population.exam_participation.values")
    for year in YEARS:
        w = {r: float(share[r]) * float(part.get(r, {}).get(year, 1.0)) for r in REGION_NAMES}
        tot = sum(w.values())
        for region in REGION_NAMES:
            pop = POP[(region, year)]
            net = {"Addis Ababa": 0.012, "Dire Dawa": 0.004}.get(region, -0.001)
            if region == "Tigray" and year in (2021, 2022):
                net = -0.02
            rows.append({
                "region": region, "year": year,
                "grade12_completers_count": int(CAND[year] * w[region] / tot),
                "university_age_population": int(pop * 0.14),
                "regional_youth_population": int(pop * 0.20),
                "net_internal_migration": int(pop * net * RNG.uniform(0.8, 1.2)),
            })
    return pd.DataFrame(rows)


# ── compatibility shapes the older dashboards read ────────────────────────────

def build_jobs_compat(vacancies: pd.DataFrame, outcomes: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
    grads = hist.groupby(["field", "region", "year"])["program_enrollment_count"].sum()
    wage = C.get("employment.mean_monthly_wage_etb.by_sector_2021")
    rows = []
    rid = 0
    for r in vacancies.itertuples(index=False):
        rid += 1
        g = int(grads.get((r.field, r.region, r.year), 0) * 0.7)
        monthly = float(wage.get(r.sector, 4500)) * WAGE[r.year] / WAGE[2021]
        rows.append({
            "record_id": rid, "year": r.year, "month": 6, "quarter": 2,
            "job_title": r.occupation, "job_family": r.field,
            "soc_code": f"ETH-{abs(int.from_bytes(r.occupation.encode(), 'little')) % 1000:03d}",
            "skill_cluster": r.field, "country": "Ethiopia",
            "state_province": r.region, "metro_area": r.region,
            "remote_allowed": False, "posting_industry": r.sector,
            "relevant_graduates_count": g,
            "bootcamp_completions": int(g * 0.05),
            "supply_demand_ratio": g / max(r.vacancy_count, 1),
            "time_to_fill_days": r.time_to_fill_days,
            "job_openings_count": r.vacancy_count,
            "demand_growth_rate_pct": r.hiring_trend_pct,
            "avg_salary_usd": round(monthly * 12 / FX[r.year], 1),
            "avg_salary_etb": int(monthly * 12),
            "company_size": "medium",
        })
    return pd.DataFrame(rows)


def build_enrollment_compat(hist, funnel, finance, outcomes) -> pd.DataFrame:
    m = hist.merge(funnel, on=["institution", "campus", "region", "program", "field", "year"], how="left")
    m = m.merge(finance, on=["institution", "program", "field", "year"], how="left")
    m = m.merge(outcomes, on=["institution", "program", "field", "region", "year"], how="left")
    stem = {f["program"]: f["stem"] for f in FIELDS}
    return pd.DataFrame({
        "year": m["year"],
        "program_name": m["program"],
        "field_of_study": m["field"],
        "stem_designated": m["program"].map(stem).astype(int),
        "accreditation_status": "accredited",
        "institution_name": m["institution"],
        "institution_type": m["institution"].map(lambda n: HEI[n]["type"]),
        "institution_state": m["region"],
        "campus_setting": m["campus"],
        "tuition_usd": (m["tuition_fee_etb"] / m["year"].map(FX)).round(1),
        "tuition_etb": m["tuition_fee_etb"],
        "net_price": m["tuition_fee_etb"] * 0.7,
        "scholarship_availability": m["scholarship_availability"],
        "roi_10yr_usd": (m["median_earnings_etb"] * 8 / m["year"].map(FX)).round(0),
        "employment_rate_6mo_pct": m["graduate_employment_rate_pct"],
        "enrollment_count": m["program_enrollment_count"],
        "students_on_roll_count": m["students_on_roll_count"],
        "applications_count": m["applications_count"],
        "acceptance_rate_pct": np.where(m["applications_count"] > 0,
                                        m["offers_count"] / m["applications_count"].where(m["applications_count"] > 0) * 100, 0),
        "yield_rate_pct": m["yield_rate_pct"],
        "us_news_ranking": 0,
        "program_level": "bachelor",
        "delivery_mode": "in-person",
        "inquiry_count": (m["applications_count"] * 1.4).astype(int),
        "marketing_spend_usd": (m["program_enrollment_count"] * 120).astype(int),
        "competitor_programs_count": 7,
        "competitor_avg_tuition_usd": (m["tuition_fee_etb"] * 1.05 / m["year"].map(FX)).round(1),
        "median_salary_field_usd": (m["median_earnings_etb"] / m["year"].map(FX)).round(0),
    })


def write_reference() -> None:
    ref = OUT / "reference"
    ref.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(REGIONS).to_csv(ref / "regions.csv", index=False)
    pd.DataFrame(HEIS).to_csv(ref / "heis.csv", index=False)
    pd.DataFrame(FIELDS).to_csv(ref / "fields.csv", index=False)
    pd.DataFrame(INDUSTRIAL_PARKS).to_csv(ref / "industrial_parks.csv", index=False)
    print("  reference dimensions written")


def generate() -> dict[str, pd.DataFrame]:
    print("Generating Ethiopia fact tables (simulated, calibrated, 2016–2025)")
    problems = C.problems()
    if problems:
        raise SystemExit("calibration.yaml is malformed:\n  " + "\n  ".join(problems))
    write_reference()
    intake = _intake_panel()
    hist = build_enrollment_history(intake)
    quota = build_capacity_quota(hist, intake)
    funnel = build_admissions_funnel(hist, quota)
    exam = build_exam_placement()
    demo = build_demographics()
    cohort = build_cohort(hist)
    vac = build_vacancies(hist)
    skills = build_skills()
    outcomes = build_outcomes(hist, vac, skills)
    icap = build_institution_capacity(hist)
    finance = build_finance(hist)
    macro_r = build_macro_regional()
    labour = build_labour_history()
    sector = build_sector_output(labour)
    formal = build_formal_informal(labour)
    public = build_public_hiring()
    fdi = build_fdi()
    macro_f = build_macro_financial()
    lab_dem = build_labour_demographics()
    shocks = build_shocks()
    jobs = build_jobs_compat(vac, outcomes, hist)
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
