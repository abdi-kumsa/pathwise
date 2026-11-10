"""Observed trends attached to list rows (frontend design pass, 2026-11-09).

Run inside the backend container, no live server required:
    docker exec pathwise_backend sh -c "cd /app && python -m pytest tests/test_trend_service.py -q"
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_BACKEND = Path(__file__).resolve().parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from services import trend_service as trends  # noqa: E402


def _frame():
    return pd.DataFrame({
        "field": ["A", "A", "A", "B", "B"],
        "region": ["N", "N", "S", "N", "N"],
        "year": [2016, 2017, 2017, 2016, 2018],
        "n": [10.0, 12.0, 3.0, 5.0, None],
    })


def test_series_sums_to_keys_and_aligns_to_every_observed_year():
    t = trends._series(_frame(), "n", ("field",))
    # A year with no observed value anywhere (2018 is NaN-only) is not a year.
    assert t["years"] == [2016, 2017]
    assert t["series"][("A",)] == [10.0, 15.0]      # 2017 sums both regions
    assert t["series"][("B",)] == [5.0, None]       # a gap is None, never zero


def test_attach_keys_on_the_row_and_leaves_unknown_rows_none():
    t = trends._series(_frame(), "n", ("region", "field"))
    rows = [{"region": "N", "field": "A"}, {"region": "S", "field": "B"}]
    out = trends.attach(rows, t, ("region", "field"))
    assert out[0]["trend"] == [10.0, 12.0]
    assert out[1]["trend"] is None


def test_enrolment_and_application_trends_cover_the_observed_decade():
    e = trends.enrolment_trend(("field",))
    a = trends.applications_trend(("institution", "program"))
    assert e["years"][0] == 2016 and e["years"][-1] >= 2025
    assert e["years"] == a["years"]
    assert all(len(v) == len(e["years"]) for v in e["series"].values())
    assert len(a["series"]) > 100
