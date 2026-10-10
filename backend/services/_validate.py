"""
Wave 1.3 — contract checks at load time.

Each Ethiopia fact table is checked for required columns (from docs/spec/),
non-empty keys, year coverage, and obvious range breaks. Failures feed
W.ADM.06 later; `generate.py --validate` raises, and `_datasets.py` logs
them on first load so a missing ministry replacement cannot fail silently.

Official replacement files (provenance tier `official`) are allowed. They
must declare a `source` and are not required to span the simulated 2016–2025
window.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    import spec_registry as S
except ImportError:
    from backend import spec_registry as S

_HERE = Path(__file__).resolve()
ETHIOPIA_CANDIDATES = (
    Path("/data/ethiopia"),
    _HERE.parents[2] / "data" / "ethiopia",
)
ETHIOPIA = next((p for p in ETHIOPIA_CANDIDATES if p.exists()), ETHIOPIA_CANDIDATES[-1])
YEAR_MIN, YEAR_MAX = 2016, 2025

KEY_CANDIDATES = (
    "year",
    "academic_year",
    "field",
    "institution",
    "region",
    "program",
    "sector",
    "occupation",
    "campus",
    "hei_name",
)

ALLOWED_TIERS = {"simulated", "official", "derived"}


def _load(table: str) -> pd.DataFrame | None:
    parquet = ETHIOPIA / f"{table}.parquet"
    csv = ETHIOPIA / f"{table}.csv"
    if parquet.exists():
        return pd.read_parquet(parquet)
    if csv.exists():
        return pd.read_csv(csv)
    return None


def check_table(table: str, df: pd.DataFrame, required: set[str]) -> list[str]:
    """Validate one in-memory frame. Used by validate_ethiopia and unit tests."""
    errors: list[str] = []
    if df is None or df.empty:
        errors.append(f"{table}: empty")
        return errors
    missing = sorted(required - set(df.columns))
    if missing:
        errors.append(f"{table}: missing columns {missing}")

    official = False
    if "provenance" in df.columns:
        tiers = {str(t) for t in df["provenance"].dropna().unique()}
        bad_tiers = tiers - ALLOWED_TIERS
        if bad_tiers:
            errors.append(f"{table}: unknown provenance tiers {sorted(bad_tiers)}")
        official = "official" in tiers
        if official:
            if "source" not in df.columns or df["source"].isna().all():
                errors.append(f"{table}: official rows require a source")
        elif not (df["provenance"] == "simulated").all():
            errors.append(f"{table}: provenance must be 'simulated' for generated files")

    if "year" in df.columns and not official:
        years = set(df["year"].dropna().unique())
        if years and (YEAR_MIN not in years or YEAR_MAX not in years):
            errors.append(
                f"{table}: year coverage {min(years)}–{max(years)} "
                f"does not include {YEAR_MIN}–{YEAR_MAX}"
            )

    for col in KEY_CANDIDATES:
        if col not in df.columns:
            continue
        series = df[col]
        blank = series.isna() | (series.astype(str).str.strip() == "") | (series.astype(str) == "nan")
        if bool(blank.all()):
            errors.append(f"{table}: key {col} is empty")

    for col in df.columns:
        name = str(col)
        if "growth" in name or "cagr" in name:
            continue
        share_like = (
            name.startswith("share_")
            or name.endswith("_rate_pct")
            or name.endswith("_utilization_pct")
        )
        if not share_like:
            continue
        nums = pd.to_numeric(df[col], errors="coerce").dropna()
        if nums.empty:
            continue
        if float(nums.min()) < -0.01 or float(nums.max()) > 100.01:
            errors.append(f"{table}: {col} outside 0–100")

    return errors


def validate_ethiopia() -> list[str]:
    errors: list[str] = []
    required_by_table: dict[str, set[str]] = {}
    for model in S.models():
        for cat in S.categories(model):
            cols = set()
            for var in cat.get("variables", []):
                cols.add(var["column"])
                cols.update(var.get("also") or [])
            required_by_table.setdefault(cat["source_table"], set()).update(cols)

    for table, cols in sorted(required_by_table.items()):
        df = _load(table)
        if df is None:
            errors.append(f"{table}: file missing")
            continue
        errors.extend(check_table(table, df, cols))
    return errors
