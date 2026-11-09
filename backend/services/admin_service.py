"""
Admin ops and governance — platform health, pipeline, quality, audit, scenarios.

W.ADM.01 wraps /health; W.ADM.02 lists every registry source_table; W.ADM.06
scans Ethiopia parquets. Audit-log GET is searchable and is itself not logged.
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import desc

from services._cache import ttl_cache
from services._validate import ETHIOPIA, validate_ethiopia

try:
    import spec_registry as S
except ImportError:
    from backend import spec_registry as S

_STARTED = time.time()

# widgets.yaml feed_families. Every registry table is tagged once.
_FEED_FAMILY = {
    "enrollment_history": "education",
    "admissions_funnel": "education",
    "exam_placement": "education",
    "demographics": "education",
    "cohort_progression": "education",
    "graduate_outcomes": "education",
    "labour_history": "labor",
    "sector_output": "labor",
    "formal_informal": "labor",
    "vacancies": "labor",
    "skills_demand": "labor",
    "labour_demographics": "labor",
    "capacity_quota": "policy",
    "public_hiring": "policy",
    "shocks_seasonality": "policy",
    "finance_support": "policy",
    "fdi_industrial": "investment",
    "macro_financial": "investment",
    "institution_capacity": "investment",
    "macro_regional": "investment",
}

_SCENARIO_STATUSES = ("draft", "submitted", "approved", "rejected", "archived")


def _iso_mtime(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def _uptime() -> dict:
    seconds = int(time.time() - _STARTED)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    return {
        "uptime_seconds": seconds,
        "uptime": f"{hours}h {minutes}m {secs}s",
        "started_at": datetime.fromtimestamp(_STARTED, tz=timezone.utc).isoformat(),
    }


def platform_health() -> dict:
    """W.ADM.01 — wrap /health with user counts and process uptime."""
    from db.database import SessionLocal
    from models.user import User
    from services import ml_service
    from services.auth_service import ALL_ROLES

    from services.feature_flags import LEGACY_US_MODELS

    # With the leftover US artefacts switched off there is nothing to load;
    # reporting "0/5 loaded" would read as an outage that is not happening.
    models = ml_service.loaded_status() if LEGACY_US_MODELS else {}
    loaded = sum(1 for v in models.values() if v)
    session = SessionLocal()
    try:
        rows = session.query(User).all()
    finally:
        session.close()
    by_role = {role: 0 for role in ALL_ROLES}
    active = 0
    for row in rows:
        by_role[row.role] = by_role.get(row.role, 0) + 1
        if row.is_active:
            active += 1
    api_status = "ok" if all(models.values()) else "degraded"
    return {
        "api_status": api_status,
        "status": api_status,
        "models": models,
        "models_loaded": loaded,
        "models_total": len(models),
        "legacy_us_models": LEGACY_US_MODELS,
        "users": {
            "total": len(rows),
            "active": active,
            "by_role": by_role,
        },
        **_uptime(),
        "tier": "simulated",
    }


@ttl_cache
def pipeline_status() -> dict:
    """W.ADM.02 — status list of all 20 source_tables."""
    validate_errors = validate_ethiopia()
    errors_by_table: dict[str, list[str]] = {}
    for err in validate_errors:
        table = err.split(":", 1)[0].strip()
        errors_by_table.setdefault(table, []).append(err)

    feeds = []
    for table, cats in sorted(S.source_tables().items()):
        parquet = ETHIOPIA / f"{table}.parquet"
        csv = ETHIOPIA / f"{table}.csv"
        path = parquet if parquet.exists() else csv if csv.exists() else None
        family = _FEED_FAMILY.get(table, "education")
        feed = {
            "source_table": table,
            "family": family,
            "categories": cats,
            "exists": path is not None,
            "rows": 0,
            "year_min": None,
            "year_max": None,
            "last_sync": _iso_mtime(path) if path else None,
            "freshness": "missing",
            "status": "error",
            "status_label": "error",
            "errors": list(errors_by_table.get(table) or []),
            "tier": "simulated",
        }
        if path is not None:
            try:
                import pandas as pd
                df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
                feed["rows"] = int(len(df))
                # Tier comes from the file itself, so an ingested official
                # table shows as official (scripts/ingest_official.py).
                if "provenance" in df.columns and len(df):
                    tiers = set(df["provenance"].dropna().astype(str))
                    feed["tier"] = tiers.pop() if len(tiers) == 1 else "mixed"
                for col in ("source", "vintage"):
                    if col in df.columns and len(df) and df[col].notna().any():
                        feed[col] = str(df[col].dropna().iloc[0])
                if "year" in df.columns and len(df):
                    feed["year_min"] = int(df["year"].min())
                    feed["year_max"] = int(df["year"].max())
                    feed["freshness"] = "current" if feed["year_max"] >= 2025 else "stale"
            except Exception as exc:
                feed["errors"].append(f"{table}: read failed ({exc.__class__.__name__})")
            if feed["errors"]:
                feed["status"] = "warning"
                feed["status_label"] = "warning"
            else:
                feed["status"] = "ok"
                feed["status_label"] = "ok"
        feeds.append(feed)

    families = sorted({f["family"] for f in feeds})
    tiers = {f["tier"] for f in feeds}
    return {
        "n": len(feeds),
        "feeds": feeds,
        "families": families,
        "tier": tiers.pop() if len(tiers) == 1 else "mixed",
        "official_tables": sorted(f["source_table"] for f in feeds if f["tier"] == "official"),
    }


@ttl_cache
def data_quality() -> dict:
    """W.ADM.06 — alert list: missing, duplicates, outliers, inconsistent."""
    import pandas as pd

    alerts: list[dict] = []
    contract: dict[str, list[str]] = {}
    for err in validate_ethiopia():
        contract.setdefault(err.split(":", 1)[0].strip(), []).append(err)

    for table in sorted(S.source_tables()):
        parquet = ETHIOPIA / f"{table}.parquet"
        csv = ETHIOPIA / f"{table}.csv"
        path = parquet if parquet.exists() else csv if csv.exists() else None
        if path is None:
            alerts.append(_alert("critical", table, "inconsistent_records", f"{table}: file missing", 1))
            continue
        try:
            df = pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)
        except Exception as exc:
            alerts.append(_alert(
                "critical", table, "inconsistent_records",
                f"{table}: could not read ({exc.__class__.__name__})", 1,
            ))
            continue

        nulls = int(df.isna().sum().sum())
        if nulls:
            alerts.append(_alert(
                "high" if nulls > 100 else "moderate",
                table, "missing_values",
                f"{table}: {nulls} missing values",
                nulls,
            ))

        dupes = int(df.duplicated().sum())
        if dupes:
            alerts.append(_alert(
                "high", table, "duplicates",
                f"{table}: {dupes} duplicate rows",
                dupes,
            ))

        outlier_n = _iqr_outliers(df)
        if outlier_n:
            alerts.append(_alert(
                "moderate", table, "outliers",
                f"{table}: {outlier_n} numeric IQR outliers",
                outlier_n,
            ))

        # Contract errors include tier problems: an official row without a
        # source, or a tier other than simulated / official / derived. A table
        # that is correctly official is not an alert.
        for msg in contract.get(table) or []:
            alerts.append(_alert("high", table, "inconsistent_records", msg, 1))

    # Cross-table consistency rules (ml/consistency.py): the checks an
    # official file must also pass, e.g. funnel order and true lag columns.
    try:
        from ml.consistency import run_rules
        for r in run_rules():
            if r["status"] == "fail":
                alerts.append(_alert(
                    r["severity"], r["table"], "inconsistent_records",
                    f"{r['table']}: {r['rule']} — {r['description']} ({r['violations']} row(s))",
                    r["violations"],
                ))
            elif r["status"] == "missing table":
                alerts.append(_alert("moderate", r["table"], "inconsistent_records",
                                     f"{r['table']}: {r['rule']} could not run (table missing)", 1))
    except Exception as exc:
        alerts.append(_alert("moderate", "consistency", "inconsistent_records",
                             f"consistency rules failed to run ({exc.__class__.__name__})", 1))

    severity_rank = {"critical": 0, "high": 1, "moderate": 2, "low": 3}
    alerts.sort(key=lambda a: (severity_rank.get(a["severity"], 9), a["table"]))
    return {
        "n": len(alerts),
        "alerts": alerts,
        "checks": ["missing_values", "duplicates", "outliers", "inconsistent_records"],
        "consistency_rules": _consistency_summary(),
        "tier": "simulated",
    }


def _consistency_summary() -> list[dict]:
    try:
        from ml.consistency import run_rules
        return run_rules()
    except Exception:
        return []


def _alert(severity: str, table: str, check: str, message: str, count: int) -> dict:
    return {
        "severity": severity,
        "severity_label": severity,
        "table": table,
        "check": check,
        "message": message,
        "count": int(count),
    }


def _iqr_outliers(df) -> int:
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return 0
    total = 0
    for col in numeric.columns:
        if col in {"year"}:
            continue
        series = numeric[col].dropna()
        if len(series) < 12:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr <= 0:
            continue
        total += int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
    return total


def list_audit_log(
    *,
    actor: str | None = None,
    action: str | None = None,
    resource: str | None = None,
    since: str | None = None,
    until: str | None = None,
    limit: int = 500,
) -> dict:
    """W.ADM.08 data. Newest first. This read is not itself written to the log."""
    from db.database import SessionLocal
    from models.governance import AuditLog

    session = SessionLocal()
    try:
        q = session.query(AuditLog)
        # Filters are substring matches. % and _ in the input are matched
        # literally, so ?actor=% no longer returns every row (audit S16).
        if actor:
            q = q.filter(AuditLog.actor.ilike(_contains(actor), escape="\\"))
        if action:
            q = q.filter(AuditLog.action.ilike(_contains(action), escape="\\"))
        if resource:
            q = q.filter(AuditLog.resource.ilike(_contains(resource), escape="\\"))
        if since:
            q = q.filter(AuditLog.created_at >= _parse_dt(since))
        if until:
            q = q.filter(AuditLog.created_at <= _parse_dt(until))
        total = q.count()
        rows = q.order_by(desc(AuditLog.created_at)).limit(max(1, min(int(limit), 1000))).all()
        return {
            "n": len(rows),
            "total": total,
            "retention_days": AUDIT_RETENTION_DAYS,
            "rows": [_audit_row(r) for r in rows],
        }
    finally:
        session.close()


def _contains(value: str) -> str:
    v = value.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{v}%"


# ── Retention (plan item 3.7) ─────────────────────────────────────────────────
# Audit rows older than AUDIT_RETENTION_DAYS are deleted by a daily job and on
# demand by an administrator. The purge is itself written to the log, so the
# record of what was removed survives the removal. Minimum 30 days, so a
# mistyped value cannot wipe recent accountability.
AUDIT_RETENTION_DAYS = max(30, int(os.getenv("AUDIT_RETENTION_DAYS") or 365))


# Draft and rejected scenarios are working notes; approved, submitted and
# archived ones are part of the governance record and are never purged.
SCENARIO_RETENTION_DAYS = max(30, int(os.getenv("SCENARIO_RETENTION_DAYS") or 180))
_PURGEABLE_SCENARIO_STATUSES = ("draft", "rejected")


def purge_scenarios(retention_days: int | None = None, actor: dict | None = None) -> dict:
    from db.database import SessionLocal
    from models.governance import Scenario
    from services.auth_service import log_audit

    days = max(30, int(retention_days or SCENARIO_RETENTION_DAYS))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    session = SessionLocal()
    try:
        deleted = (
            session.query(Scenario)
            .filter(Scenario.created_at < cutoff,
                    Scenario.status.in_(_PURGEABLE_SCENARIO_STATUSES))
            .delete(synchronize_session=False)
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    log_audit(actor or {"username": "system", "role": "SYSTEM"}, "scenario_retention",
              "scenarios", {"deleted": int(deleted), "cutoff": cutoff.isoformat(),
                            "statuses": list(_PURGEABLE_SCENARIO_STATUSES), "retention_days": days})
    return {"deleted": int(deleted), "cutoff": cutoff.isoformat(), "retention_days": days}


def purge_audit_log(retention_days: int | None = None, actor: dict | None = None) -> dict:
    from db.database import SessionLocal
    from models.governance import AuditLog
    from services.auth_service import log_audit

    days = max(30, int(retention_days or AUDIT_RETENTION_DAYS))
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    session = SessionLocal()
    try:
        deleted = (
            session.query(AuditLog)
            .filter(AuditLog.created_at < cutoff)
            .delete(synchronize_session=False)
        )
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    log_audit(actor or {"username": "system", "role": "SYSTEM"}, "audit_retention",
              "audit_log", {"deleted": int(deleted), "cutoff": cutoff.isoformat(),
                            "retention_days": days})
    return {"deleted": int(deleted), "cutoff": cutoff.isoformat(), "retention_days": days}


def _parse_dt(value: str):
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"invalid timestamp {value!r}") from exc


def _audit_row(row) -> dict:
    return {
        "id": row.id,
        "actor": row.actor,
        "role": row.role,
        "action": row.action,
        "resource": row.resource,
        "payload": row.payload or {},
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def list_scenarios() -> dict:
    from db.database import SessionLocal
    from models.governance import Scenario

    session = SessionLocal()
    try:
        rows = session.query(Scenario).order_by(desc(Scenario.created_at)).all()
        return {"n": len(rows), "rows": [_scenario_row(r) for r in rows]}
    finally:
        session.close()


def patch_scenario(scenario_id: int, *, status: str, actor: dict) -> dict:
    from fastapi import HTTPException
    from db.database import SessionLocal
    from models.governance import Scenario
    from services.auth_service import log_audit

    if status not in _SCENARIO_STATUSES:
        raise HTTPException(status_code=422, detail=f"status must be one of {_SCENARIO_STATUSES}")

    session = SessionLocal()
    try:
        row = session.query(Scenario).filter(Scenario.id == scenario_id).first()
        if row is None:
            raise HTTPException(status_code=404, detail="scenario not found")
        assumptions = dict(row.assumptions or {})
        assumptions["official_forecast"] = False
        nested = dict(assumptions.get("assumptions") or {})
        nested["official_forecast"] = False
        assumptions["assumptions"] = nested
        row.assumptions = assumptions
        row.status = status
        session.commit()
        session.refresh(row)
        out = _scenario_row(row)
        log_audit(actor, "scenario_action", f"scenario:{row.id}", {
            "status": status,
            "official_forecast": False,
        })
        return out
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _scenario_row(row) -> dict:
    assumptions = dict(row.assumptions or {})
    return {
        "id": row.id,
        "name": row.name,
        "owner": row.owner,
        "assumptions": assumptions,
        "status": row.status,
        "approval_status": row.status,
        "official_forecast": False,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }
