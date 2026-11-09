from fastapi import APIRouter, Depends, HTTPException, Query

from services import monitoring_service
from services.auth_service import require_roles, ROLE_ADMIN

# Model drift and the raw prediction log are operator concerns — ADMIN only.
router = APIRouter(
    prefix="/monitoring",
    tags=["Monitoring"],
    dependencies=[Depends(require_roles(ROLE_ADMIN))],
)


@router.get("/drift")  # /monitoring/drift
def get_drift(
    window: int = Query(
        100,
        description="Number of recent predictions to analyse for drift detection",
    )
):
    """Drift report for the Ethiopia forecasts (W.ADM.03).

    Per target: PSI of each model input in the latest year against the
    reference years, and the selected model's latest backtest error against
    its earlier origins. `alert: true` means at least one target shifted or
    degraded — re-run the model comparison. A secondary `placement` block
    covers the leftover US model when LEGACY_US_MODELS=1.
    """
    try:
        return monitoring_service.get_drift_report(window=window)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/predictions")
def get_recent_predictions(
    n: int = Query(20, description="Number of most-recent predictions to return"),
):
    """Return the last *n* raw prediction log entries for manual inspection."""
    try:
        return monitoring_service.get_recent_predictions(n=n)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
