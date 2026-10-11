"""scripts/spec_report.py must run and expose the shared coverage numbers."""
from __future__ import annotations

from scripts import spec_report


def test_registry_summary_matches_the_documents():
    s = spec_report.S.summary()
    assert s["categories"] == 20
    assert s["widgets"] == 44
    assert s["procedure"] == 7
    assert s["source_tables"] == 20
    assert s["attributes"] > 0


def test_coverage_rows_are_complete_counts():
    rows = spec_report.coverage_rows()
    assert set(rows) == {
        "attributes",
        "source_tables",
        "widget_components",
        "widget_endpoints",
        "procedure",
        "architecture",
        "ingestion",
    }
    for done, total in rows.values():
        assert 0 <= done <= total
        assert total > 0


def test_ethiopia_source_tables_are_present():
    """Wave 1: every DOC1 source table has a generated Ethiopia file."""
    done, total = spec_report.coverage_rows()["source_tables"]
    assert done == total == 20
