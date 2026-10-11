"""DOC1 step 7 — AHP. ADMIN-only. Weights refused when CR > 0.1."""
from fastapi import APIRouter, Depends, HTTPException

from services import ahp_service
from services.auth_service import ROLE_ADMIN, log_audit, require_roles

router = APIRouter(
    prefix="/ahp",
    tags=["AHP"],
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)

_admin = require_roles(ROLE_ADMIN)


@router.get("/weights")  # /ahp/weights
def get_weights(model: str | None = None):
    try:
        return ahp_service.latest(model)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/weights")  # /ahp/weights
def post_weights(body: dict, actor: dict = Depends(_admin)):
    matrix = body.get("matrix")
    labels = body.get("labels")
    model = body.get("model") or "M1"
    if not isinstance(matrix, list):
        raise HTTPException(status_code=422, detail="matrix is required")
    result = ahp_service.compute_weights(matrix, labels, model)
    ahp_service.persist_matrix(model, matrix, result.get("consistency_ratio"))
    log_audit(actor, "model_run", f"ahp-weights:{model}", {
        "consistency_ratio": result.get("consistency_ratio"),
        "refused": result.get("refused"),
    })
    learned = body.get("learned") or []
    if result.get("weights") and learned:
        result["display_ranks"] = ahp_service.hybrid_display(result["weights"], learned)
    return result


@router.get("/consistency")  # /ahp/consistency
def get_consistency(model: str | None = None):
    latest = ahp_service.latest(model)
    return {
        "consistency_ratio": latest.get("consistency_ratio"),
        "usable": bool(latest.get("weights")) and not latest.get("refused"),
        "model": latest.get("model"),
        "refused": latest.get("refused"),
    }


@router.post("/consistency")  # /ahp/consistency
def post_consistency(body: dict):
    matrix = body.get("matrix")
    if not isinstance(matrix, list):
        raise HTTPException(status_code=422, detail="matrix is required")
    return ahp_service.evaluate_consistency(matrix)
