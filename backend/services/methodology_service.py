"""
DOC1 procedure steps 2–6 — expert sign-off, tiers, comparison, two-panel importance.

Learned importance and collection priority are assembled as sibling keys. There
is no blended score. collection_priority is read here for display only; it is
never imported from ml/.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import spec_registry as S
except ImportError:
    from backend import spec_registry as S

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_ML_MODELS = _ROOT / "ml" / "models"
_COMPARISON = _ML_MODELS / "ethiopia_comparison.json"
_M1_CMP = _ML_MODELS / "model1_layer1_comparison.json"
_M2_CMP = _ML_MODELS / "model2_comparison.json"
_ETH_IMP = _ML_MODELS / "ethiopia_feature_importance.json"

EXPERT_DOMAINS = next(
    s["expert_domains"] for s in S.procedure() if s["id"] == "PROC.S2"
)
VERDICTS = ("accepted", "revision", "rejected")


def _read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return None


def _mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def priority_tiers() -> dict:
    """PROC.S3 — M1 70/18/12 and M2 55/30/15."""
    return {
        "model1": S.priority_tiers("model1"),
        "model2": S.priority_tiers("model2"),
        "note": (
            "Tiers are data-collection priorities, not model weights. "
            "DOC1: 70/18/12 (M1) and 55/30/15 (M2)."
        ),
    }


def collection_priority_panel() -> list[dict]:
    rows = []
    for model in S.models():
        for cat in S.categories(model):
            rows.append({
                "id": cat["id"],
                "name": cat["name"],
                "model": S.load(model)["model"]["id"],
                "collection_priority": cat["collection_priority"],
                "source_table": cat.get("source_table"),
            })
    return rows


def model_comparison() -> dict:
    """PROC.S4. Prefer the facade cache; fall back to per-model JSON."""
    cached = _read_json(_COMPARISON)
    if cached and cached.get("targets"):
        cached["last_retrained"] = _mtime(_COMPARISON)
        return cached
    m1 = _read_json(_M1_CMP) or {}
    m2 = _read_json(_M2_CMP) or {}
    return {
        "validation": "grouped chronological holdout (last two observed years per series)",
        "random_split": False,
        "targets": [
            {
                "id": "M1.enrollment",
                "target": m1.get("target", "program_enrollment_count"),
                "candidates": sorted((m1.get("estimators") or {}).keys()),
                **m1,
            },
            {
                "id": "M2.employment",
                "target": m2.get("target", "employment_level"),
                "candidates": sorted((m2.get("estimators") or {}).keys()),
                **m2,
            },
        ],
        "us_models_not_compared": sorted(set(
            list(m1.get("not_compared") or [])
            + list(m2.get("not_compared") or [])
        )),
        "last_retrained": _mtime(_M1_CMP) or _mtime(_M2_CMP),
        "cached": False,
    }


def run_model_comparison() -> dict:
    from ml.compare_models import compare_all
    return compare_all()


def feature_importance() -> dict:
    """W.ADM.04 / PROC.S5–S6. Two labelled panels; never_merged."""
    learned = {
        "placement": _placement_shap(),
        "model1": {"method": "model_based_importance", "rows": []},
        "model2": {"method": "model_based_importance", "rows": []},
    }
    ethiopia = _ethiopia_importance()
    if ethiopia:
        for key in ("model1", "model2"):
            block = ethiopia.get(key) or {}
            learned[key] = {
                "method": "model_based_importance",
                "also": ["shap_linear_exact", "permutation_importance"],
                "model": block.get("model"),
                "target": block.get("target"),
                "model_based": block.get("model_based") or [],
                "shap": block.get("shap") or [],
                "permutation": block.get("permutation") or [],
                "rows": block.get("model_based") or [],
                "coefficients": block.get("coefficients"),
                "holdout_rmse": block.get("holdout_rmse"),
                "holdout_rmse_no_change": block.get("holdout_rmse_no_change"),
                "split": block.get("split"),
                "features_from": block.get("features_from"),
            }
    # The pooled learners use only the target's own history. Every other DOC1
    # column is collected but not a learner input, and is listed as such.
    used = {
        "model1": ["applications_count"],
        "model2": ["employment_level", "employment_lag_1y", "employment_lag_2y"],
    }
    unused = []
    for model_key, mid in (("model1", "M1"), ("model2", "M2")):
        used_cols = set(used[model_key])
        for var in S.variables(model_key if model_key == "model1" else "model2"):
            for col in S.columns_for(var):
                if col not in used_cols:
                    unused.append({
                        "model": mid,
                        "column": col,
                        "variable": var.get("id"),
                        "unused_by_learner": True,
                    })
                    used_cols.add(col)
    return {
        "panels": ["learned_importance", "collection_priority"],
        "never_merged": True,
        "learned_importance": learned,
        "collection_priority": collection_priority_panel(),
        "unused_by_learner": unused,
        "note": (
            "Ethiopia M1/M2 importance comes from the pooled ridge the forecasts use, "
            "trained on earlier years and explained on later ones. Its two inputs are "
            "derived from the target's own history; other DOC1 columns are collected "
            "and unused by the learner. Placement SHAP is a leftover US tool."
        ),
        "us_models_not_compared": (ethiopia or {}).get("not_compared") or [
            "US LSTM (ml/models/enrollment_lstm.keras)",
            "US Prophet (ml/models/demand_prophet.pkl)",
        ],
    }


def run_feature_importance() -> dict:
    from ml.explain_predictions import ethiopia_feature_importance
    ethiopia_feature_importance(persist=True)
    return feature_importance()


def _ethiopia_importance() -> dict | None:
    return _read_json(_ETH_IMP)


def _placement_shap() -> dict:
    from services.feature_flags import LEGACY_US_MODELS
    if not LEGACY_US_MODELS:
        return {
            "method": "shap",
            "available": False,
            "rows": [],
            "note": (
                "Placement SHAP belongs to the leftover US placement model, which is "
                "switched off (LEGACY_US_MODELS=0). It is not an Ethiopia model."
            ),
        }
    try:
        from services import ml_service
        shap_values, base_val, feature_names, _X = ml_service.get_shap_cache()
        import numpy as np
        mean_abs = np.abs(shap_values).mean(axis=0)
        ranked = sorted(
            zip(feature_names, mean_abs),
            key=lambda x: x[1],
            reverse=True,
        )
        return {
            "method": "shap",
            "base_value": round(float(np.mean(np.atleast_1d(base_val))), 4),
            "rows": [
                {"feature": name, "importance": round(float(val), 6), "method": "shap"}
                for name, val in ranked[:20]
            ],
        }
    except Exception:
        metrics = _read_json(_ML_MODELS / "model_metrics.json") or {}
        top = (metrics.get("xgboost_placement") or {}).get("top_features") or {}
        return {
            "method": "model_based_importance",
            "rows": [
                {"feature": k, "importance": v, "method": "model_based_importance"}
                for k, v in sorted(top.items(), key=lambda kv: kv[1], reverse=True)
            ],
        }


def _valid_spec_ids() -> set[str]:
    ids = set()
    for model in S.models():
        for cat in S.categories(model):
            ids.add(cat["id"])
        for var in S.variables(model):
            ids.add(var["id"])
    return ids


def list_expert_validations() -> dict:
    """PROC.S2 records plus validation coverage.

    Coverage counts *recorded* reviews only. Seeded demonstration rows are
    returned (flagged) so the page is not empty in a demo, but never count as
    validation. They are created only in development.
    """
    from db.database import SessionLocal
    from models.governance import ExpertValidation
    from services.auth_service import IS_DEV

    session = SessionLocal()
    try:
        rows = session.query(ExpertValidation).order_by(ExpertValidation.created_at.desc()).all()
        if not rows and IS_DEV:
            rows = _seed_expert_validations(session)
        out = [_expert_row(r) for r in rows]
    finally:
        session.close()
    return {
        "n": len(out),
        "expert_domains": EXPERT_DOMAINS,
        "verdicts": list(VERDICTS),
        "coverage": _coverage(out),
        "rows": out,
    }


def _coverage(rows: list[dict]) -> dict:
    """Which domains and categories have a real (recorded) review, and the
    latest recorded verdict per category."""
    recorded = [r for r in rows if r["source"] == "recorded"]
    by_domain = {d: 0 for d in EXPERT_DOMAINS}
    for r in recorded:
        by_domain[r["expert_role"]] = by_domain.get(r["expert_role"], 0) + 1
    categories = [c["id"] for m in S.models() for c in S.categories(m)]
    latest: dict[str, dict] = {}
    for r in sorted(recorded, key=lambda r: r["created_at"] or ""):
        cat = ".".join(r["spec_id"].split(".")[:2])
        latest[cat] = {"verdict": r["verdict"], "expert_role": r["expert_role"],
                       "expert_name": r["expert_name"], "at": r["created_at"]}
    accepted = [c for c in categories if latest.get(c, {}).get("verdict") == "accepted"]
    return {
        "recorded_reviews": len(recorded),
        "seeded_rows": len(rows) - len(recorded),
        "domains_with_a_review": sum(1 for v in by_domain.values() if v),
        "domains_total": len(EXPERT_DOMAINS),
        "reviews_by_domain": by_domain,
        "categories_total": len(categories),
        "categories_accepted": len(accepted),
        "latest_by_category": latest,
        "complete": all(by_domain.values()) and len(accepted) == len(categories),
        "note": (
            "Only recorded reviews count. PROC.S2 is complete when every expert domain "
            "has reviewed and every DOC1 category's latest recorded verdict is accepted."
        ),
    }


def create_expert_validation(
    *,
    spec_id: str,
    expert_role: str,
    verdict: str,
    expert_name: str,
    organisation: str,
    notes: str | None = None,
    recorded_by: str | None = None,
) -> dict:
    from fastapi import HTTPException
    from db.database import SessionLocal
    from models.governance import ExpertValidation

    if spec_id not in _valid_spec_ids():
        raise HTTPException(status_code=422,
                            detail=f"spec_id {spec_id!r} is not a DOC1 category or variable id")
    if expert_role not in EXPERT_DOMAINS:
        raise HTTPException(status_code=422, detail=f"expert_role must be one of {EXPERT_DOMAINS}")
    if verdict not in VERDICTS:
        raise HTTPException(status_code=422, detail=f"verdict must be one of {VERDICTS}")
    if not (expert_name or "").strip() or not (organisation or "").strip():
        raise HTTPException(status_code=422,
                            detail="A recorded review needs the expert's name and organisation")

    session = SessionLocal()
    try:
        row = ExpertValidation(
            spec_id=spec_id, expert_role=expert_role, verdict=verdict, notes=notes,
            expert_name=expert_name.strip(), organisation=organisation.strip(),
            recorded_by=recorded_by, source="recorded",
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return _expert_row(row)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def clear_seeded_expert_validations() -> int:
    """Remove the demonstration rows (before real reviews are entered)."""
    from db.database import SessionLocal
    from models.governance import ExpertValidation

    session = SessionLocal()
    try:
        n = session.query(ExpertValidation).filter(ExpertValidation.source == "seeded").delete()
        session.commit()
        return int(n)
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def export_expert_validations_csv() -> str:
    """The attribute list with its latest recorded verdict — what PROC.S2 asks
    to be validated, in a form a ministry reviewer can sign off."""
    import csv
    import io

    data = list_expert_validations()
    latest = data["coverage"]["latest_by_category"]
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["category_id", "category", "model", "collection_priority_pct",
                "latest_verdict", "expert_role", "expert_name", "reviewed_at"])
    for model in S.models():
        mid = S.load(model)["model"]["id"]
        for cat in S.categories(model):
            rec = latest.get(cat["id"], {})
            w.writerow([cat["id"], cat["name"], mid, cat.get("collection_priority"),
                        rec.get("verdict", "not reviewed"), rec.get("expert_role", ""),
                        rec.get("expert_name", ""), rec.get("at", "")])
    return buf.getvalue()


def _seed_expert_validations(session) -> list:
    from models.governance import ExpertValidation

    seeds = [
        ("M1.C1", "higher_education", "accepted", "Enrolment history is the right demand spine."),
        ("M1.C4", "ministry_of_education", "accepted", "Quota tables match placement practice."),
        ("M2.C3", "labour_and_skills", "revision", "Formal/informal split needs a ministry refresh."),
        ("M2.C1", "statistics", "accepted", "Labour history grain is usable for a simulated series."),
        ("M1.C10", "economics", "accepted", "Macro-regional context is a collection priority, not a weight."),
        ("M2.C7", "sector_specialist", "accepted", "FDI parks are leading indicators, displayed separately."),
    ]
    rows = []
    for spec_id, role, verdict, notes in seeds:
        row = ExpertValidation(spec_id=spec_id, expert_role=role, verdict=verdict,
                               notes=notes, source="seeded",
                               expert_name="(demonstration row)", organisation="—")
        session.add(row)
        rows.append(row)
    try:
        session.commit()
        for row in rows:
            session.refresh(row)
    except Exception:
        session.rollback()
        return []
    return rows


def _expert_row(row) -> dict:
    source = getattr(row, "source", None) or "recorded"
    return {
        "id": row.id,
        "spec_id": row.spec_id,
        "expert_role": row.expert_role,
        "verdict": row.verdict,
        "notes": row.notes,
        "expert_name": getattr(row, "expert_name", None),
        "organisation": getattr(row, "organisation", None),
        "recorded_by": getattr(row, "recorded_by", None),
        "source": source,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "tier": "simulated" if source == "seeded" else "recorded",
    }


