"""Admin ops and governance. ADMIN-only. SCOPE.ADM."""
from fastapi import APIRouter, Depends, HTTPException, Query

from services import admin_service
from services.auth_service import ROLE_ADMIN, require_roles

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)

_admin = require_roles(ROLE_ADMIN)


@router.get("/platform-health")  # /admin/platform-health
def platform_health():
    try:
        return admin_service.platform_health()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pipeline-status")  # /admin/pipeline-status
def pipeline_status():
    try:
        return admin_service.pipeline_status()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/data-quality")  # /admin/data-quality
def data_quality():
    try:
        return admin_service.data_quality()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/audit-log")  # /admin/audit-log
def audit_log(
    actor: str | None = Query(None),
    action: str | None = Query(None),
    resource: str | None = Query(None),
    since: str | None = Query(None),
    until: str | None = Query(None),
):
    """Searchable audit rows, newest first. This GET is not itself logged."""
    try:
        return admin_service.list_audit_log(
            actor=actor, action=action, resource=resource, since=since, until=until,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/scenarios")  # /admin/scenarios
def list_scenarios():
    try:
        return admin_service.list_scenarios()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/scenarios/{scenario_id}")
def patch_scenario(
    scenario_id: int,
    body: dict,
    actor: dict = Depends(_admin),
):
    """Approve / reject / archive. Does not flip official_forecast."""
    status = (body or {}).get("status")
    if not status:
        raise HTTPException(status_code=422, detail="status is required")
    try:
        return admin_service.patch_scenario(scenario_id, status=status, actor=actor)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
