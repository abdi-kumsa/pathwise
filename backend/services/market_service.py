"""
Market demand data service.
Reads data/mock/placements.csv and data/processed/features.parquet to compute
all values served by the /api/market/* endpoints.
"""
from pathlib import Path
import functools
import time
import numpy as np
import pandas as pd

# ── TTL cache ─────────────────────────────────────────────────────────────────
# Simple 5-minute in-memory cache keyed by (function, args).
# Thread-safe for CPython (GIL protects dict updates).

_TTL_SECONDS = 300   # 5 minutes
_cache: dict = {}

def _ttl_cache(fn):
    """Decorator: cache return value for _TTL_SECONDS, then recompute."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        key = (fn.__name__, args, tuple(sorted(kwargs.items())))
        entry = _cache.get(key)
        if entry and (time.monotonic() - entry[0]) < _TTL_SECONDS:
            return entry[1]
        result = fn(*args, **kwargs)
        _cache[key] = (time.monotonic(), result)
        return result
    return wrapper

_ROOT = Path(__file__).resolve().parent.parent.parent
_PLACEMENTS_CSV = _ROOT / 'data' / 'mock' / 'placements.csv'
_PARQUET = _ROOT / 'data' / 'processed' / 'features.parquet'

# ── Static lookup tables ──────────────────────────────────────────────────────

_COMPANY_REGION = {
    'Microsoft':            'West Coast',
    'Amazon Web Services':  'West Coast',
    'Intel':                'West Coast',
    'Cisco Systems':        'West Coast',
    'Visa':                 'West Coast',
    'Stripe':               'West Coast',
    'JPMorgan Chase':       'Northeast',
    'Bloomberg':            'Northeast',
    'IBM':                  'Northeast',
    'UnitedHealth Group':   'Midwest',
    'Deloitte':             'Midwest',
    'Infosys':              'Southeast',
    'Lockheed Martin':      'Southeast',
    'Raytheon Technologies': 'Southeast',
    'SAP':                  'International',
}

_COMPANY_SECTOR = {
    'Microsoft':            'Technology',
    'Amazon Web Services':  'Technology',
    'Intel':                'Technology',
    'Cisco Systems':        'Technology',
    'SAP':                  'Technology',
    'Stripe':               'FinTech',
    'Visa':                 'FinTech',
    'JPMorgan Chase':       'Finance',
    'Bloomberg':            'Finance',
    'UnitedHealth Group':   'Healthcare',
    'Deloitte':             'Consulting',
    'IBM':                  'Consulting',
    'Infosys':              'Consulting',
    'Lockheed Martin':      'Defense',
    'Raytheon Technologies': 'Defense',
}

_SKILL_MAP = {
    'gpa_scaled':                 'Academic Performance (GPA)',
    'internships':                'Industry Experience',
    'communication_score_scaled': 'Communication Skills',
    'projects':                   'Project Portfolio',
}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _load_placements() -> pd.DataFrame:
    df = pd.read_csv(_PLACEMENTS_CSV)
    df['placed'] = df['placed'].map(lambda x: str(x).lower() == 'true')
    return df


def _load_parquet() -> pd.DataFrame:
    return pd.read_parquet(_PARQUET)


# ── Public service functions ──────────────────────────────────────────────────

@_ttl_cache
def get_market_overview() -> dict:
    df = _load_placements()
    placed = df[df['placed']]
    return {
        'total_companies':    int(df['company'].nunique()),
        'total_placements':   int(len(placed)),
        'avg_salary':         round(float(placed['salary'].mean()), 2),
        'avg_time_to_hire':   round(float(placed['time_to_hire'].mean()), 1),
        'top_role':           placed['role'].value_counts().index[0],
    }


@_ttl_cache
def get_top_companies(n: int = 10) -> list:
    df = _load_placements()
    placed = df[df['placed']]
    counts = placed['company'].value_counts().head(n)
    return [{'company': c, 'count': int(v)} for c, v in counts.items()]


def get_job_internship_ratio() -> dict:
    placements = _load_placements()
    parquet = _load_parquet()
    placed = placements[placements['placed']]
    job_count = int(len(placed))
    intern_count = int(parquet['internships'].sum())
    ratio = round(job_count / intern_count, 2) if intern_count > 0 else 0.0
    return {'job_count': job_count, 'internship_count': intern_count, 'ratio': ratio}


@_ttl_cache
def get_skill_gap() -> dict:
    from .ml_service import get_shap_cache

    shap_values, _, feature_names, _ = get_shap_cache()
    parquet = _load_parquet()

    feature_names_list = list(feature_names)
    mean_abs = np.abs(shap_values).mean(axis=0)
    max_shap = float(mean_abs.max())

    skills = []
    for feat, label in _SKILL_MAP.items():
        if feat not in feature_names_list:
            continue
        idx = feature_names_list.index(feat)
        demand_score = round(float(mean_abs[idx] / max_shap * 100), 1)

        # Coverage: how well students currently meet this demand (0–100 scale)
        if feat in parquet.columns:
            avg_scaled = float(parquet[feat].mean())
            coverage = round(min(avg_scaled * 100, 100.0), 1)
        elif feat == 'internships':
            avg_raw = float(parquet['internships'].mean())
            coverage = round(min(avg_raw / 4.0 * 100, 100.0), 1)
        elif feat == 'projects':
            avg_raw = float(parquet['projects'].mean())
            coverage = round(min(avg_raw / 5.0 * 100, 100.0), 1)
        else:
            coverage = 50.0

        gap = round(max(demand_score - coverage, 0.0), 1)
        skills.append({
            'skill':                label,
            'demand_score':         demand_score,
            'curriculum_coverage':  coverage,
            'gap_score':            gap,
        })

    top_gap = max(skills, key=lambda s: s['gap_score'])
    avg_gap = round(sum(s['gap_score'] for s in skills) / len(skills), 1)
    return {'skills': skills, 'top_gap_skill': top_gap['skill'], 'avg_gap_score': avg_gap}


@_ttl_cache
def get_regional_hiring() -> list:
    df = _load_placements()
    placed = df[df['placed']].copy()
    placed['region'] = placed['company'].map(_COMPANY_REGION).fillna('Other')
    counts = placed.groupby('region').size().sort_values(ascending=False)
    return [{'location': r, 'count': int(c)} for r, c in counts.items()]


@_ttl_cache
def get_hiring_sources() -> list:
    df = _load_placements()
    placed = df[df['placed']].copy()
    placed['sector'] = placed['company'].map(_COMPANY_SECTOR).fillna('Other')
    counts = placed.groupby('sector').size().sort_values(ascending=False)
    return [{'source': s, 'count': int(c)} for s, c in counts.items()]


def get_demand_forecast(months_ahead: int = 12) -> list:
    from .ml_service import forecast_demand
    fc = forecast_demand(months_ahead)
    return [
        {
            'month':               str(row['month'].date()),
            'predicted_postings':  int(row['predicted_postings']),
            'lower_bound':         int(row['lower_bound']),
            'upper_bound':         int(row['upper_bound']),
        }
        for _, row in fc.iterrows()
    ]
