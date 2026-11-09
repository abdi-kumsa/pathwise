"""Plan item 4.3 — the official-file ingestion path, proven on fixtures.

No official MoE / MoLS / ESS file is in this repository, so these tests build
official-*shaped* files from the simulated tables and run the dry-run path.
Nothing is written to data/ethiopia/.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import ingest_official as I  # noqa: E402


@pytest.fixture
def scratch():
    with tempfile.TemporaryDirectory(prefix="pw-ingest-") as d:
        yield Path(d)


def _official_like(table: str, scratch: Path, mutate=None) -> Path:
    df = pd.read_parquet(f"data/ethiopia/{table}.parquet").drop(columns=["provenance"])
    if mutate:
        df = mutate(df)
    path = scratch / f"{table}.csv"
    df.to_csv(path, index=False)
    return path


def test_a_well_formed_file_passes_and_is_reconciled(scratch):
    def nudge(df):
        """10% higher enrolment, with every derived column recomputed so the
        file is internally consistent (the rules would refuse it otherwise)."""
        df = df.copy().sort_values(["institution", "program", "year"])
        df["program_enrollment_count"] = (df["program_enrollment_count"] * 1.1).round()
        g = df.groupby(["institution", "program"])["program_enrollment_count"]
        df["enrollment_lag_1y"] = g.shift(1)
        df["enrollment_lag_2y"] = g.shift(2)
        df["enrollment_rolling_3y_avg"] = g.transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
        df["enrollment_rolling_5y_avg"] = g.transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
        return df
    path = _official_like("enrollment_history", scratch, nudge)
    stamped, report = I.prepare("enrollment_history", path, "MoE EMIS (fixture)", "2025-10")
    assert (stamped["provenance"] == "official").all()
    assert (stamped["source"] == "MoE EMIS (fixture)").all()
    assert report["matched_rows"] == len(stamped)
    col = next(c for c in report["columns"] if c["column"] == "program_enrollment_count")
    assert 9 < col["median_abs_pct_diff"] < 11, "reconciliation measures the 10% difference"


def test_missing_required_column_is_refused(scratch):
    path = _official_like("enrollment_history", scratch,
                          lambda d: d.drop(columns=["enrollment_lag_1y"]))
    with pytest.raises(I.IngestError, match="missing required column"):
        I.prepare("enrollment_history", path, "MoE EMIS", "2025-10")


def test_unknown_institution_is_refused(scratch):
    def rename(df):
        df = df.copy()
        df.loc[df.index[0], "institution"] = "Hogwarts"
        return df
    path = _official_like("enrollment_history", scratch, rename)
    with pytest.raises(I.IngestError, match="unknown institution"):
        I.prepare("enrollment_history", path, "MoE EMIS", "2025-10")


def test_duplicate_keys_are_refused(scratch):
    path = _official_like("vacancies", scratch, lambda d: pd.concat([d, d.head(3)]))
    with pytest.raises(I.IngestError, match="duplicate"):
        I.prepare("vacancies", path, "MoLS", "2025-10")


def test_source_and_vintage_are_required(scratch):
    path = _official_like("vacancies", scratch)
    with pytest.raises(I.IngestError):
        I.prepare("vacancies", path, " ", "2025-10")


def test_unknown_table_is_refused(scratch):
    path = _official_like("vacancies", scratch)
    with pytest.raises(I.IngestError, match="not a DOC1 source table"):
        I.prepare("not_a_table", path, "X", "2025")


def test_a_leaky_rolling_average_is_refused(scratch):
    """The exact leak behind the old near-zero OLS errors is a blocking rule."""
    def leak(df):
        df = df.copy().sort_values(["institution", "program", "year"])
        g = df.groupby(["institution", "program"])["program_enrollment_count"]
        df["enrollment_rolling_3y_avg"] = g.transform(lambda s: s.rolling(3, min_periods=1).mean())
        return df
    path = _official_like("enrollment_history", scratch, leak)
    with pytest.raises(I.IngestError, match="C.ROLLING.ENROLMENT"):
        I.prepare("enrollment_history", path, "MoE EMIS", "2025-10")


def test_a_funnel_that_accepts_more_than_it_offers_is_refused(scratch):
    def overfill(df):
        df = df.copy()
        df.loc[df.index[:5], "accepted_offers_count"] = df.loc[df.index[:5], "offers_count"] + 50
        return df
    path = _official_like("admissions_funnel", scratch, overfill)
    with pytest.raises(I.IngestError, match="C.FUNNEL.ORDER"):
        I.prepare("admissions_funnel", path, "MoE", "2025-10")
