"""
Graduate-to-role fit classification — Matched / Overeducated / Undereducated.

A contracted deliverable, and squarely a Ministry of Labour concern: it measures
whether graduates end up in roles that match the credential they hold.

The vocabulary is the one already used elsewhere in the project — encoded in
ml/feature_engineering.py (Matched=2, Overeducated=1, Undereducated=0) and
constrained in db/schema.sql's placements table.

────────────────────────────────────────────────────────────────────────────────
IMPORTANT — read before charting any of this.

The distribution is close to identical in every field: roughly 80% Undereducated,
13% Matched, 5% Overeducated, varying by under 3 percentage points across all
nine fields and all twelve programmes. The mock generator that produced
data/mock/placements.csv did not encode any between-group signal.

So these numbers are meaningful as a SYSTEM-WIDE descriptive statistic and are
meaningless as a comparison between fields. Ranking fields against each other
here would be presenting sampling noise as a finding.

Every response therefore carries `comparable: False` and a `caveat` string, and
the UI renders the caveat next to the figures. For a mismatch signal that does
have real variance, use labour_market_service.get_supply_demand_gap().
────────────────────────────────────────────────────────────────────────────────
"""
from . import _datasets as ds
from ._cache import ttl_cache

# Ordered worst-to-best for consistent stacking in charts.
STATUSES = ['Undereducated', 'Overeducated', 'Matched']

_CAVEAT = (
    "Fit classification is uniform across fields in this dataset (within ~3 "
    "percentage points), so these figures describe the system as a whole and "
    "should not be read as a ranking between fields. For a mismatch signal with "
    "real variation, see the supply-demand gap."
)


@ttl_cache
def get_overview() -> dict:
    """System-wide fit distribution across all placed graduates."""
    p = ds.placements()
    placed = p[p['placed'] & p['placement_status'].notna()]
    total = int(len(placed))

    counts = placed['placement_status'].value_counts()
    breakdown = [
        {
            'status':  s,
            'count':   int(counts.get(s, 0)),
            'share_pct': round(float(counts.get(s, 0)) / total * 100, 1) if total else 0.0,
        }
        for s in STATUSES
    ]

    matched = int(counts.get('Matched', 0))

    return {
        'total_placed':      total,
        'total_unplaced':    int((~p['placed']).sum()),
        'breakdown':         breakdown,
        'match_rate_pct':    round(matched / total * 100, 1) if total else 0.0,
        'mismatch_rate_pct': round((total - matched) / total * 100, 1) if total else 0.0,
        'headline': (
            f"{round((total - matched) / total * 100)}% of placed graduates hold a role "
            f"that does not match their credential level."
        ) if total else "No placement outcomes recorded.",
        'comparable':    False,
        'caveat':        _CAVEAT,
        'dataset_label': 'Leftover US placement mock — not Ethiopia M1/M2',
        'provenance': {
            'source': 'data/mock/placements.csv',
            'tier': 'simulated',
            'as_of': 'US synthetic',
            'method': 'mock generator',
            'caveat': 'Leftover US placement mock. Not official statistics and not Ethiopia Model 1 or 2.',
        },
    }


@ttl_cache
def get_by_field() -> dict:
    """Fit distribution per field.

    Returned for completeness and for the contracted deliverable, but flagged
    non-comparable — see the module docstring. `spread_pct` reports the actual
    observed range in match rate so the caller can see for themselves how little
    separates the fields.
    """
    p = ds.placements()
    placed = p[p['placed'] & p['placement_status'].notna() & p['job_family'].notna()]

    rows = []
    for field in ds.FIELDS:
        sub = placed[placed['job_family'] == field]
        total = int(len(sub))
        if total == 0:
            continue
        counts = sub['placement_status'].value_counts()
        matched = int(counts.get('Matched', 0))
        rows.append({
            'field': field,
            'total': total,
            **{
                s.lower(): int(counts.get(s, 0)) for s in STATUSES
            },
            'match_rate_pct': round(matched / total * 100, 1),
        })

    rates = [r['match_rate_pct'] for r in rows]
    spread = round(max(rates) - min(rates), 1) if rates else 0.0

    return {
        'fields':      rows,
        'spread_pct':  spread,
        'comparable':  False,
        'caveat':      _CAVEAT,
        'dataset_label': 'Leftover US placement mock — not Ethiopia M1/M2',
        'provenance': {
            'source': 'data/mock/placements.csv',
            'tier': 'simulated',
            'as_of': 'US synthetic',
            'method': 'mock generator',
            'caveat': 'Leftover US placement mock. Not official statistics and not Ethiopia Model 1 or 2.',
        },
    }


@ttl_cache
def get_by_program() -> dict:
    """Fit distribution per programme, from the ML feature store.

    Uses `placement_status_encoded` in features.parquet rather than the CSV, so
    this stays consistent with what the models were trained on. Same
    non-comparability caveat applies.
    """
    decode = {2: 'Matched', 1: 'Overeducated', 0: 'Undereducated', -1: 'Not placed'}
    f = ds.features().copy()
    f['fit'] = f['placement_status_encoded'].map(decode)

    rows = []
    for program in ds.PROGRAMS:
        sub = f[(f['program'] == program) & (f['fit'] != 'Not placed')]
        total = int(len(sub))
        if total == 0:
            continue
        counts = sub['fit'].value_counts()
        matched = int(counts.get('Matched', 0))
        rows.append({
            'program': program,
            'total':   total,
            **{s.lower(): int(counts.get(s, 0)) for s in STATUSES},
            'match_rate_pct': round(matched / total * 100, 1),
        })

    rates = [r['match_rate_pct'] for r in rows]

    return {
        'programs':   rows,
        'spread_pct': round(max(rates) - min(rates), 1) if rates else 0.0,
        'comparable': False,
        'caveat':     _CAVEAT,
        'dataset_label': 'Leftover US placement mock — not Ethiopia M1/M2',
        'provenance': {
            'source': 'data/processed/features.parquet',
            'tier': 'simulated',
            'as_of': 'US synthetic',
            'method': 'mock feature store',
            'caveat': 'Leftover US placement mock. Not official statistics and not Ethiopia Model 1 or 2.',
        },
    }
