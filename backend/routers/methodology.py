"""DOC1 methodology steps 2–6. ADMIN-only."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

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


class ExpertValidationIn(BaseModel):
    spec_id: str = Field(..., max_length=32, description="DOC1 category or variable id, e.g. M1.C2")
    expert_role: str = Field(..., max_length=64)
    verdict: str = Field(..., max_length=24)
    expert_name: str = Field(..., min_length=2, max_length=120)
    organisation: str = Field(..., min_length=2, max_length=160)
    notes: Optional[str] = Field(None, max_length=2000)


@router.post("/expert-validations")
def create_expert_validation(body: ExpertValidationIn, actor: dict = Depends(_admin)):
    """Record one expert's judgement on a DOC1 attribute (PROC.S2).

    The administrator enters it on the expert's behalf; the expert's name and
    organisation are required and the entry is audited under the admin.
    """
    try:
        row = methodology_service.create_expert_validation(
            **body.model_dump(), recorded_by=actor.get("username"),
        )
        log_audit(actor, "expert_validation", f"expert-validation:{row.get('spec_id')}", {
            "verdict": row.get("verdict"), "expert_role": row.get("expert_role"),
            "expert_name": row.get("expert_name"),
        })
        return row
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/expert-validations/clear-seeded")
def clear_seeded(actor: dict = Depends(_admin)):
    """Delete the demonstration rows so only real reviews remain."""
    try:
        n = methodology_service.clear_seeded_expert_validations()
        log_audit(actor, "expert_validation", "clear-seeded", {"deleted": n})
        return {"deleted": n}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/expert-validations/export")
def export_expert_validations(actor: dict = Depends(_admin)):
    """CSV of every DOC1 category with its latest recorded verdict."""
    try:
        body = methodology_service.export_expert_validations_csv()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    log_audit(actor, "report_export", "expert-validations", {"format": "csv"})
    return Response(content=body, media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="expert-validations.csv"'})
