"""
Education-supply intelligence — the Ministry of Education view.

Reads Ethiopia fact tables via services/_datasets.py (enrollment_compat /
jobs_compat backed by data/ethiopia/). Model 3 policy-priority is the W.MOE.05
ranker. get_investment_priority() remains on its own route and is not the
widget page.
"""
from . import _datasets as ds
from . import labour_market_service as labour
from ._cache import ttl_cache


# ── Overview ──────────────────────────────────────────────────────────────────

@ttl_cache
def get_overview() -> dict:
    e = ds.enrollment()

    by_year = e.groupby('year')['enrollment_count'].sum()
    apps_by_year = e.groupby('year')['applications_count'].sum()
    growth = ds.cagr(
        float(by_year.loc[ds.YEAR_MIN]),
        float(by_year.loc[ds.YEAR_MAX]),
        ds.YEAR_MAX - ds.YEAR_MIN,
    )

    capacity_utilization_pct = None
    projected_intake = None
    try:
        from ml.features.model1 import c4_quota
        from services import constraint_service as m1
        q = c4_quota.frame()
        if not q.empty and "program_capacity" in q.columns:
            qy = int(q["year"].max())
            cap = float(q[q["year"] == qy]["program_capacity"].sum())
            latest_enr = float(by_year.loc[ds.YEAR_MAX])
            if cap > 0:
                capacity_utilization_pct = round(latest_enr / cap * 100, 1)
        cons = m1.constrained_demand(horizon=1)
        if not cons.empty and "constrained_enrollment" in cons.columns:
            year = int(cons["academic_year"].max())
            projected_intake = round(float(
                cons[cons["academic_year"] == year]["constrained_enrollment"].sum()
            ), 1)
    except Exception:
        capacity_utilization_pct = None
        projected_intake = None

    return {
        'total_enrollment':      int(e['enrollment_count'].sum()),
        'enrollment_latest_year': int(by_year.loc[ds.YEAR_MAX]),
        'enrollment_cagr_pct':   growth,
        # All years combined; shown beside a single year of enrolment it
        # overstated demand roughly tenfold. The page uses the latest year.
        'total_applications':    int(e['applications_count'].sum()),
        'applications_latest_year': int(apps_by_year.loc[ds.YEAR_MAX]),
        'institutions':          int(e['institution_name'].nunique()),
        'programs':              int(e['program_name'].nunique()),
        'fields':                int(e['field_of_study'].nunique()),
        'avg_employment_rate_pct': round(float(e['employment_rate_6mo_pct'].mean()), 1),
        'avg_tuition':           round(float(e['tuition_usd'].mean()), 2),
        'avg_net_price':         round(float(e['net_price'].mean()), 2),
        'avg_roi_10yr':          round(float(e['roi_10yr_usd'].mean()), 2),
        'stem_share_pct':        round(float(e['stem_designated'].mean()) * 100, 1),
        'capacity_utilization_pct': capacity_utilization_pct,
        'projected_intake':      projected_intake,
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


def _records(df):
    import json
    if df is None or getattr(df, "empty", True):
        return []
    return json.loads(df.to_json(orient="records"))


@ttl_cache
def demand_constrained_comparison(horizon: int = 3) -> dict:
    """National unconstrained vs constrained demand by field and year (W.MOE.02)."""
    from services import constraint_service as m1

    unconstrained = m1.unconstrained_demand(horizon=horizon, dimensions=["field", "academic_year"])
    constrained = m1.constrained_demand(horizon=horizon, dimensions=["field", "academic_year"])
    if unconstrained is None or unconstrained.empty:
        return {"horizon": horizon, "n": 0, "rows": []}
    left = unconstrained.rename(columns={"unconstrained_demand": "unconstrained"})
    keep_u = [c for c in ("field", "academic_year", "unconstrained") if c in left.columns]
    left = left[keep_u]
    if constrained is not None and not constrained.empty:
        keep_c = [c for c in (
            "field", "academic_year", "constrained_enrollment", "binding_constraint", "constraint_loss",
        ) if c in constrained.columns]
        merged = left.merge(constrained[keep_c], on=["field", "academic_year"], how="outer")
    else:
        merged = left
        merged["constrained_enrollment"] = 0
        merged["binding_constraint"] = "none"
        merged["constraint_loss"] = 0
    merged = merged.fillna({"unconstrained": 0, "constrained_enrollment": 0, "binding_constraint": "none", "constraint_loss": 0})
    return {
        "horizon": horizon,
        "grain": "national",
        "n": int(len(merged)),
        "rows": _records(merged),
    }


@ttl_cache
def institution_comparison(horizon: int = 1) -> dict:
    """All registered HEIs: capacity, forecast accuracy, outcomes, alignment (W.MOE.07)."""
    from ml.features.model1 import c4_quota, c7_outcomes
    from services import alignment_service as m3
    from services import constraint_service as m1

    e = ds.enrollment()
    latest_year = int(e["year"].max())
    enrol = e[e["year"] == latest_year].groupby("institution_name").agg(
        enrollment=("enrollment_count", "sum"),
        applications=("applications_count", "sum"),
        employment_rate_pct=("employment_rate_6mo_pct", "mean"),
        region=("institution_state", "first"),
    ).reset_index()

    quota = c4_quota.frame()
    cap_map = {}
    if not quota.empty and "institution" in quota.columns:
        qy = int(quota["year"].max())
        qnow = quota[quota["year"] == qy]
        cap_map = qnow.groupby("institution")["program_capacity"].sum().to_dict() if "program_capacity" in qnow.columns else {}

    cons = m1.constrained_demand(horizon=horizon)
    un_map, c_map, bind_map = {}, {}, {}
    if cons is not None and not cons.empty and "institution" in cons.columns:
        cy = int(cons["academic_year"].max())
        now = cons[cons["academic_year"] == cy]
        un_map = now.groupby("institution")["unconstrained_demand"].sum().to_dict()
        c_map = now.groupby("institution")["constrained_enrollment"].sum().to_dict()
        bind_map = (
            now.groupby("institution")["binding_constraint"]
            .agg(lambda s: s.value_counts().index[0] if len(s) else "none")
            .to_dict()
        )

    outcomes = c7_outcomes.frame()
    emp_map = {}
    if not outcomes.empty and "institution" in outcomes.columns:
        oy = int(outcomes["year"].max())
        onow = outcomes[outcomes["year"] == oy]
        if "graduate_employment_rate_pct" in onow.columns:
            emp_map = onow.groupby("institution")["graduate_employment_rate_pct"].mean().to_dict()

    region_status = {}
    try:
        regional = m3.regional_alignment(horizon=horizon)
        if regional is not None and not regional.empty and "region" in regional.columns:
            latest = int(regional["period"].max()) if "period" in regional.columns else None
            now = regional[regional["period"] == latest] if latest is not None else regional
            for region, slice_ in now.groupby("region"):
                statuses = [str(s) for s in slice_["status"].tolist()] if "status" in slice_.columns else []
                region_status[region] = max(set(statuses), key=statuses.count) if statuses else "balanced"
    except Exception:
        region_status = {}

    rows = []
    for _, r in enrol.iterrows():
        name = r["institution_name"]
        unconstrained = float(un_map.get(name, 0) or 0)
        constrained = float(c_map.get(name, 0) or 0)
        realised = float(r["enrollment"] or 0)
        capacity = float(cap_map.get(name, 0) or 0)
        accuracy = None
        if constrained:
            accuracy = round(1.0 - abs(constrained - realised) / max(constrained, 1.0), 3)
        alignment = region_status.get(r["region"], "balanced")
        rows.append({
            "institution": name,
            "region": r["region"],
            "enrollment": int(realised),
            "applications": int(r["applications"] or 0),
            "capacity": round(capacity, 1),
            "capacity_utilization_pct": round(realised / capacity * 100, 1) if capacity else None,
            "unconstrained_demand": round(unconstrained, 1),
            "constrained_enrollment": round(constrained, 1),
            "forecast_accuracy": accuracy,
            "binding_constraint": bind_map.get(name, "none"),
            "employment_rate_pct": round(float(emp_map.get(name, r["employment_rate_pct"] or 0)), 1),
            "alignment_status": alignment,
        })
    rows.sort(key=lambda x: x["enrollment"], reverse=True)
    return {"n": len(rows), "year": latest_year, "rows": rows}


def policy_impact() -> dict:
    """Simulated quota/capacity YoY versus subsequent enrolment and employment (W.MOE.08)."""
    from ml.features.model1 import c4_quota, c7_outcomes

    quota = c4_quota.frame()
    e = ds.enrollment()
    out = c7_outcomes.frame()
    years = sorted(int(y) for y in e["year"].unique())
    series = []
    for year in years:
        qy = quota[quota["year"] == year] if not quota.empty and "year" in quota.columns else quota.iloc[0:0]
        ey = e[e["year"] == year]
        oy = out[out["year"] == year] if not out.empty and "year" in out.columns else out.iloc[0:0]
        series.append({
            "year": year,
            "approved_intake_quota": float(qy["approved_intake_quota"].sum()) if "approved_intake_quota" in qy.columns and not qy.empty else 0,
            "program_capacity": float(qy["program_capacity"].sum()) if "program_capacity" in qy.columns and not qy.empty else 0,
            "enrollment": float(ey["enrollment_count"].sum()) if not ey.empty else 0,
            "employment_rate_pct": round(float(oy["graduate_employment_rate_pct"].mean()), 1) if not oy.empty and "graduate_employment_rate_pct" in oy.columns else None,
        })
    return {
        "official_forecast": False,
        "n": len(series),
        "series": series,
        "note": (
            "Simulated quota and capacity against subsequent enrolment and employment. "
            "Not a real MoE circular or an official impact evaluation."
        ),
    }
