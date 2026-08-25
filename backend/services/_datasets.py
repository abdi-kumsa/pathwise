"""
Shared loaders and the join backbone for the two Assets datasets.

Until the role-based work these two files were read only by data/load_to_db.py
to seed Postgres, which nothing then queried — the richest data in the repo was
unused by the API. Every role dashboard now reads them through here.

    Assets/job_market_forecasting_data.csv        3000 rows x 35 cols, 2020-2025
    Assets/student_enrollment_forecasting_data.csv 2000 rows x 41 cols, 2020-2025

── The join backbone ─────────────────────────────────────────────────────────

    job_title  ──►  job_family  ═══  field_of_study  ──►  program_name
      (33)            (9)          identical vocabulary       (12)

`job_family` (jobs) and `field_of_study` (enrollment) share the same nine
values exactly, so demand and supply join with no mapping table. This is what
makes the student job->department recommender and every ministry aggregate
possible without new data.

One wrinkle: data/mock/placements.csv records outcomes against `role`, which
uses the same 33-title vocabulary but overlaps only 28 of 33. The five
placement-only titles are mapped in _PLACEMENT_ROLE_FAMILY below; without it
371 of 2649 placed rows (14%) silently drop out of any family aggregate.

── Provenance ────────────────────────────────────────────────────────────────

This is a US-benchmarked reference dataset: US metro areas, US states, USD
salaries, SOC codes. It is presented as such throughout the UI. No figure is
re-labelled to another country's context.
"""
from pathlib import Path

import pandas as pd

from ._cache import ttl_cache

_ROOT = Path(__file__).resolve().parent.parent.parent

_JOBS_CSV       = _ROOT / 'Assets' / 'job_market_forecasting_data.csv'
_ENROLLMENT_CSV = _ROOT / 'Assets' / 'student_enrollment_forecasting_data.csv'
_PLACEMENTS_CSV = _ROOT / 'data'   / 'mock' / 'placements.csv'
_PARQUET        = _ROOT / 'data'   / 'processed' / 'features.parquet'

# Earliest and latest year present in both datasets — used for CAGR windows and
# for the provenance label shown in the UI.
YEAR_MIN = 2020
YEAR_MAX = 2025

DATASET_LABEL = "US benchmark dataset · 2020–2025"

# The nine shared field/family values, in display order.
FIELDS = [
    'AI/ML Engineering',
    'Business Intelligence',
    'Cloud Infrastructure',
    'Cybersecurity',
    'Data & Analytics',
    'DevOps',
    'Product Management',
    'Software Engineering',
    'UX Design',
]

PROGRAMS = [
    'BS Computer Science', 'BS Data Science', 'Certificate Data Analytics',
    'MBA Product Management', 'MS Artificial Intelligence', 'MS Business Analytics',
    'MS Cloud Computing', 'MS Computer Science', 'MS Cybersecurity',
    'MS Data Science', 'MS Human-Computer Interaction', 'MS Information Technology',
]

# Placement roles that do not appear in the job-market title list. Each is
# assigned the family it plainly belongs to.
_PLACEMENT_ROLE_FAMILY = {
    'QA Engineer':         'Software Engineering',
    'Release Manager':     'DevOps',
    'Scrum Master':        'Product Management',
    'Solutions Architect': 'Cloud Infrastructure',
    'UX Researcher':       'UX Design',
}


# ── Loaders ───────────────────────────────────────────────────────────────────

@ttl_cache
def jobs() -> pd.DataFrame:
    """Labour-market demand records, one row per posting-month observation."""
    return pd.read_csv(_JOBS_CSV)


@ttl_cache
def enrollment() -> pd.DataFrame:
    """Education-supply records, one row per institution x programme x term."""
    return pd.read_csv(_ENROLLMENT_CSV)


@ttl_cache
def placements() -> pd.DataFrame:
    """Graduate outcomes, with `placed` coerced to bool and a job_family column
    attached via the role vocabulary (including the five aliases above)."""
    df = pd.read_csv(_PLACEMENTS_CSV)
    df['placed'] = df['placed'].map(lambda x: str(x).lower() == 'true')
    df['job_family'] = df['role'].map(title_to_family())
    return df


@ttl_cache
def features() -> pd.DataFrame:
    """The ML feature store, with the one-hot programme columns collapsed back
    into a single `program` column (the parquet has no such column of its own)."""
    df = pd.read_parquet(_PARQUET)
    prog_cols = [c for c in df.columns if c.startswith('prog_')]
    df['program'] = df[prog_cols].idxmax(axis=1).str.replace('prog_', '', regex=False)
    return df


# ── Join backbone ─────────────────────────────────────────────────────────────

@ttl_cache
def title_to_family() -> dict:
    """job_title -> job_family, including the five placement-only aliases."""
    j = jobs().drop_duplicates('job_title')
    mapping = dict(zip(j['job_title'], j['job_family']))
    mapping.update(_PLACEMENT_ROLE_FAMILY)
    return mapping


@ttl_cache
def family_to_programs() -> dict:
    """field_of_study -> [program_name], derived from the data rather than
    hard-coded, so a new programme in the CSV appears automatically."""
    e = enrollment()[['field_of_study', 'program_name']].drop_duplicates()
    out: dict = {f: [] for f in FIELDS}
    for field, prog in e.itertuples(index=False):
        out.setdefault(field, [])
        if prog not in out[field]:
            out[field].append(prog)
    return {k: sorted(v) for k, v in out.items()}


@ttl_cache
def program_to_family() -> dict:
    """program_name -> field_of_study (each programme belongs to exactly one)."""
    e = enrollment()[['program_name', 'field_of_study']].drop_duplicates()
    return dict(zip(e['program_name'], e['field_of_study']))


@ttl_cache
def job_titles() -> list:
    """All 33 job titles with their family, sorted for the typeahead."""
    j = jobs().drop_duplicates('job_title')[['job_title', 'job_family', 'soc_code']]
    return [
        {'job_title': r.job_title, 'job_family': r.job_family}
        for r in j.sort_values('job_title').itertuples(index=False)
    ]


@ttl_cache
def institutions() -> list:
    """The eight institutions present in the enrollment dataset."""
    e = enrollment()[['institution_name', 'institution_type', 'institution_state']].drop_duplicates()
    return [
        {'name': r.institution_name, 'type': r.institution_type, 'state': r.institution_state}
        for r in e.sort_values('institution_name').itertuples(index=False)
    ]


# ── Shared maths ──────────────────────────────────────────────────────────────

def cagr(first: float, last: float, years: int) -> float:
    """Compound annual growth rate as a percentage.

    Returns 0.0 when the base is non-positive rather than raising or returning
    infinity — several fields have a zero-volume first year, and a chart is
    better served by a flat 0 than by a NaN that breaks the axis.
    """
    if years <= 0 or first is None or last is None or first <= 0 or last <= 0:
        return 0.0
    return round(((last / first) ** (1 / years) - 1) * 100, 2)


def normalise(series: pd.Series) -> pd.Series:
    """Min-max scale to 0-1. A constant series maps to 0.5, so a factor with no
    variance contributes neutrally to a composite score instead of skewing it."""
    lo, hi = float(series.min()), float(series.max())
    if hi - lo < 1e-9:
        return pd.Series([0.5] * len(series), index=series.index)
    return (series - lo) / (hi - lo)
