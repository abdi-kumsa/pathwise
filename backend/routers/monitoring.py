from fastapi import APIRouter, HTTPException, Query

from services import monitoring_service

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/drift")
def get_drift(
    window: int = Query(
        100,
        description="Number of recent predictions to analyse for drift detection",
    )
):
    """Drift report: compares recent prediction probabilities to the
    training-time baseline (0.88).

    Use this endpoint to detect model degradation over time without
    needing access to the server.  An `alert: true` response means the
    mean placement probability has drifted more than 10 percentage
    points from the baseline — trigger a retrain.
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
