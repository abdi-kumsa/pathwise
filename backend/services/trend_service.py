"""
Observed year-by-year series for table rows.

List pages draw a small trend beside each field, programme, region or
institution. The series is the plain observed history summed to the row's
keys — never a forecast — so the shape a reader sees is what the data did.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from services._cache import ttl_cache  # noqa: E402


def _series(df: pd.DataFrame, value: str, keys: tuple[str, ...]) -> dict:
    df = df.dropna(subset=[value])
    years = sorted(int(y) for y in df["year"].dropna().unique())
    g = df.groupby([*keys, "year"], as_index=False)[value].sum()
    out: dict[tuple, list] = {}
    for k, s in g.groupby(list(keys), sort=False):
        k = k if isinstance(k, tuple) else (k,)
        by_year = dict(zip(s["year"].astype(int), s[value].astype(float)))
        out[k] = [round(by_year[y], 1) if y in by_year else None for y in years]
    return {"years": years, "series": out}


@ttl_cache
def enrolment_trend(keys: tuple[str, ...]) -> dict:
    """Programme enrolment summed to `keys`, one value per observed year."""
    from ml.features.model1 import c1_enrollment
    return _series(c1_enrollment.frame(), "program_enrollment_count", tuple(keys))


@ttl_cache
def applications_trend(keys: tuple[str, ...]) -> dict:
    """Applications summed to `keys`, one value per observed year."""
    from ml.features.model1 import c2_funnel
    return _series(c2_funnel.frame(), "applications_count", tuple(keys))


def attach(rows: Iterable[dict], trend: dict, keys: tuple[str, ...], name: str = "trend") -> list[dict]:
    """Add `name` (a list aligned to trend['years']) to each row, keyed on `keys`."""
    rows = list(rows)
    series = trend["series"]
    for r in rows:
        r[name] = series.get(tuple(r.get(c) for c in keys))
    return rows
