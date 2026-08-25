"""
Institution intelligence — the University view.

Answers "which fields should we resource, expand, or consolidate?" for ONE
institution at a time.

Row scoping: every public function takes `institution` as its first argument,
and the router always passes the value from the caller's JWT rather than from a
query parameter. A university therefore cannot request another's data even by
crafting the request. Peer comparisons are anonymised to "Peer A/B/C..." so
benchmarking never leaks a named competitor's figures.
"""
import pandas as pd

from . import _datasets as ds
from ._cache import ttl_cache


def _scoped(institution: str) -> pd.DataFrame:
    """All enrollment rows for one institution, or raise if unknown."""
    e = ds.enrollment()
    sub = e[e['institution_name'] == institution]
    if sub.empty:
        raise ValueError(f"Unknown institution '{institution}'")
    return sub


# ── Profile ───────────────────────────────────────────────────────────────────

@ttl_cache
def get_profile(institution: str) -> dict:
    sub = _scoped(institution)

    by_year = sub.groupby('year')['enrollment_count'].sum()
    growth = ds.cagr(
        float(by_year.get(ds.YEAR_MIN, 0)),
        float(by_year.get(ds.YEAR_MAX, 0)),
        ds.YEAR_MAX - ds.YEAR_MIN,
    )

    return {
        'institution':       institution,
        'type':              sub['institution_type'].mode().iloc[0],
        'state':             sub['institution_state'].mode().iloc[0],
        'campus_setting':    sub['campus_setting'].mode().iloc[0],
        'us_news_ranking':   int(sub['us_news_ranking'].mode().iloc[0]),
        'total_enrollment':  int(sub['enrollment_count'].sum()),
        'enrollment_cagr_pct': growth,
        'total_applications': int(sub['applications_count'].sum()),
        'programs':          int(sub['program_name'].nunique()),
        'avg_acceptance_rate_pct': round(float(sub['acceptance_rate_pct'].mean()), 1),
        'avg_yield_rate_pct': round(float(sub['yield_rate_pct'].mean()), 1),
        'avg_tuition':       round(float(sub['tuition_usd'].mean()), 2),
        'avg_net_price':     round(float(sub['net_price'].mean()), 2),
        'total_marketing_spend': int(sub['marketing_spend_usd'].sum()),
        'avg_employment_rate_pct': round(float(sub['employment_rate_6mo_pct'].mean()), 1),
        'series': [
            {'year': int(y), 'enrollment': int(v)} for y, v in by_year.items()
        ],
        'dataset_label': ds.DATASET_LABEL,
    }


# ── Programme portfolio ───────────────────────────────────────────────────────

@ttl_cache
def get_portfolio(institution: str) -> dict:
    """Every programme this institution runs, with its enrolment funnel and cost."""
    sub = _scoped(institution)

    rows = []
    for name, g in sub.groupby('program_name'):
        enrolled = int(g['enrollment_count'].sum())
        spend    = float(g['marketing_spend_usd'].sum())
        rows.append({
            'program':             name,
            'field':               g['field_of_study'].mode().iloc[0],
            'level':               g['program_level'].mode().iloc[0],
            'delivery_mode':       g['delivery_mode'].mode().iloc[0],
            'enrollment':          enrolled,
            'applications':        int(g['applications_count'].sum()),
            'inquiries':           int(g['inquiry_count'].sum()),
            'acceptance_rate_pct': round(float(g['acceptance_rate_pct'].mean()), 1),
            'yield_rate_pct':      round(float(g['yield_rate_pct'].mean()), 1),
            'tuition':             round(float(g['tuition_usd'].mean()), 2),
            'net_price':           round(float(g['net_price'].mean()), 2),
            'marketing_spend':     int(spend),
            'cost_per_enrollment': round(spend / enrolled, 2) if enrolled else 0.0,
            'employment_rate_pct': round(float(g['employment_rate_6mo_pct'].mean()), 1),
            'roi_10yr':            round(float(g['roi_10yr_usd'].mean()), 2),
            'competitor_programs': int(g['competitor_programs_count'].mean()),
            'competitor_avg_tuition': round(float(g['competitor_avg_tuition_usd'].mean()), 2),
        })

    rows.sort(key=lambda r: r['enrollment'], reverse=True)

    return {
        'institution':   institution,
        'programs':      rows,
        'dataset_label': ds.DATASET_LABEL,
    }


# ── Expansion opportunities ───────────────────────────────────────────────────

# Published in the response so the recommendation is auditable.
_EXPANSION_WEIGHTS = {
    'demand_growth':     0.35,   # is the labour market for this field growing?
    'own_momentum':      0.25,   # is our own enrolment in it growing?
    'competitive_room':  0.20,   # how crowded is the field with competitors?
    'yield_strength':    0.20,   # do admitted students actually enrol?
}

_EXPAND_THRESHOLD    = 60.0
_CONSOLIDATE_THRESHOLD = 35.0


@ttl_cache
def get_expansion_opportunities(institution: str) -> dict:
    """Rank this institution's programmes for expansion, hold, or consolidation.

    Combines the institution's own trajectory with national labour demand for
    the field, and discounts fields already crowded with competitor programmes.
    """
    sub = _scoped(institution)
    j = ds.jobs()

    # National demand CAGR per field, computed once.
    openings = j.pivot_table(index='job_family', columns='year',
                             values='job_openings_count', aggfunc='sum').fillna(0)
    span = ds.YEAR_MAX - ds.YEAR_MIN
    demand_growth = {
        f: ds.cagr(float(openings.loc[f].get(ds.YEAR_MIN, 0)),
                   float(openings.loc[f].get(ds.YEAR_MAX, 0)), span)
        for f in openings.index
    }

    records = []
    for name, g in sub.groupby('program_name'):
        field = g['field_of_study'].mode().iloc[0]
        by_year = g.groupby('year')['enrollment_count'].sum()

        records.append({
            'program':           name,
            'field':             field,
            'own_growth_pct':    ds.cagr(float(by_year.get(ds.YEAR_MIN, 0)),
                                         float(by_year.get(ds.YEAR_MAX, 0)), span),
            'demand_growth_pct': demand_growth.get(field, 0.0),
            'enrollment':        int(g['enrollment_count'].sum()),
            'yield_rate_pct':    round(float(g['yield_rate_pct'].mean()), 1),
            'competitor_programs': int(g['competitor_programs_count'].mean()),
            'tuition':           round(float(g['tuition_usd'].mean()), 2),
            'competitor_avg_tuition': round(float(g['competitor_avg_tuition_usd'].mean()), 2),
            'employment_rate_pct': round(float(g['employment_rate_6mo_pct'].mean()), 1),
        })

    if not records:
        return {'institution': institution, 'programs': [],
                'weights': _EXPANSION_WEIGHTS, 'dataset_label': ds.DATASET_LABEL}

    df = pd.DataFrame(records)
    # Fewer competitors = more room, so invert before normalising.
    df['room'] = -df['competitor_programs']

    components = {
        'demand_growth':    ds.normalise(df['demand_growth_pct']),
        'own_momentum':     ds.normalise(df['own_growth_pct']),
        'competitive_room': ds.normalise(df['room']),
        'yield_strength':   ds.normalise(df['yield_rate_pct']),
    }
    df['score'] = (sum(components[k] * w for k, w in _EXPANSION_WEIGHTS.items()) * 100).round(1)

    out = []
    for _, r in df.sort_values('score', ascending=False).iterrows():
        score = float(r['score'])
        if score >= _EXPAND_THRESHOLD:
            rec = 'Expand'
        elif score <= _CONSOLIDATE_THRESHOLD:
            rec = 'Consolidate'
        else:
            rec = 'Hold'

        out.append({
            'program':           r['program'],
            'field':             r['field'],
            'score':             score,
            'recommendation':    rec,
            'rationale':         _rationale(rec, r),
            'own_growth_pct':    float(r['own_growth_pct']),
            'demand_growth_pct': float(r['demand_growth_pct']),
            'enrollment':        int(r['enrollment']),
            'yield_rate_pct':    float(r['yield_rate_pct']),
            'competitor_programs': int(r['competitor_programs']),
            'tuition':           float(r['tuition']),
            'competitor_avg_tuition': float(r['competitor_avg_tuition']),
            'price_position':    _price_position(r['tuition'], r['competitor_avg_tuition']),
            'factors': [
                {'factor': k, 'weight': w,
                 'normalised': round(float(components[k].loc[r.name]), 3),
                 'contribution': round(float(components[k].loc[r.name]) * w * 100, 1)}
                for k, w in _EXPANSION_WEIGHTS.items()
            ],
        })

    return {
        'institution': institution,
        'programs':    out,
        'weights':     _EXPANSION_WEIGHTS,
        'thresholds':  {'expand': _EXPAND_THRESHOLD, 'consolidate': _CONSOLIDATE_THRESHOLD},
        'method': (
            "Each factor is min-max normalised across this institution's own "
            "programmes, then combined with the published weights. Scores rank "
            "programmes against each other, not against an absolute standard."
        ),
        'dataset_label': ds.DATASET_LABEL,
    }


def _rationale(rec: str, r) -> str:
    if rec == 'Expand':
        return (f"National demand for {r['field']} is growing {r['demand_growth_pct']:.1f}%/yr "
                f"and only {int(r['competitor_programs'])} competitor programmes serve it.")
    if rec == 'Consolidate':
        return (f"Own enrolment is trending {r['own_growth_pct']:.1f}%/yr against "
                f"{int(r['competitor_programs'])} competing programmes — review viability.")
    return (f"Demand growth {r['demand_growth_pct']:.1f}%/yr with a "
            f"{r['yield_rate_pct']:.0f}% yield — maintain current capacity.")


def _price_position(tuition: float, competitor: float) -> str:
    if competitor <= 0:
        return 'unknown'
    delta = (tuition - competitor) / competitor * 100
    if delta > 10:
        return 'premium'
    if delta < -10:
        return 'discount'
    return 'parity'


# ── Resource efficiency ───────────────────────────────────────────────────────

@ttl_cache
def get_resource_efficiency(institution: str) -> dict:
    """The recruitment funnel and what each stage costs.

        marketing spend -> inquiries -> applications -> enrolments
    """
    sub = _scoped(institution)

    spend    = float(sub['marketing_spend_usd'].sum())
    inquiry  = float(sub['inquiry_count'].sum())
    apps     = float(sub['applications_count'].sum())
    enrolled = float(sub['enrollment_count'].sum())

    programs = []
    for name, g in sub.groupby('program_name'):
        s, i = float(g['marketing_spend_usd'].sum()), float(g['inquiry_count'].sum())
        a, en = float(g['applications_count'].sum()), float(g['enrollment_count'].sum())
        programs.append({
            'program':              name,
            'marketing_spend':      int(s),
            'inquiries':            int(i),
            'applications':         int(a),
            'enrollment':           int(en),
            'cost_per_inquiry':     round(s / i, 2) if i else 0.0,
            'cost_per_enrollment':  round(s / en, 2) if en else 0.0,
            'inquiry_to_app_pct':   round(a / i * 100, 1) if i else 0.0,
            'app_to_enroll_pct':    round(en / a * 100, 1) if a else 0.0,
        })

    # Most efficient = lowest cost per enrolment among programmes that enrolled anyone.
    ranked = sorted([p for p in programs if p['enrollment'] > 0],
                    key=lambda p: p['cost_per_enrollment'])

    return {
        'institution': institution,
        'funnel': [
            {'stage': 'Inquiries',    'count': int(inquiry)},
            {'stage': 'Applications', 'count': int(apps)},
            {'stage': 'Enrolments',   'count': int(enrolled)},
        ],
        'total_marketing_spend':    int(spend),
        'cost_per_enrollment':      round(spend / enrolled, 2) if enrolled else 0.0,
        'inquiry_to_app_pct':       round(apps / inquiry * 100, 1) if inquiry else 0.0,
        'app_to_enroll_pct':        round(enrolled / apps * 100, 1) if apps else 0.0,
        'programs':                 sorted(programs, key=lambda p: p['cost_per_enrollment']),
        'most_efficient_program':   ranked[0]['program'] if ranked else None,
        'least_efficient_program':  ranked[-1]['program'] if ranked else None,
        'dataset_label': ds.DATASET_LABEL,
    }


# ── Peer benchmark ────────────────────────────────────────────────────────────

@ttl_cache
def get_peer_benchmark(institution: str) -> dict:
    """Compare against the other institutions, anonymised.

    Peers are labelled "Peer A", "Peer B", ... in a stable alphabetical order.
    Names are never returned, so a university can see where it stands without
    seeing a named competitor's internals.
    """
    e = ds.enrollment()
    if institution not in set(e['institution_name']):
        raise ValueError(f"Unknown institution '{institution}'")

    def _metrics(g: pd.DataFrame) -> dict:
        enrolled = float(g['enrollment_count'].sum())
        spend    = float(g['marketing_spend_usd'].sum())
        return {
            'enrollment':          int(enrolled),
            'applications':        int(g['applications_count'].sum()),
            'acceptance_rate_pct': round(float(g['acceptance_rate_pct'].mean()), 1),
            'yield_rate_pct':      round(float(g['yield_rate_pct'].mean()), 1),
            'avg_tuition':         round(float(g['tuition_usd'].mean()), 2),
            'avg_net_price':       round(float(g['net_price'].mean()), 2),
            'employment_rate_pct': round(float(g['employment_rate_6mo_pct'].mean()), 1),
            'roi_10yr':            round(float(g['roi_10yr_usd'].mean()), 2),
            'cost_per_enrollment': round(spend / enrolled, 2) if enrolled else 0.0,
        }

    me = _metrics(e[e['institution_name'] == institution])

    peers = []
    others = sorted(n for n in e['institution_name'].unique() if n != institution)
    for i, name in enumerate(others):
        peers.append({'label': f"Peer {chr(65 + i)}", **_metrics(e[e['institution_name'] == name])})

    # Percentile rank against peers. "Better" is not self-evident for every
    # metric — a high acceptance rate means less selectivity, and high tuition
    # is revenue to the institution but cost to the student. So the direction
    # used for each metric is declared here and returned to the caller, rather
    # than left implicit in the number.
    direction = {
        'enrollment':          'higher',
        'applications':        'higher',
        'acceptance_rate_pct': 'lower',   # lower = more selective
        'yield_rate_pct':      'higher',  # more admitted students choose us
        'avg_tuition':         'neutral',  # revenue vs affordability — not ranked
        'avg_net_price':       'lower',   # lower = more affordable to students
        'employment_rate_pct': 'higher',
        'roi_10yr':            'higher',
        'cost_per_enrollment': 'lower',   # lower = more efficient recruitment
    }

    standing = {}
    for metric, mine in me.items():
        d = direction.get(metric, 'higher')
        if d == 'neutral':
            continue
        peer_vals = [p[metric] for p in peers]
        if not peer_vals:
            continue
        beaten = sum(1 for v in peer_vals if (mine < v if d == 'lower' else mine > v))
        standing[metric] = round(beaten / len(peer_vals) * 100)

    return {
        'institution':   institution,
        'me':            me,
        'peers':         peers,
        'percentile':    standing,
        'direction':     direction,
        'peer_count':    len(peers),
        'note': (
            "Peer institutions are anonymised; ordering is stable but not disclosed. "
            "Percentile is the share of peers this institution beats, scored in the "
            "direction given by `direction`. Tuition is reported but not ranked — "
            "higher is revenue to the institution and cost to the student."
        ),
        'dataset_label': ds.DATASET_LABEL,
    }
