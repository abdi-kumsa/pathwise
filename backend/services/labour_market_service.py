"""
Labour-market intelligence — the Ministry of Labour view.

Answers "which occupations are emerging, and where is the workforce short?"
from Assets/job_market_forecasting_data.csv.

The headline signal is the supply-demand gap: `job_openings_count` against
`relevant_graduates_count + bootcamp_completions`. That has real between-field
variance, unlike the graduate fit classification in mismatch_service, and is
what the dashboard leads with.
"""
import pandas as pd

from . import _datasets as ds
from ._cache import ttl_cache


# ── Overview ──────────────────────────────────────────────────────────────────

@ttl_cache
def get_overview() -> dict:
    j = ds.jobs()
    latest = j[j['year'] == ds.YEAR_MAX]

    by_year = j.groupby('year')['job_openings_count'].sum()
    growth = ds.cagr(
        float(by_year.loc[ds.YEAR_MIN]),
        float(by_year.loc[ds.YEAR_MAX]),
        ds.YEAR_MAX - ds.YEAR_MIN,
    )

    # supply_demand_ratio < 1 means fewer qualified people than openings.
    undersupplied = int((j.groupby('job_family')['supply_demand_ratio'].mean() < 1.0).sum())

    return {
        'total_openings':        int(j['job_openings_count'].sum()),
        'openings_latest_year':  int(latest['job_openings_count'].sum()),
        'openings_cagr_pct':     growth,
        'avg_demand_growth_pct': round(float(j['demand_growth_rate_pct'].mean()), 2),
        'avg_supply_demand_ratio': round(float(j['supply_demand_ratio'].mean()), 3),
        'avg_time_to_fill_days': round(float(j['time_to_fill_days'].mean()), 1),
        'occupations_tracked':   int(j['job_title'].nunique()),
        'fields_tracked':        int(j['job_family'].nunique()),
        'undersupplied_fields':  undersupplied,
        'dataset_label':         ds.DATASET_LABEL,
    }


# ── Emerging occupations ──────────────────────────────────────────────────────

@ttl_cache
def get_emerging(level: str = 'family', top_n: int = 10) -> list:
    """Rank fields (or individual occupations) by growth.

    `level` is 'family' for the nine fields or 'title' for the 33 occupations.
    Each row carries its full yearly series so the UI can draw a sparkline
    without a second request.
    """
    key = 'job_family' if level == 'family' else 'job_title'
    j = ds.jobs()

    pivot = j.pivot_table(index=key, columns='year',
                          values='job_openings_count', aggfunc='sum').fillna(0)

    agg = j.groupby(key).agg(
        total_openings=('job_openings_count', 'sum'),
        avg_growth=('demand_growth_rate_pct', 'mean'),
        avg_salary=('avg_salary_usd', 'mean'),
        supply_demand_ratio=('supply_demand_ratio', 'mean'),
        time_to_fill=('time_to_fill_days', 'mean'),
    )

    rows = []
    for name in pivot.index:
        series = pivot.loc[name]
        first, last = float(series.get(ds.YEAR_MIN, 0)), float(series.get(ds.YEAR_MAX, 0))
        a = agg.loc[name]
        rows.append({
            key:                    name,
            'job_family':           name if key == 'job_family' else ds.title_to_family().get(name),
            'total_openings':       int(a['total_openings']),
            'openings_cagr_pct':    ds.cagr(first, last, ds.YEAR_MAX - ds.YEAR_MIN),
            'avg_growth_pct':       round(float(a['avg_growth']), 2),
            'avg_salary':           round(float(a['avg_salary']), 2),
            'supply_demand_ratio':  round(float(a['supply_demand_ratio']), 3),
            'time_to_fill_days':    round(float(a['time_to_fill']), 1),
            'series':               [
                {'year': int(y), 'openings': int(series[y])} for y in sorted(series.index)
            ],
        })

    rows.sort(key=lambda r: r['openings_cagr_pct'], reverse=True)
    return rows[:top_n]


# ── Supply vs demand ──────────────────────────────────────────────────────────

@ttl_cache
def get_supply_demand_gap() -> dict:
    """Workforce shortfall per field: openings vs the people qualified to fill them.

    Supply counts formal graduates plus bootcamp completions, since both feed
    the same hiring pipeline. A positive gap means unfilled demand.
    """
    j = ds.jobs()

    g = j.groupby('job_family').agg(
        openings=('job_openings_count', 'sum'),
        graduates=('relevant_graduates_count', 'sum'),
        bootcamp=('bootcamp_completions', 'sum'),
        ratio=('supply_demand_ratio', 'mean'),
        time_to_fill=('time_to_fill_days', 'mean'),
        salary=('avg_salary_usd', 'mean'),
    )

    fields = []
    for name, r in g.iterrows():
        supply = float(r['graduates'] + r['bootcamp'])
        demand = float(r['openings'])
        fields.append({
            'field':               name,
            'demand_openings':     int(demand),
            'supply_graduates':    int(r['graduates']),
            'supply_bootcamp':     int(r['bootcamp']),
            'supply_total':        int(supply),
            'gap':                 int(demand - supply),
            'coverage_pct':        round(supply / demand * 100, 1) if demand else 0.0,
            'supply_demand_ratio': round(float(r['ratio']), 3),
            'time_to_fill_days':   round(float(r['time_to_fill']), 1),
            'avg_salary':          round(float(r['salary']), 2),
        })

    fields.sort(key=lambda f: f['gap'], reverse=True)
    _assign_severity(fields)

    return {
        'fields':            fields,
        'total_gap':         sum(f['gap'] for f in fields),
        'largest_gap_field': fields[0]['field'] if fields else None,
        'severity_basis': (
            "Severity ranks the absolute shortfall (unfilled openings) across the "
            "nine fields. Coverage is 90-93% everywhere in this dataset, so the "
            "ratio does not separate them — the headcount shortfall does."
        ),
        'dataset_label':     ds.DATASET_LABEL,
    }


def _assign_severity(fields: list) -> None:
    """Label each field by where its absolute shortfall sits among the nine.

    Deliberately relative, not absolute. Coverage ratios in this dataset span
    only 90-93%, so any fixed coverage threshold would bucket every field
    identically and tell the reader nothing. The unfilled-headcount gap ranges
    across an order of magnitude and is what actually distinguishes them —
    so severity is a quartile rank of that, and the response says so.
    """
    if not fields:
        return
    gaps = sorted((f['gap'] for f in fields), reverse=True)
    n = len(gaps)
    q1 = gaps[max(0, n // 4 - 1)]
    q2 = gaps[max(0, n // 2 - 1)]
    q3 = gaps[max(0, (3 * n) // 4 - 1)]

    for f in fields:
        if f['gap'] >= q1:
            f['severity'] = 'critical'
        elif f['gap'] >= q2:
            f['severity'] = 'high'
        elif f['gap'] >= q3:
            f['severity'] = 'moderate'
        else:
            f['severity'] = 'low'


# ── Regional ──────────────────────────────────────────────────────────────────

@ttl_cache
def get_regional_demand(field: str = None, top_n: int = 20) -> dict:
    """Demand by metro area, optionally narrowed to one field."""
    j = ds.jobs()
    if field:
        j = j[j['job_family'] == field]
        if j.empty:
            raise ValueError(f"Unknown field '{field}'")

    metro = j.groupby('metro_area').agg(
        openings=('job_openings_count', 'sum'),
        salary=('avg_salary_usd', 'mean'),
        growth=('demand_growth_rate_pct', 'mean'),
    ).sort_values('openings', ascending=False).head(top_n)

    state = j.groupby('state_province')['job_openings_count'].sum().sort_values(ascending=False)

    remote = j.groupby('remote_allowed')['job_openings_count'].sum()
    remote_total = float(remote.sum())

    return {
        'field': field,
        'metros': [
            {
                'metro':     name,
                'openings':  int(r['openings']),
                'avg_salary': round(float(r['salary']), 2),
                'growth_pct': round(float(r['growth']), 2),
            }
            for name, r in metro.iterrows()
        ],
        'states': [
            {'state': name, 'openings': int(v)} for name, v in state.items()
        ],
        'remote_share_pct': round(float(remote.get(True, 0)) / remote_total * 100, 1) if remote_total else 0.0,
        'dataset_label': ds.DATASET_LABEL,
    }


# ── Occupation detail ─────────────────────────────────────────────────────────

@ttl_cache
def get_occupation_detail(job_title: str) -> dict:
    """Everything known about one of the 33 occupations."""
    j = ds.jobs()
    sub = j[j['job_title'] == job_title]
    if sub.empty:
        raise ValueError(f"Unknown occupation '{job_title}'")

    by_year = sub.groupby('year').agg(
        openings=('job_openings_count', 'sum'),
        salary=('avg_salary_usd', 'mean'),
    )

    first = float(by_year['openings'].get(ds.YEAR_MIN, 0))
    last  = float(by_year['openings'].get(ds.YEAR_MAX, 0))

    return {
        'job_title':   job_title,
        'job_family':  sub['job_family'].iloc[0],
        'soc_code':    str(sub['soc_code'].iloc[0]),
        'total_openings':    int(sub['job_openings_count'].sum()),
        'openings_cagr_pct': ds.cagr(first, last, ds.YEAR_MAX - ds.YEAR_MIN),
        'avg_growth_pct':    round(float(sub['demand_growth_rate_pct'].mean()), 2),
        'avg_salary':        round(float(sub['avg_salary_usd'].mean()), 2),
        'supply_demand_ratio': round(float(sub['supply_demand_ratio'].mean()), 3),
        'time_to_fill_days': round(float(sub['time_to_fill_days'].mean()), 1),
        'remote_share_pct':  round(float(sub['remote_allowed'].mean()) * 100, 1),
        'series': [
            {
                'year': int(y),
                'openings': int(r['openings']),
                'avg_salary': round(float(r['salary']), 2),
            }
            for y, r in by_year.iterrows()
        ],
        'top_industries': _top_counts(sub, 'posting_industry', 5),
        'top_metros':     _top_counts(sub, 'metro_area', 5),
        'company_sizes':  _top_counts(sub, 'company_size', 5),
        'dataset_label':  ds.DATASET_LABEL,
    }


def _top_counts(df: pd.DataFrame, column: str, n: int) -> list:
    s = df.groupby(column)['job_openings_count'].sum().sort_values(ascending=False).head(n)
    return [{'name': k, 'openings': int(v)} for k, v in s.items()]
