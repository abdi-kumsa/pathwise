"""
Education-supply intelligence — the Ministry of Education view.

Answers "which fields are emerging and worth investing in?" by joining the two
Assets datasets on the shared field vocabulary (see services/_datasets.py):

    education supply  (enrollment CSV, field_of_study)
            ═══ joined on the identical nine values ═══
    labour demand     (jobs CSV, job_family)

The centrepiece is get_investment_quadrant(): demand growth on one axis, the
graduate supply growth meant to serve it on the other. A field where demand is
climbing faster than supply is where new capacity pays off.
"""
from . import _datasets as ds
from . import labour_market_service as labour
from ._cache import ttl_cache


# ── Overview ──────────────────────────────────────────────────────────────────

@ttl_cache
def get_overview() -> dict:
    e = ds.enrollment()

    by_year = e.groupby('year')['enrollment_count'].sum()
    growth = ds.cagr(
        float(by_year.loc[ds.YEAR_MIN]),
        float(by_year.loc[ds.YEAR_MAX]),
        ds.YEAR_MAX - ds.YEAR_MIN,
    )

    return {
        'total_enrollment':      int(e['enrollment_count'].sum()),
        'enrollment_latest_year': int(by_year.loc[ds.YEAR_MAX]),
        'enrollment_cagr_pct':   growth,
        'total_applications':    int(e['applications_count'].sum()),
        'institutions':          int(e['institution_name'].nunique()),
        'programs':              int(e['program_name'].nunique()),
        'fields':                int(e['field_of_study'].nunique()),
        'avg_employment_rate_pct': round(float(e['employment_rate_6mo_pct'].mean()), 1),
        'avg_tuition':           round(float(e['tuition_usd'].mean()), 2),
        'avg_net_price':         round(float(e['net_price'].mean()), 2),
        'avg_roi_10yr':          round(float(e['roi_10yr_usd'].mean()), 2),
        'stem_share_pct':        round(float(e['stem_designated'].mean()) * 100, 1),
        'dataset_label':         ds.DATASET_LABEL,
    }


# ── Field trends ──────────────────────────────────────────────────────────────

@ttl_cache
def get_field_trends() -> list:
    """Enrollment and applications per field per year — the supply trajectory."""
    e = ds.enrollment()

    enrol = e.pivot_table(index='field_of_study', columns='year',
                          values='enrollment_count', aggfunc='sum').fillna(0)
    apps = e.pivot_table(index='field_of_study', columns='year',
                         values='applications_count', aggfunc='sum').fillna(0)

    rows = []
    for field in enrol.index:
        es, as_ = enrol.loc[field], apps.loc[field]
        rows.append({
            'field': field,
            'enrollment_cagr_pct': ds.cagr(
                float(es.get(ds.YEAR_MIN, 0)), float(es.get(ds.YEAR_MAX, 0)),
                ds.YEAR_MAX - ds.YEAR_MIN,
            ),
            'total_enrollment': int(es.sum()),
            'series': [
                {
                    'year': int(y),
                    'enrollment': int(es[y]),
                    'applications': int(as_.get(y, 0)),
                }
                for y in sorted(es.index)
            ],
        })

    rows.sort(key=lambda r: r['enrollment_cagr_pct'], reverse=True)
    return rows


# ── Investment quadrant — the MoE centrepiece ─────────────────────────────────

@ttl_cache
def get_investment_quadrant() -> dict:
    """Plot every field by labour-demand growth against graduate-supply growth.

    Quadrants, split at the median of each axis so they always partition the
    nine fields rather than depending on an arbitrary absolute threshold:

        Invest          high demand growth, low supply growth  -> expand capacity
        Sustain         high demand growth, high supply growth -> keep pace
        Oversupply risk low demand growth,  high supply growth -> slow intake
        Review          low demand growth,  low supply growth  -> reassess
    """
    e = ds.enrollment()
    j = ds.jobs()

    enrol = e.pivot_table(index='field_of_study', columns='year',
                          values='enrollment_count', aggfunc='sum').fillna(0)
    openings = j.pivot_table(index='job_family', columns='year',
                             values='job_openings_count', aggfunc='sum').fillna(0)

    span = ds.YEAR_MAX - ds.YEAR_MIN

    points = []
    for field in ds.FIELDS:
        if field not in enrol.index or field not in openings.index:
            continue
        es, os_ = enrol.loc[field], openings.loc[field]

        supply_growth = ds.cagr(float(es.get(ds.YEAR_MIN, 0)), float(es.get(ds.YEAR_MAX, 0)), span)
        demand_growth = ds.cagr(float(os_.get(ds.YEAR_MIN, 0)), float(os_.get(ds.YEAR_MAX, 0)), span)

        sub_e = e[e['field_of_study'] == field]
        sub_j = j[j['job_family'] == field]

        points.append({
            'field':               field,
            'demand_growth_pct':   demand_growth,
            'supply_growth_pct':   supply_growth,
            'demand_openings':     int(os_.sum()),
            'supply_enrollment':   int(es.sum()),
            'supply_demand_ratio': round(float(sub_j['supply_demand_ratio'].mean()), 3),
            'median_salary':       round(float(sub_e['median_salary_field_usd'].mean()), 2),
            'employment_rate_pct': round(float(sub_e['employment_rate_6mo_pct'].mean()), 1),
            'roi_10yr':            round(float(sub_e['roi_10yr_usd'].mean()), 2),
            'programs':            ds.family_to_programs().get(field, []),
        })

    if not points:
        return {'points': [], 'demand_median': 0, 'supply_median': 0, 'dataset_label': ds.DATASET_LABEL}

    d_med = _median([p['demand_growth_pct'] for p in points])
    s_med = _median([p['supply_growth_pct'] for p in points])

    for p in points:
        high_d = p['demand_growth_pct'] >= d_med
        high_s = p['supply_growth_pct'] >= s_med
        if high_d and not high_s:
            p['quadrant'], p['action'] = 'Invest', 'Expand capacity — demand is outpacing graduate supply'
        elif high_d and high_s:
            p['quadrant'], p['action'] = 'Sustain', 'Maintain investment — supply is keeping pace with demand'
        elif not high_d and high_s:
            p['quadrant'], p['action'] = 'Oversupply risk', 'Moderate intake — supply is growing faster than demand'
        else:
            p['quadrant'], p['action'] = 'Review', 'Reassess — neither demand nor supply is growing'

    points.sort(key=lambda p: p['demand_growth_pct'] - p['supply_growth_pct'], reverse=True)

    return {
        'points':        points,
        'demand_median': d_med,
        'supply_median': s_med,
        'invest_fields': [p['field'] for p in points if p['quadrant'] == 'Invest'],
        'dataset_label': ds.DATASET_LABEL,
    }


def _median(values: list) -> float:
    s = sorted(values)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return round(s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2, 2)


# ── Investment priority ranking ───────────────────────────────────────────────

# Weights are published in the API response so the ranking is auditable rather
# than a black box. They must sum to 1.0.
_PRIORITY_WEIGHTS = {
    'demand_growth':   0.30,   # is the labour market for this field growing?
    'supply_shortfall': 0.30,  # how far short is graduate supply?
    'employment_rate': 0.20,   # do graduates actually get hired?
    'roi':             0.20,   # is it worth it for the student?
}


@ttl_cache
def get_investment_priority() -> dict:
    """Rank the nine fields for investment, with a per-factor breakdown."""
    import pandas as pd

    quadrant = get_investment_quadrant()['points']
    gap = {f['field']: f for f in labour.get_supply_demand_gap()['fields']}

    if not quadrant:
        return {'fields': [], 'weights': _PRIORITY_WEIGHTS, 'dataset_label': ds.DATASET_LABEL}

    df = pd.DataFrame(quadrant)
    # Shortfall: 1 - coverage, so a field whose supply meets 20% of demand
    # scores far higher than one already at 90%.
    df['shortfall'] = df['field'].map(
        lambda f: max(0.0, 100.0 - gap.get(f, {}).get('coverage_pct', 100.0))
    )

    components = {
        'demand_growth':    ds.normalise(df['demand_growth_pct']),
        'supply_shortfall': ds.normalise(df['shortfall']),
        'employment_rate':  ds.normalise(df['employment_rate_pct']),
        'roi':              ds.normalise(df['roi_10yr']),
    }

    score = sum(components[k] * w for k, w in _PRIORITY_WEIGHTS.items())
    df['score'] = (score * 100).round(1)

    rows = []
    # Do NOT reset_index here: `components` is still keyed by the original row
    # index, and r.name is what looks each factor up. Renumbering the rows would
    # silently pair every field with another field's factor values.
    for rank, (_, r) in enumerate(df.sort_values('score', ascending=False).iterrows(), start=1):
        field = r['field']
        rows.append({
            'rank':   rank,
            'field':  field,
            'score':  float(r['score']),
            'quadrant': r['quadrant'],
            'action': r['action'],
            'programs': r['programs'],
            'factors': [
                {
                    'factor':     k,
                    'weight':     w,
                    'normalised': round(float(components[k].loc[r.name]), 3),
                    'contribution': round(float(components[k].loc[r.name]) * w * 100, 1),
                }
                for k, w in _PRIORITY_WEIGHTS.items()
            ],
            'demand_growth_pct':   float(r['demand_growth_pct']),
            'supply_growth_pct':   float(r['supply_growth_pct']),
            'coverage_pct':        gap.get(field, {}).get('coverage_pct'),
            'employment_rate_pct': float(r['employment_rate_pct']),
            'roi_10yr':            float(r['roi_10yr']),
        })

    return {
        'fields':  rows,
        'weights': _PRIORITY_WEIGHTS,
        'method': (
            "Each factor is min-max normalised across the nine fields, then "
            "combined with the published weights. Scores are relative, not absolute."
        ),
        'dataset_label': ds.DATASET_LABEL,
    }


# ── Field detail ──────────────────────────────────────────────────────────────

@ttl_cache
def get_field_detail(field: str) -> dict:
    """Full education profile for one field of study."""
    e = ds.enrollment()
    sub = e[e['field_of_study'] == field]
    if sub.empty:
        raise ValueError(f"Unknown field '{field}'")

    by_year = sub.groupby('year').agg(
        enrollment=('enrollment_count', 'sum'),
        applications=('applications_count', 'sum'),
        acceptance=('acceptance_rate_pct', 'mean'),
        yield_rate=('yield_rate_pct', 'mean'),
    )

    programs = []
    for name, g in sub.groupby('program_name'):
        programs.append({
            'program':            name,
            'level':              g['program_level'].mode().iloc[0],
            'enrollment':         int(g['enrollment_count'].sum()),
            'applications':       int(g['applications_count'].sum()),
            'acceptance_rate_pct': round(float(g['acceptance_rate_pct'].mean()), 1),
            'yield_rate_pct':     round(float(g['yield_rate_pct'].mean()), 1),
            'tuition':            round(float(g['tuition_usd'].mean()), 2),
            'net_price':          round(float(g['net_price'].mean()), 2),
            'roi_10yr':           round(float(g['roi_10yr_usd'].mean()), 2),
            'employment_rate_pct': round(float(g['employment_rate_6mo_pct'].mean()), 1),
        })
    programs.sort(key=lambda p: p['enrollment'], reverse=True)

    # Demand side for the same field, joined on the shared vocabulary.
    j = ds.jobs()
    demand = j[j['job_family'] == field]

    return {
        'field': field,
        'total_enrollment':    int(sub['enrollment_count'].sum()),
        'total_applications':  int(sub['applications_count'].sum()),
        'avg_acceptance_rate_pct': round(float(sub['acceptance_rate_pct'].mean()), 1),
        'avg_yield_rate_pct':  round(float(sub['yield_rate_pct'].mean()), 1),
        'avg_tuition':         round(float(sub['tuition_usd'].mean()), 2),
        'avg_net_price':       round(float(sub['net_price'].mean()), 2),
        'avg_roi_10yr':        round(float(sub['roi_10yr_usd'].mean()), 2),
        'employment_rate_pct': round(float(sub['employment_rate_6mo_pct'].mean()), 1),
        'median_salary':       round(float(sub['median_salary_field_usd'].mean()), 2),
        'stem_designated':     bool(sub['stem_designated'].mode().iloc[0]),
        'demand_openings':     int(demand['job_openings_count'].sum()) if not demand.empty else 0,
        'demand_growth_pct':   round(float(demand['demand_growth_rate_pct'].mean()), 2) if not demand.empty else 0.0,
        'series': [
            {
                'year': int(y),
                'enrollment': int(r['enrollment']),
                'applications': int(r['applications']),
                'acceptance_rate_pct': round(float(r['acceptance']), 1),
                'yield_rate_pct': round(float(r['yield_rate']), 1),
            }
            for y, r in by_year.iterrows()
        ],
        'programs':      programs,
        'dataset_label': ds.DATASET_LABEL,
    }
