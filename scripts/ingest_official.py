"""
Replace one simulated fact table with an official file (plan item 4.3, Phase 5).

    python scripts/ingest_official.py TABLE FILE --source "MoE EMIS" --vintage 2025-10
    python scripts/ingest_official.py TABLE FILE --source ... --vintage ... --apply

Without --apply this is a dry run: it validates the file and prints a
reconciliation report against the current table, and writes nothing.

Steps, in order — any failure stops before anything is written:

1. Load the file (CSV, Parquet or Excel).
2. Contract: every column docs/spec/ requires for TABLE is present.
3. Keys: institutions, regions and fields exist in data/ethiopia/reference/;
   years are integers; no duplicate rows on the table's key columns.
4. Stamp: provenance = "official", plus `source` and `vintage` columns.
5. Validate with the same checker the API uses (backend/services/_validate.py).
6. Reconcile with the current table: rows, years, and per-column differences
   on matching keys (Phase 5 groundwork — how far the simulation was off).
7. --apply only: back up the current file to data/ethiopia/_backup/, write the
   new Parquet and CSV, append to data/ethiopia/ingestion_log.json, and re-run
   the rolling-origin model comparison so the next forecast uses the file.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ETH = ROOT / "data" / "ethiopia"
REF = ETH / "reference"
BACKUP = ETH / "_backup"
LOG = ETH / "ingestion_log.json"

KEY_COLUMNS = ("institution", "campus", "region", "program", "field", "sector", "occupation", "year")


class IngestError(ValueError):
    pass


def required_columns(table: str) -> set[str]:
    from backend import spec_registry as S
    cols: set[str] = set()
    for model in S.models():
        for cat in S.categories(model):
            if cat.get("source_table") != table:
                continue
            for var in cat.get("variables", []):
                cols.add(var["column"])
                cols.update(var.get("also") or [])
    if not cols:
        raise IngestError(f"{table!r} is not a DOC1 source table")
    return cols


def load(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(path)
    if suffix in (".xlsx", ".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path)


def check_keys(df: pd.DataFrame) -> list[str]:
    problems = []
    refs = {
        "institution": set(pd.read_csv(REF / "heis.csv")["name"]),
        "region": set(pd.read_csv(REF / "regions.csv")["name"]),
        "field": set(pd.read_csv(REF / "fields.csv")["field"]),
    }
    for col, valid in refs.items():
        if col in df.columns:
            unknown = sorted(set(df[col].dropna().astype(str)) - valid)
            if unknown:
                problems.append(f"unknown {col} value(s): {unknown[:5]}"
                                + (" …" if len(unknown) > 5 else ""))
    if "year" in df.columns:
        years = pd.to_numeric(df["year"], errors="coerce")
        if years.isna().any() or (years % 1 != 0).any():
            problems.append("year must be a whole number on every row")
    keys = [c for c in KEY_COLUMNS if c in df.columns]
    if keys:
        dupes = int(df.duplicated(subset=keys).sum())
        if dupes:
            problems.append(f"{dupes} duplicate row(s) on {keys}")
    return problems


def stamp(df: pd.DataFrame, source: str, vintage: str) -> pd.DataFrame:
    out = df.copy()
    out["provenance"] = "official"
    out["source"] = source
    out["vintage"] = vintage
    return out


def reconcile(table: str, new: pd.DataFrame) -> dict:
    """Compare an official file with the table it replaces."""
    current_path = ETH / f"{table}.parquet"
    if not current_path.exists():
        return {"current_rows": 0, "note": "no current table"}
    cur = pd.read_parquet(current_path)
    keys = [c for c in KEY_COLUMNS if c in new.columns and c in cur.columns]
    def _measure(col: str) -> bool:
        # Booleans count as numeric in pandas but are flags, not measurements.
        return all(pd.api.types.is_numeric_dtype(d[col]) and not pd.api.types.is_bool_dtype(d[col])
                   for d in (new, cur))
    numeric = [c for c in new.columns if c in cur.columns and c not in keys and _measure(c)]
    merged = new[keys + numeric].merge(cur[keys + numeric], on=keys, how="inner",
                                       suffixes=("_official", "_current")) if keys else pd.DataFrame()
    columns = []
    for c in numeric:
        a, b = merged.get(f"{c}_official"), merged.get(f"{c}_current")
        if a is None or b is None or not len(merged):
            continue
        denom = b.abs().where(b.abs() > 1e-9)
        pct = ((a - b).abs() / denom * 100).replace([np.inf, -np.inf], np.nan)
        columns.append({
            "column": c,
            "matched_rows": int(pct.notna().sum()),
            "median_abs_pct_diff": None if pct.dropna().empty else round(float(pct.median()), 2),
            "official_mean": round(float(a.mean()), 4),
            "current_mean": round(float(b.mean()), 4),
        })
    years = lambda d: sorted(int(y) for y in d["year"].dropna().unique()) if "year" in d else []  # noqa: E731
    return {
        "current_rows": int(len(cur)),
        "official_rows": int(len(new)),
        "matched_rows": int(len(merged)),
        "keys": keys,
        "years_official": years(new),
        "years_current": years(cur),
        "columns": sorted(columns, key=lambda r: -(r["median_abs_pct_diff"] or 0)),
    }


def prepare(table: str, path: Path, source: str, vintage: str) -> tuple[pd.DataFrame, dict]:
    """Steps 1–6. Raises IngestError on the first blocking problem."""
    from backend.services._validate import check_table

    if not source.strip() or not vintage.strip():
        raise IngestError("--source and --vintage are required")
    df = load(path)
    required = required_columns(table)
    missing = sorted(required - set(df.columns))
    if missing:
        raise IngestError(f"missing required column(s) for {table}: {missing}")
    problems = check_keys(df)
    if problems:
        raise IngestError("; ".join(problems))
    stamped = stamp(df, source.strip(), vintage.strip())
    errors = check_table(table, stamped, required)
    if errors:
        raise IngestError("; ".join(errors))
    # Consistency rules with this file substituted for the current table.
    from ml.consistency import run_rules
    failed = [r for r in run_rules({table: stamped})
              if r["table"] == table and r["status"] == "fail"]
    blocking = [r for r in failed if r["severity"] in ("critical", "high")]
    if blocking:
        raise IngestError("; ".join(f"{r['rule']} ({r['violations']} row(s)): {r['description']}"
                                    for r in blocking))
    report = reconcile(table, stamped)
    report["consistency_warnings"] = [r["rule"] for r in failed if r not in blocking]
    return stamped, report


def apply(table: str, stamped: pd.DataFrame, report: dict, source: str, vintage: str) -> dict:
    BACKUP.mkdir(parents=True, exist_ok=True)
    when = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    for suffix in (".parquet", ".csv"):
        cur = ETH / f"{table}{suffix}"
        if cur.exists():
            shutil.copy2(cur, BACKUP / f"{table}.{when}{suffix}")
    stamped.to_parquet(ETH / f"{table}.parquet", index=False)
    stamped.to_csv(ETH / f"{table}.csv", index=False)
    entry = {"table": table, "source": source, "vintage": vintage, "applied_at": when,
             "rows": int(len(stamped)), "backup": f"_backup/{table}.{when}.parquet",
             "reconciliation": report}
    log = json.loads(LOG.read_text(encoding="utf-8")) if LOG.exists() else []
    log.append(entry)
    LOG.write_text(json.dumps(log, indent=2), encoding="utf-8")
    from ml._memo import clear
    clear()
    from ml.compare_models import compare_all
    entry["comparison"] = {t["id"]: t["selected_for_request_path"] for t in compare_all()["targets"]}
    return entry


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("table")
    ap.add_argument("file", type=Path)
    ap.add_argument("--source", required=True, help='e.g. "MoE EMIS"')
    ap.add_argument("--vintage", required=True, help="e.g. 2025-10")
    ap.add_argument("--apply", action="store_true", help="write the file (default: dry run)")
    args = ap.parse_args()
    try:
        stamped, report = prepare(args.table, args.file, args.source, args.vintage)
    except IngestError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"table": args.table, "dry_run": not args.apply, "reconciliation": report},
                     indent=2, default=str))
    if args.apply:
        entry = apply(args.table, stamped, report, args.source, args.vintage)
        print(f"applied; backup at data/ethiopia/{entry['backup']}. Restart the backend "
              "(docker compose restart backend) to serve it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
