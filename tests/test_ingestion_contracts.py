"""Wave 1.3 — ingestion contracts and load-time validation."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from backend import spec_registry as S
from backend.services._validate import validate_ethiopia

ROOT = Path(__file__).resolve().parent.parent
CONTRACTS = ROOT / "docs" / "spec" / "ingestion"


def test_every_source_table_has_a_contract_file():
    missing = [
        t for t in S.source_tables()
        if not (CONTRACTS / f"{t}.md").exists()
    ]
    assert missing == [], f"missing ingestion contracts: {missing}"


def test_ethiopia_tables_pass_the_contract_validator():
    errors = validate_ethiopia()
    assert errors == [], "\n".join(errors)


def test_generated_tables_declare_simulated_provenance():
    ethiopia = ROOT / "data" / "ethiopia"
    offenders = []
    for path in sorted(ethiopia.glob("*.parquet")):
        df = pd.read_parquet(path)
        if "provenance" not in df.columns or not (df["provenance"] == "simulated").all():
            offenders.append(path.name)
    assert offenders == [], offenders


def test_validator_accepts_official_provenance_with_source():
    from backend.services._validate import check_table

    df = pd.DataFrame({
        "year": [2020, 2021],
        "field": ["Engineering & Technology", "Engineering & Technology"],
        "provenance": ["official", "official"],
        "source": ["CSA LFS", "CSA LFS"],
        "enrollment_lag_1y": [100, 110],
    })
    assert check_table("enrollment_history", df, {"enrollment_lag_1y"}) == []


def test_validator_rejects_official_without_source():
    from backend.services._validate import check_table

    df = pd.DataFrame({
        "year": [2020],
        "field": ["Engineering & Technology"],
        "provenance": ["official"],
        "enrollment_lag_1y": [100],
    })
    errors = check_table("enrollment_history", df, {"enrollment_lag_1y"})
    assert any("source" in e for e in errors)


def test_validator_rejects_empty_join_key():
    from backend.services._validate import check_table

    df = pd.DataFrame({
        "year": [2016, 2025],
        "field": [None, None],
        "provenance": ["simulated", "simulated"],
        "enrollment_lag_1y": [1, 2],
    })
    errors = check_table("enrollment_history", df, {"enrollment_lag_1y"})
    assert any("key field is empty" in e for e in errors)
