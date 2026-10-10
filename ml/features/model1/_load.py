"""Load a DOC1 fact table. Category percentages never enter a learner."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_KEYS = ("institution", "campus", "region", "program", "field", "band", "year")


def ethiopia(table: str) -> pd.DataFrame:
    try:
        from services._datasets import ethiopia as _eth
    except ImportError:
        from backend.services._datasets import ethiopia as _eth
    return _eth(table)


def load(table: str, columns: tuple[str, ...]) -> pd.DataFrame:
    df = ethiopia(table)
    keep = []
    for col in list(_KEYS) + list(columns):
        if col in df.columns and col not in keep:
            keep.append(col)
    return df[keep].copy()
