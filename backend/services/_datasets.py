"""
Shared loaders and the join backbone.

Wave 1 re-bases the request path onto `data/ethiopia/`. The US CSVs in
`Assets/` are no longer read here — they remain on disk as an archive only.

Join backbone (Ethiopia):

    occupation  ──►  sector / MoE field  ═══  field  ──►  programme

Compatibility frames `jobs_compat` and `enrollment_compat` keep the column
names the existing role services already call (`job_family`, `field_of_study`,
`enrollment_count`, …) so those pages keep working while they are rewritten
in Waves 5–6.
"""
from pathlib import Path

import pandas as pd

from ._cache import ttl_cache

_ROOT = Path(__file__).resolve().parent.parent.parent
_ETH = _ROOT / "data" / "ethiopia"

YEAR_MIN = 2016
YEAR_MAX = 2025

DATASET_LABEL = "Simulated Ethiopian structure · 2016–2025"

FIELDS = [
    "Engineering & Technology",
    "Natural & Computational Sciences",
    "Medicine & Health Sciences",
    "Agriculture & Life Sciences",
    "Business & Economics",
    "Social Sciences & Humanities",
    "Law",
    "Education",
]

PROGRAMS = [
    "BSc Civil Engineering",
    "BSc Computer Science",
    "MD Medicine",
    "BSc Agriculture",
    "BA Accounting",
    "BA Sociology",
    "LLB Law",
    "BEd Education",
]


def _read(name: str) -> pd.DataFrame:
    _ensure_contracts()
    path = _ETH / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"Ethiopia table {name!r} is missing. Run: python data/ethiopia/generate.py"
        )
    return pd.read_parquet(path)


_CONTRACTS_CHECKED = False


def _ensure_contracts() -> None:
    """Run Wave 1.3 validators once per process. Log, do not 500 the dashboard."""
    global _CONTRACTS_CHECKED
    if _CONTRACTS_CHECKED:
        return
    _CONTRACTS_CHECKED = True
    try:
        try:
            from services._validate import validate_ethiopia
        except ImportError:
            from backend.services._validate import validate_ethiopia
        errors = validate_ethiopia()
    except Exception as exc:  # spec files missing in a half-mounted container
        import logging
        logging.getLogger(__name__).warning("Ethiopia contract check skipped: %s", exc)
        return
    if errors:
        import logging
        logging.getLogger(__name__).warning(
            "Ethiopia contract issues (%d): %s", len(errors), "; ".join(errors[:12])
        )


@ttl_cache
def ethiopia(table: str) -> pd.DataFrame:
    """One DOC1 fact table, keyed by the spec `source_table` name."""
    return _read(table)


@ttl_cache
def jobs() -> pd.DataFrame:
    """Labour-market observations in the column shape existing services read."""
    return _read("jobs_compat")


@ttl_cache
def enrollment() -> pd.DataFrame:
    """Education-supply observations in the column shape existing services read."""
    return _read("enrollment_compat")


@ttl_cache
def placements() -> pd.DataFrame:
    """Graduate fit-classification outcomes (Wave 2 does not replace this path).

    Still read from the mock placement file. Ranking on these figures is
    forbidden (RANK.R1); the Ethiopia rebase does not pretend to have invented
    a between-field fit signal.
    """
    df = pd.read_csv(_ROOT / "data" / "mock" / "placements.csv")
    df["placed"] = df["placed"].map(lambda x: str(x).lower() == "true")
    df["job_family"] = df["role"].map(title_to_family())
    return df


@ttl_cache
def features() -> pd.DataFrame:
    """Feature store for the still-resident placement model."""
    df = pd.read_parquet(_ROOT / "data" / "processed" / "features.parquet")
    prog_cols = [c for c in df.columns if c.startswith("prog_")]
    if prog_cols and "program" not in df.columns:
        df["program"] = df[prog_cols].idxmax(axis=1).str.replace("prog_", "", regex=False)
    return df


@ttl_cache
def title_to_family() -> dict:
    j = jobs().drop_duplicates("job_title")
    return dict(zip(j["job_title"], j["job_family"]))


@ttl_cache
def family_to_programs() -> dict:
    e = enrollment()[["field_of_study", "program_name"]].drop_duplicates()
    out: dict = {f: [] for f in FIELDS}
    for field, prog in e.itertuples(index=False):
        out.setdefault(field, [])
        if prog not in out[field]:
            out[field].append(prog)
    return {k: sorted(v) for k, v in out.items()}


@ttl_cache
def program_to_family() -> dict:
    e = enrollment()[["program_name", "field_of_study"]].drop_duplicates()
    return dict(zip(e["program_name"], e["field_of_study"]))


@ttl_cache
def job_titles() -> list:
    j = jobs().drop_duplicates("job_title")[["job_title", "job_family"]]
    return [
        {"job_title": r.job_title, "job_family": r.job_family}
        for r in j.sort_values("job_title").itertuples(index=False)
    ]


@ttl_cache
def institutions() -> list:
    e = enrollment()[["institution_name", "institution_type", "institution_state"]].drop_duplicates()
    return [
        {"name": r.institution_name, "type": r.institution_type, "state": r.institution_state}
        for r in e.sort_values("institution_name").itertuples(index=False)
    ]


def cagr(first: float, last: float, years: int) -> float:
    if years <= 0 or first is None or last is None or first <= 0 or last <= 0:
        return 0.0
    return round(((last / first) ** (1 / years) - 1) * 100, 2)


def normalise(series: pd.Series) -> pd.Series:
    lo, hi = float(series.min()), float(series.max())
    if hi - lo < 1e-9:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - lo) / (hi - lo)
