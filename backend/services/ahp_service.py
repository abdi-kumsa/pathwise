"""AHP persistence and HTTP-facing helpers. Never imported by a learner."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi import HTTPException

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from ml.ahp import AhpRefused, consistency_ratio, display_ranks, weigh  # noqa: E402


def evaluate_consistency(matrix: list[list[float]]) -> dict:
    try:
        return consistency_ratio(matrix)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def compute_weights(matrix: list[list[float]], labels: list[str] | None, model: str) -> dict:
    if model not in {"M1", "M2", "M3"}:
        raise HTTPException(status_code=422, detail="model must be M1, M2 or M3")
    try:
        result = weigh(matrix, labels)
    except AhpRefused as exc:
        raise HTTPException(status_code=422, detail=exc.detail) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result["model"] = model
    return result


def persist_matrix(model: str, matrix: list[list[float]], consistency: float | None) -> None:
    from db.database import SessionLocal
    from models.governance import AhpMatrix

    session = SessionLocal()
    try:
        session.add(AhpMatrix(
            model=model,
            matrix=matrix,
            consistency_ratio=consistency,
        ))
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()


def latest(model: str | None = None) -> dict:
    from db.database import SessionLocal
    from models.governance import AhpMatrix
    from sqlalchemy import desc

    session = SessionLocal()
    try:
        q = session.query(AhpMatrix)
        if model:
            q = q.filter(AhpMatrix.model == model)
        row = q.order_by(desc(AhpMatrix.created_at)).first()
        if row is None:
            return {
                "weights": None,
                "consistency_ratio": None,
                "matrix": None,
                "model": model,
                "refused": False,
            }
        try:
            weighed = weigh(row.matrix, None)
            payload = {**weighed, "model": row.model, "id": row.id}
        except AhpRefused as exc:
            payload = {**exc.detail, "model": row.model, "id": row.id}
        except ValueError:
            payload = {
                "weights": None,
                "consistency_ratio": float(row.consistency_ratio) if row.consistency_ratio is not None else None,
                "matrix": row.matrix,
                "model": row.model,
                "id": row.id,
                "refused": True,
            }
        payload["matrix"] = row.matrix
        payload["created_at"] = row.created_at.isoformat() if row.created_at else None
        return payload
    finally:
        session.close()


def hybrid_display(ahp_weights: dict[str, float], learned_rows: list[dict]) -> list[dict]:
    return display_ranks(ahp_weights, learned_rows)
