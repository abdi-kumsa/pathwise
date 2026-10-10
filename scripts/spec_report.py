#!/usr/bin/env python3
"""
Burn-down table for the two feedback documents.

Prints how much of docs/spec/ is claimed by real artefacts. Coverage stays
red until Waves 1–7 land — that is the point. Integrity of the registry itself
is a different question; run:

    pytest tests/test_spec_coverage.py -m integrity
    python scripts/spec_report.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import spec_registry as S  # noqa: E402


def _exists(rel: str | None) -> bool:
    return bool(rel) and (ROOT / rel).exists()


def _ethiopia_columns() -> set[str]:
    ethiopia = ROOT / "data" / "ethiopia"
    if not ethiopia.exists():
        return set()
    import pandas as pd
    cols: set[str] = set()
    for path in ethiopia.rglob("*.parquet"):
        cols |= set(pd.read_parquet(path).columns)
    for path in ethiopia.rglob("*.csv"):
        cols |= set(pd.read_csv(path, nrows=0).columns)
    return cols


def attribute_column_gaps() -> list[str]:
    have = _ethiopia_columns()
    missing: list[str] = []
    for var in S.all_variables():
        for col in S.columns_for(var):
            if col not in have:
                missing.append(f"{var['id']} {var['name']!r} -> {col}")
    return missing


def source_table_gaps() -> list[str]:
    ethiopia = ROOT / "data" / "ethiopia"
    missing: list[str] = []
    for table in S.source_tables():
        if not list(ethiopia.rglob(f"{table}.parquet")) and not list(ethiopia.rglob(f"{table}.csv")):
            missing.append(table)
    return missing


def widget_component_gaps() -> list[str]:
    return [
        f"{w['id']} -> {w['satisfied_by']['component']}"
        for w in S.widgets()
        if not _exists(w["satisfied_by"]["component"])
    ]


def widget_endpoint_gaps() -> list[str]:
    routers = ROOT / "backend" / "routers"
    blob = "\n".join(p.read_text(encoding="utf-8") for p in routers.glob("*.py"))
    missing: list[str] = []
    for w in S.widgets():
        path = w["satisfied_by"]["endpoint"]
        tail = path[len("/api"):] if path.startswith("/api") else path
        literal = tail.split("{")[0].rstrip("/")
        if literal and literal not in blob:
            missing.append(f"{w['id']} -> {path}")
    return missing


def procedure_gaps() -> list[str]:
    missing: list[str] = []
    for step in S.procedure():
        sat = step["satisfied_by"]
        for key in ("artefact", "report", "module", "component"):
            target = sat.get(key)
            if target and not _exists(target):
                missing.append(f"{step['id']} -> {target}")
        for extra in sat.get("also") or []:
            if not _exists(extra):
                missing.append(f"{step['id']} -> {extra}")
    return missing


def architecture_gaps() -> list[str]:
    missing: list[str] = []
    for comp in S.architecture()["components"]:
        sat = comp.get("satisfied_by") or {}
        for target in (sat.get("module"), sat.get("service"), comp.get("spec")):
            if target and not _exists(target):
                missing.append(f"{comp['id']} -> {target}")
    cl = S.architecture()["constraint_layer"]["satisfied_by"]["service"]
    if not _exists(cl):
        missing.append(f"SYS.CL -> {cl}")
    return missing


def ingestion_gaps() -> list[str]:
    contracts = ROOT / "docs" / "spec" / "ingestion"
    return [
        f"{t}.md"
        for t in sorted(S.source_tables())
        if not (contracts / f"{t}.md").exists()
    ]


def _line(label: str, missing: list[str], total: int) -> tuple[int, int]:
    done = total - len(missing)
    mark = "OK  " if not missing else "TODO"
    print(f"  {mark}  {label}: {done}/{total}")
    for item in missing[:12]:
        print(f"        - {item}")
    if len(missing) > 12:
        print(f"        ... {len(missing) - 12} more")
    return done, total


def coverage_rows() -> dict[str, tuple[int, int]]:
    """Numbers the tests and this report share."""
    attr_missing = attribute_column_gaps()
    attr_total = sum(len(S.columns_for(v)) for v in S.all_variables())
    widgets = list(S.widgets())
    return {
        "attributes": (attr_total - len(attr_missing), attr_total),
        "source_tables": (len(S.source_tables()) - len(source_table_gaps()), len(S.source_tables())),
        "widget_components": (len(widgets) - len(widget_component_gaps()), len(widgets)),
        "widget_endpoints": (len(widgets) - len(widget_endpoint_gaps()), len(widgets)),
        "procedure": (len(S.procedure()) - len(procedure_gaps()), len(S.procedure())),
        "architecture": (4 - len(architecture_gaps()), 4),
        "ingestion": (len(S.source_tables()) - len(ingestion_gaps()), len(S.source_tables())),
    }


def main() -> int:
    summary = S.summary()
    print("PathWise spec coverage")
    print("======================")
    print(
        f"Registry: {summary['attributes']} attributes, "
        f"{summary['categories']} categories, "
        f"{summary['widgets']} widgets, "
        f"{summary['procedure']} procedure steps, "
        f"{summary['total_ids']} ids"
    )
    print()
    print("Burn-down (artefacts on disk / declared in docs/spec)")
    rows = [
        ("Attribute columns (Wave 1 fact tables)", attribute_column_gaps(),
         sum(len(S.columns_for(v)) for v in S.all_variables())),
        ("Source tables", source_table_gaps(), len(S.source_tables())),
        ("Widget components", widget_component_gaps(), sum(1 for _ in S.widgets())),
        ("Widget endpoints", widget_endpoint_gaps(), sum(1 for _ in S.widgets())),
        ("Procedure artefacts", procedure_gaps(), len(S.procedure())),
        ("Architecture components", architecture_gaps(), 4),
        ("Ingestion contracts", ingestion_gaps(), len(S.source_tables())),
    ]
    claimed = 0
    total = 0
    for label, missing, n in rows:
        d, t = _line(label, missing, n)
        claimed += d
        total += t
    print()
    print(f"Overall: {claimed}/{total} artefact checks claimed")
    print("Integrity of the YAML itself: pytest tests/test_spec_coverage.py -m integrity")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
