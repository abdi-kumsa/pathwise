"""
Student dashboard slices (Wave 5.1).

Identity comes from student_scope (JWT sub). These functions never look up
another student by name. Field-level figures are aggregates with a minimum
cell size; smaller cells are withheld.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services.auth_service import MIN_CELL_SIZE, cell_released

from ml.features.model1 import c9_finance
from ml.features.model2 import c4_vacancies, c6_public
from ml.model1.layer1_demand import forecast_unconstrained
from ml.model2.forecast import forecast_vacancies
from ml.model3.gap import eligibility_by_field, supply_demand_gap


def profile(user: dict) -> dict:
    field = user.get("field")
    elig_pct = None
    elig = eligibility_by_field()
    if field and not elig.empty and "field" in elig.columns:
        hit = elig[elig["field"].astype(str) == str(field)]
        if not hit.empty:
            elig_pct = round(float(hit["eligibility_pct"].iloc[0]), 1)
    return {
        "username": user.get("username"),
        "display_name": user.get("display_name") or user.get("username"),
        "program": user.get("program"),
        "department": user.get("department") or None,
        "field": field,
        "institution": user.get("institution"),
        "enrollment_year": user.get("enrollment_year"),
        "enrollment_status": user.get("enrollment_status") or "enrolled",
        "eligibility": {
            "label": "Field accessibility (ESSLCE pass-rate proxy)",
            "pct": elig_pct,
            "note": (
                "This is the field's exam pass rate, not a personal exam score. "
                "It keeps recommendations realistic without ranking a student "
                "on a credential they have not sat."
            ),
        },
    }


def labour_outlook(field: str | None, horizons: tuple[int, ...] = (3, 5)) -> dict:
    series = {}
    occupations = []
    for h in horizons:
        vac = forecast_vacancies(horizon=h)
        if field and "field" in vac.columns:
            vac = vac[vac["field"].astype(str) == str(field)]
        if vac.empty:
            series[str(h)] = []
            continue
        by_year = vac.groupby("period", as_index=False)["vacancies"].sum()
        series[str(h)] = [
            {"period": int(r.period), "vacancies": round(float(r.vacancies), 1)}
            for r in by_year.itertuples(index=False)
        ]
        if not occupations:
            occ = vac.groupby("occupation", as_index=False)["vacancies"].sum()
            occupations = [
                {"occupation": r.occupation, "vacancies": round(float(r.vacancies), 1)}
                for r in occ.sort_values("vacancies", ascending=False).itertuples(index=False)
            ]
    n_occ = len(occupations)
    return {
        "field": field,
        "horizons": list(horizons),
        "series": series,
        "occupations": occupations if cell_released(n_occ) else [],
        "cell_withheld": not cell_released(n_occ) and n_occ > 0,
        "min_cell_size": MIN_CELL_SIZE,
        "note": "Projected occupational vacancies for the student's field. Simulated Ethiopian structure.",
    }


def demand_comparison(field: str | None) -> dict:
    unconstrained = forecast_unconstrained(horizon=1)
    if unconstrained.empty:
        return {"field": field, "rows": []}
    year = int(unconstrained["academic_year"].max())
    now = unconstrained[unconstrained["academic_year"] == year]
    popularity = now.groupby("field", as_index=False)["unconstrained_demand"].sum()
    gap = supply_demand_gap(horizon=1, group=("field", "period"))
    gap = gap[gap["period"] == gap["period"].max()] if not gap.empty else gap
    labour = gap[["field", "labour_demand", "expected_graduates", "status", "severity"]] if not gap.empty else pd.DataFrame()
    merged = popularity.merge(labour, on="field", how="outer")
    rows = []
    for r in merged.itertuples(index=False):
        pop = float(getattr(r, "unconstrained_demand", 0) or 0)
        lab = float(getattr(r, "labour_demand", 0) or 0)
        rows.append({
            "field": r.field,
            "student_demand": round(pop, 1),
            "labour_demand": round(lab, 1),
            "divergence": round(pop - lab, 1),
            "is_own_field": str(r.field) == str(field) if field else False,
            "status": getattr(r, "status", None),
            "severity": int(getattr(r, "severity", 0) or 0),
        })
    rows.sort(key=lambda x: abs(x["divergence"]), reverse=True)
    return {
        "field": field,
        "period": year,
        "rows": rows,
        "note": (
            "Student demand is unconstrained Model 1 enrolment pressure. "
            "Labour demand is Model 2 occupational vacancies. "
            "A large positive divergence means popularity outruns jobs."
        ),
    }


def opportunities(field: str | None, program: str | None) -> dict:
    """Simulated feed. Not official MoE/MoLS circulars."""
    items = []
    fin = c9_finance.frame()
    if not fin.empty:
        sub = fin
        if program and "program" in sub.columns:
            hit = sub[sub["program"].astype(str) == str(program)]
            if not hit.empty:
                sub = hit
        elif field and "field" in sub.columns:
            hit = sub[sub["field"].astype(str) == str(field)]
            if not hit.empty:
                sub = hit
        latest = int(sub["year"].max())
        now = sub[sub["year"] == latest]
        rate = float(now["scholarship_availability"].mean()) if "scholarship_availability" in now.columns else 0.2
        items.append({
            "kind": "scholarship",
            "title": "Need-based cost-sharing support",
            "detail": (
                f"Simulated scholarship availability around {round(rate * 100)}% of "
                f"{program or field or 'this field'} places in {latest}."
            ),
            "year": latest,
            "field": field,
            "program": program,
        })
        items.append({
            "kind": "training",
            "title": "Stipend-linked workplace attachment",
            "detail": "Simulated from finance-support stipend rows — not a named ministry scheme.",
            "year": latest,
            "field": field,
            "program": program,
        })

    vac = c4_vacancies.frame()
    if not vac.empty:
        if field and "field" in vac.columns:
            vac = vac[vac["field"].astype(str) == str(field)]
        if not vac.empty:
            latest = int(vac["year"].max())
            now = vac[vac["year"] == latest]
            top = now.sort_values("vacancy_count", ascending=False).iloc[0]
            items.append({
                "kind": "internship",
                "title": f"Vacancy-linked placement · {top.get('occupation', 'occupation')}",
                "detail": (
                    f"{int(top['vacancy_count'])} simulated openings in "
                    f"{top.get('region', 'Ethiopia')} ({latest}). Not a job-board scrape."
                ),
                "year": latest,
                "field": field,
                "occupation": top.get("occupation"),
            })
            items.append({
                "kind": "job_fair",
                "title": f"{top.get('sector', 'Sector')} hiring window",
                "detail": "Simulated seasonal hiring signal from the vacancies table.",
                "year": latest,
                "field": field,
            })

    pub = c6_public.frame()
    if not pub.empty and "hiring_policy_state" in pub.columns:
        latest = int(pub["year"].max())
        open_ = pub[(pub["year"] == latest) & (pub["hiring_policy_state"].astype(str) != "freeze")]
        if not open_.empty:
            items.append({
                "kind": "training",
                "title": "Public-sector intake (not frozen)",
                "detail": "Simulated civil-service hiring pipeline — authorised planning data analogue.",
                "year": latest,
                "field": field,
            })

    kinds = ["scholarship", "internship", "training", "job_fair"]
    return {
        "kinds": kinds,
        "items": items,
        "official": False,
        "note": (
            "No official MoE or MoLS opportunities circular is on file. "
            "This feed is assembled from the simulated finance and vacancy tables."
        ),
    }
