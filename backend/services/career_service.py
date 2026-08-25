"""
Career explorer — the Student view, and the literal ask in the client feedback:

    "for students provide some potential job and the system should recommend
     department to join for that particular job"

Given a target occupation, rank the twelve programmes on how well each routes a
student into it. Reuses the trained XGBoost placement model through
services.ml_service exactly as escape_route_service already does — no new model.

Scoring is deliberately transparent: every recommendation carries the weight and
normalised value of each factor that produced it, mirroring the SHAP
explainability the rest of the project is built on. A student should be able to
see *why* a department was suggested, not just that it was.
"""
import pandas as pd

from . import _datasets as ds
from ._cache import ttl_cache

# Published in every response. Must sum to 1.0.
WEIGHTS = {
    'field_match':      0.30,   # does this programme actually teach the field?
    'placement_odds':   0.25,   # will this student get placed from it?
    'employment_rate':  0.15,   # do its graduates get hired at all?
    'earnings':         0.15,   # what does the field pay?
    'accessibility':    0.10,   # can this student realistically get in?
    'affordability':    0.05,   # what will it cost them?
}

# A programme outside the target field still routes into it to a degree. Rather
# than dropping it, score partial credit so the student always sees a full,
# ranked list of options with honest relative scoring.
_OFF_FIELD_MATCH = 25.0
_ON_FIELD_MATCH  = 100.0

# Fields that share substantial skill overlap score between the two.
_ADJACENT = {
    'AI/ML Engineering':     {'Data & Analytics', 'Software Engineering'},
    'Data & Analytics':      {'AI/ML Engineering', 'Business Intelligence'},
    'Business Intelligence': {'Data & Analytics'},
    'Software Engineering':  {'AI/ML Engineering', 'DevOps', 'Cloud Infrastructure'},
    'DevOps':                {'Cloud Infrastructure', 'Software Engineering'},
    'Cloud Infrastructure':  {'DevOps', 'Cybersecurity', 'Software Engineering'},
    'Cybersecurity':         {'Cloud Infrastructure'},
    'Product Management':    {'UX Design', 'Business Intelligence'},
    'UX Design':             {'Product Management'},
}
_ADJACENT_MATCH = 60.0


# ── Catalogue ─────────────────────────────────────────────────────────────────

@ttl_cache
def list_jobs() -> list:
    """All 33 occupations with their field — powers the typeahead."""
    return ds.job_titles()


@ttl_cache
def search(query: str, limit: int = 10) -> list:
    """Substring search across occupations and fields.

    Prefix matches rank above mid-string matches so typing "data" surfaces
    "Data Analyst" before "Warehouse Data Architect".
    """
    q = (query or '').strip().lower()
    if not q:
        return []

    hits = []
    for entry in ds.job_titles():
        title = entry['job_title'].lower()
        if title.startswith(q):
            hits.append((0, entry))
        elif q in title:
            hits.append((1, entry))
        elif q in entry['job_family'].lower():
            hits.append((2, entry))

    hits.sort(key=lambda h: (h[0], h[1]['job_title']))
    return [h[1] for h in hits[:limit]]


# ── The recommender ───────────────────────────────────────────────────────────

def recommend(job_title: str, profile: dict = None, top_n: int = 5) -> dict:
    """Rank programmes for a student targeting `job_title`.

    `profile` is optional. With it, placement odds come from the XGBoost model
    run against this specific student in each programme. Without it, the
    programme's historical placement rate stands in — so the page is useful
    before a student has entered anything.
    """
    family = ds.title_to_family().get(job_title)
    if family is None:
        raise ValueError(f"Unknown occupation '{job_title}'")

    demand = _demand_context(job_title, family)
    rows = _score_programs(family, profile)

    df = pd.DataFrame(rows)
    components = {
        'field_match':     ds.normalise(df['field_match']),
        'placement_odds':  ds.normalise(df['placement_probability']),
        'employment_rate': ds.normalise(df['employment_rate_pct']),
        'earnings':        ds.normalise(df['median_salary']),
        'accessibility':   ds.normalise(df['acceptance_rate_pct']),
        # Cheaper is better, so invert before normalising.
        'affordability':   ds.normalise(-df['net_price']),
    }
    df['score'] = (sum(components[k] * w for k, w in WEIGHTS.items()) * 100).round(1)

    ranked = []
    for rank, (_, r) in enumerate(df.sort_values('score', ascending=False).iterrows(), start=1):
        ranked.append({
            'rank':            rank,
            'program':         r['program'],
            'field':           r['field'],
            'score':           float(r['score']),
            'is_direct_route': bool(r['field'] == family),
            'why':             _why(r, family),
            'placement_probability': round(float(r['placement_probability']), 4),
            'employment_rate_pct':   float(r['employment_rate_pct']),
            'median_salary':         float(r['median_salary']),
            'acceptance_rate_pct':   float(r['acceptance_rate_pct']),
            'net_price':             float(r['net_price']),
            'roi_10yr':              float(r['roi_10yr']),
            'level':                 r['level'],
            'factors': [
                {'factor': k, 'weight': w,
                 'normalised': round(float(components[k].loc[r.name]), 3),
                 'contribution': round(float(components[k].loc[r.name]) * w * 100, 1)}
                for k, w in WEIGHTS.items()
            ],
        })

    return {
        'job_title':       job_title,
        'job_family':      family,
        'demand':          demand,
        'recommendations': ranked[:top_n],
        'all_programs':    ranked,
        'weights':         WEIGHTS,
        'personalised':    profile is not None,
        'method': (
            "Each factor is min-max normalised across the twelve programmes, then "
            "combined with the published weights. Placement odds come from the "
            + ("XGBoost model run on your profile."
               if profile else "programme's historical placement rate.")
        ),
        'dataset_label': ds.DATASET_LABEL,
    }


def _demand_context(job_title: str, family: str) -> dict:
    """What the labour market looks like for this occupation."""
    j = ds.jobs()
    sub = j[j['job_title'] == job_title]

    by_year = sub.groupby('year')['job_openings_count'].sum()
    first = float(by_year.get(ds.YEAR_MIN, 0))
    last  = float(by_year.get(ds.YEAR_MAX, 0))

    return {
        'total_openings':      int(sub['job_openings_count'].sum()),
        'openings_cagr_pct':   ds.cagr(first, last, ds.YEAR_MAX - ds.YEAR_MIN),
        'avg_growth_pct':      round(float(sub['demand_growth_rate_pct'].mean()), 2),
        'avg_salary':          round(float(sub['avg_salary_usd'].mean()), 2),
        'supply_demand_ratio': round(float(sub['supply_demand_ratio'].mean()), 3),
        'time_to_fill_days':   round(float(sub['time_to_fill_days'].mean()), 1),
        'remote_share_pct':    round(float(sub['remote_allowed'].mean()) * 100, 1),
        'outlook':             _outlook(float(sub['supply_demand_ratio'].mean())),
        'series': [{'year': int(y), 'openings': int(v)} for y, v in by_year.items()],
        'top_metros': [
            {'metro': k, 'openings': int(v)}
            for k, v in sub.groupby('metro_area')['job_openings_count']
                           .sum().sort_values(ascending=False).head(5).items()
        ],
    }


def _outlook(ratio: float) -> str:
    """supply_demand_ratio below 1 means employers cannot fill the roles."""
    if ratio < 0.7:
        return 'Severe shortage — strong hiring market for graduates'
    if ratio < 0.9:
        return 'Undersupplied — favourable hiring market'
    if ratio <= 1.1:
        return 'Balanced supply and demand'
    return 'Oversupplied — expect stronger competition'


def _score_programs(family: str, profile: dict) -> list:
    """Gather the raw (un-normalised) factor values for all twelve programmes."""
    e = ds.enrollment()
    prog_field = ds.program_to_family()
    adjacent = _ADJACENT.get(family, set())

    historical = _historical_placement_rates()

    rows = []
    for program in ds.PROGRAMS:
        g = e[e['program_name'] == program]
        if g.empty:
            continue

        field = prog_field.get(program, '')
        if field == family:
            match = _ON_FIELD_MATCH
        elif field in adjacent:
            match = _ADJACENT_MATCH
        else:
            match = _OFF_FIELD_MATCH

        rows.append({
            'program':               program,
            'field':                 field,
            'level':                 g['program_level'].mode().iloc[0],
            'field_match':           match,
            'placement_probability': _placement_odds(program, profile, historical),
            'employment_rate_pct':   round(float(g['employment_rate_6mo_pct'].mean()), 1),
            'median_salary':         round(float(g['median_salary_field_usd'].mean()), 2),
            'acceptance_rate_pct':   round(float(g['acceptance_rate_pct'].mean()), 1),
            'net_price':             round(float(g['net_price'].mean()), 2),
            'roi_10yr':              round(float(g['roi_10yr_usd'].mean()), 2),
        })

    return rows


@ttl_cache
def _historical_placement_rates() -> dict:
    """Observed placement rate per programme, the fallback when no profile is given."""
    f = ds.features()
    return {p: float(g['placed'].mean()) for p, g in f.groupby('program')}


def _placement_odds(program: str, profile: dict, historical: dict) -> float:
    """XGBoost odds for this student in this programme, or the historical rate.

    A model failure for one programme must not fail the whole request, so it
    falls back to the historical rate rather than propagating.
    """
    if not profile:
        return historical.get(program, 0.5)

    try:
        from .ml_service import predict_placement
        result = predict_placement({**profile, 'program': program})
        return float(result['placed_probability'])
    except Exception:
        return historical.get(program, 0.5)


def _why(row, family: str) -> str:
    """One plain sentence explaining the ranking, for the card header."""
    if row['field'] == family:
        return (f"Trains directly for {family}. "
                f"{row['employment_rate_pct']:.0f}% of graduates are employed within 6 months.")
    if row['field'] in _ADJACENT.get(family, set()):
        return (f"Adjacent to {family} via {row['field']} — substantial skill overlap, "
                f"{row['employment_rate_pct']:.0f}% employed within 6 months.")
    return (f"Indirect route through {row['field']}. "
            f"Consider it only alongside targeted {family} experience.")
