from fastapi import APIRouter, Depends, HTTPException, Query

from services import alignment_service as m3
from services import constraint_service as m1
from services import institution_service
from services.auth_service import (
    ROLE_ADMIN,
    ROLE_UNIVERSITY,
    assert_cross_institution,
    require_roles,
)

router = APIRouter(
    prefix="/institution",
    tags=["Institution (University)"],
)

_guard = require_roles(ROLE_UNIVERSITY)


def _institution_of(user: dict, requested: str | None = None) -> str:
    """Resolve which institution the caller may read.

    Own HEI comes from the signed JWT. A different `?institution=` is 403
    unless the CROSS_INSTITUTION grant is on the user record (SCOPE.UNI.R2).
    """
    own = user.get("institution")
    if not own and user.get("role") == ROLE_ADMIN:
        from services import _datasets as ds
        options = ds.institutions()
        if options:
            own = options[0]["name"]

    if requested and own and requested != own:
        return assert_cross_institution(user, requested)
    if requested and not own:
        return assert_cross_institution(user, requested)

    if own:
        return own
    raise HTTPException(
        status_code=403,
        detail="This account is not linked to an institution.",
    )


def _scope(user: dict = Depends(_guard), institution: str | None = Query(None)):
    return user, _institution_of(user, institution)


def _records(df):
    return m3.as_records(df)


@router.get("/me")  # /institution/me
def get_my_institution(scope: tuple = Depends(_scope)):
    """Profile of the caller's own institution."""
    _, inst = scope
    try:
        return institution_service.get_profile(inst)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio")
def get_portfolio(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        return institution_service.get_portfolio(inst)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expansion")
def get_expansion(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        return institution_service.get_expansion_opportunities(inst)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources")
def get_resources(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        return institution_service.get_resource_efficiency(inst)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/benchmark")
def get_benchmark(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        return institution_service.get_peer_benchmark(inst)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/program-health")  # /institution/program-health
def program_health(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        return m3.program_health(horizon=1, institution=inst)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/curriculum-alignment")  # /institution/curriculum-alignment
def curriculum_alignment(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        return m3.curriculum_alignment(horizon=1, institution=inst)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/demand-vs-labour")  # /institution/demand-vs-labour
def demand_vs_labour(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        df = m3.three_way(horizon=1, institution=inst)
        return {
            "n": int(len(df)),
            "series": ["student_demand", "expected_graduates", "labour_demand"],
            "rows": _records(df),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/funnel")  # /institution/funnel
def funnel(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        raw = m1.scope_to_institution(m1.admissions_funnel(), inst)
        constrained = m1.scope_to_institution(m1.constrained_demand(horizon=1), inst)
        bind = {}
        if not constrained.empty and "program" in constrained.columns:
            bind = (
                constrained.groupby("program")["binding_constraint"]
                .agg(lambda s: s.value_counts().index[0] if len(s) else "none")
                .to_dict()
            )
        rows = _records(raw)
        for row in rows:
            row["binding_constraint"] = bind.get(row.get("program"), "none")
        stages = {
            "applications": int(raw["applications_count"].sum()) if "applications_count" in raw.columns else 0,
            "offers_placement": int(raw["offers_count"].sum()) if "offers_count" in raw.columns else 0,
            "acceptance": int(raw["accepted_offers_count"].sum()) if "accepted_offers_count" in raw.columns else 0,
            "enrollment": int(constrained["constrained_enrollment"].sum()) if "constrained_enrollment" in constrained.columns else 0,
        }
        return {"institution": inst, "stages": stages, "n": int(len(raw)), "rows": rows}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cohort-progression")  # /institution/cohort-progression
def cohort_progression(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        df = m1.scope_to_institution(m1.cohort_progression(), inst)
        return {"institution": inst, "n": int(len(df)), "rows": _records(df)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graduate-outcomes")  # /institution/graduate-outcomes
def graduate_outcomes(scope: tuple = Depends(_scope)):
    _, inst = scope
    try:
        out = m1.scope_to_institution(m1.graduate_outcomes(), inst)
        cohort = m1.scope_to_institution(m1.cohort_progression(), inst)
        six = []
        try:
            from services import _datasets as ds
            e = ds.enrollment()
            sub = e[e["institution_name"] == inst] if "institution_name" in e.columns else e
            if not sub.empty and "employment_rate_6mo_pct" in sub.columns:
                by = sub.groupby("year")["employment_rate_6mo_pct"].mean()
                six = [{"year": int(y), "employed_within_6mo_pct": round(float(v), 1)} for y, v in by.items()]
        except Exception:
            six = []
        return {
            "institution": inst,
            "n": int(len(out)),
            "rows": _records(out),
            "cohort": _records(cohort),
            "time_to_employment": six,
            "time_to_employment_note": (
                "Share employed within six months from the enrollment compat table. "
                "Not time-to-graduation."
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resource-planning")  # /institution/resource-planning
def resource_planning(
    scope: tuple = Depends(_scope),
    quota_scale: float = Query(1.0, ge=0.25, le=3.0),
    capacity_scale: float = Query(1.0, ge=0.25, le=3.0),
):
    _, inst = scope
    try:
        return m3.resource_planning(inst, quota_scale=quota_scale, capacity_scale=capacity_scale)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
