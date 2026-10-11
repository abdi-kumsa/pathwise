"""DOC1 methodology steps 2–6. ADMIN-only."""
from fastapi import APIRouter, Depends, HTTPException

from services import methodology_service
from services.auth_service import ROLE_ADMIN, log_audit, require_roles

router = APIRouter(
    prefix="/methodology",
    tags=["Methodology"],
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)

_admin = require_roles(ROLE_ADMIN)


@router.get("/feature-importance")  # /methodology/feature-importance
def feature_importance():
    try:
        return methodology_service.feature_importance()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/feature-importance")
def run_feature_importance(actor: dict = Depends(_admin)):
    try:
        payload = methodology_service.run_feature_importance()
        log_audit(actor, "model_run", "feature-importance")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/priority-tiers")  # /methodology/priority-tiers
def priority_tiers():
    try:
        return methodology_service.priority_tiers()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/model-comparison")  # /methodology/model-comparison
def model_comparison():
    try:
        return methodology_service.model_comparison()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/model-comparison")
def run_model_comparison(actor: dict = Depends(_admin)):
    try:
        payload = methodology_service.run_model_comparison()
        log_audit(actor, "model_run", "model-comparison")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/expert-validations")  # /methodology/expert-validations
def list_expert_validations():
    try:
        return methodology_service.list_expert_validations()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/expert-validations")
def create_expert_validation(body: dict, actor: dict = Depends(_admin)):
    try:
        row = methodology_service.create_expert_validation(
            spec_id=body.get("spec_id") or "",
            expert_role=body.get("expert_role") or "",
            verdict=body.get("verdict") or "",
            notes=body.get("notes"),
        )
        log_audit(actor, "model_run", f"expert-validation:{row.get('spec_id')}", {
            "verdict": row.get("verdict"),
        })
        return row
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
