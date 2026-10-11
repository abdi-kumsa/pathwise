"""
Labour-market intelligence — the Ministry of Labour view.

Reads Ethiopia labour tables via services/_datasets.py. The headline signal for
MoL widgets is Model 2 (forecast, skills, pipelines). Leftover /api/labour/emerging
and mismatch routes are not Ethiopia Model 1/2 scores.
"""
import json

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

    employment_level = None
    unemployment_rate_pct = None
    labour_force_participation_pct = None
    underemployment = None
    vacancies = int(latest['job_openings_count'].sum())
    try:
        import sys
        from pathlib import Path
        _root = Path(__file__).resolve().parent.parent.parent
        if str(_root) not in sys.path:
            sys.path.insert(0, str(_root))
        from ml.features.model2 import c1_labour, c3_formal_informal, c4_vacancies
        hist = c1_labour.frame()
        if not hist.empty:
            hy = int(hist['year'].max())
            now = hist[hist['year'] == hy]
            if 'employment_level' in now.columns:
                employment_level = int(now['employment_level'].sum())
            if 'unemployment_rate_pct' in now.columns:
                unemployment_rate_pct = round(float(now['unemployment_rate_pct'].mean()), 1)
            if 'labour_force_participation_pct' in now.columns:
                labour_force_participation_pct = round(float(now['labour_force_participation_pct'].mean()), 1)
        fi = c3_formal_informal.frame()
        if not fi.empty and 'underemployment' in fi.columns:
            fy = int(fi['year'].max())
            underemployment = int(fi[fi['year'] == fy]['underemployment'].sum())
        vac = c4_vacancies.frame()
        if not vac.empty and 'vacancy_count' in vac.columns:
            vy = int(vac['year'].max())
            vacancies = int(vac[vac['year'] == vy]['vacancy_count'].sum())
    except Exception:
        pass

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
        'employment_level':      employment_level,
        'unemployment_rate_pct': unemployment_rate_pct,
        'underemployment':       underemployment,
        'vacancies':             vacancies,
        'labour_force_participation_pct': labour_force_participation_pct,
        'field_openings': [
            {'field': str(k), 'openings': int(v)}
            for k, v in latest.groupby('job_family')['job_openings_count'].sum()
            .sort_values(ascending=False).items()
        ],
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


def _ml_root() -> None:
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


def graduate_absorption() -> dict:
    """National aggregate time-to-employment and employment type (W.MOL.07)."""
    _ml_root()
    from ml.features.model1 import c7_outcomes
    from ml.features.model2 import c3_formal_informal

    out = c7_outcomes.frame()
    e = ds.enrollment()
    fi = c3_formal_informal.frame()
    years = sorted(set(int(y) for y in e['year'].unique()))
    series = []
    for year in years:
        oy = out[out['year'] == year] if not out.empty and 'year' in out.columns else out.iloc[0:0]
        ey = e[e['year'] == year]
        fiy = fi[fi['year'] == year] if not fi.empty and 'year' in fi.columns else fi.iloc[0:0]
        shares = {}
        if not fiy.empty:
            counts = {
                'formal': float(fiy['formal_wage_employment'].sum()) if 'formal_wage_employment' in fiy.columns else 0,
                'informal': float(fiy['informal_employment'].sum()) if 'informal_employment' in fiy.columns else 0,
                'self_employment': float(fiy['self_employment'].sum()) if 'self_employment' in fiy.columns else 0,
                'underemployment': float(fiy['underemployment'].sum()) if 'underemployment' in fiy.columns else 0,
            }
            total = sum(counts.values()) or 1.0
            shares = {k: round(v / total, 4) for k, v in counts.items()}
        series.append({
            'year': year,
            'employment_rate_pct': (
                round(float(oy['graduate_employment_rate_pct'].mean()), 1)
                if not oy.empty and 'graduate_employment_rate_pct' in oy.columns else None
            ),
            'unemployment_rate_pct': (
                round(float(oy['graduate_unemployment_rate_pct'].mean()), 1)
                if not oy.empty and 'graduate_unemployment_rate_pct' in oy.columns else None
            ),
            'employed_within_6mo_pct': (
                round(float(ey['employment_rate_6mo_pct'].mean()), 1)
                if not ey.empty and 'employment_rate_6mo_pct' in ey.columns else None
            ),
            'share_formal': shares.get('formal'),
            'share_informal': shares.get('informal'),
            'share_self_employment': shares.get('self_employment'),
            'share_underemployment': shares.get('underemployment'),
        })
    return {
        'grain': 'national_aggregate',
        'fit_classification_used': False,
        'n': len(series),
        'series': series,
        'note': (
            'Aggregate graduate outcomes and labour-force employment type. '
            'Not fit classification. Not an institution-level table (SCOPE.MOL.R2).'
        ),
    }


def workforce_report(horizon: int = 3) -> dict:
    """Planning report with sector / occupation / skill / region breakdowns (W.MOL.09)."""
    _ml_root()
    from services import model2_service as m2
    from services._provenance import default_provenance

    payload = {
        'official_forecast': False,
        'horizon': horizon,
        'as_of': None,
        'breakdowns': {
            'sector': m2.as_records(m2.labour_forecast(horizon=horizon, dimensions=['sector', 'period'])),
            'occupation': m2.as_records(m2.labour_forecast(horizon=horizon, dimensions=['occupation', 'period'])),
            'skill': m2.as_records(m2.skills(horizon=horizon)),
            'region': m2.as_records(m2.labour_forecast(horizon=horizon, dimensions=['region', 'period'])),
        },
        'note': (
            'Simulated workforce planning breakdowns. Not an official MoLS circular. '
            'official_forecast is false.'
        ),
        'provenance': default_provenance().to_dict(),
    }
    periods = []
    for rows in payload['breakdowns'].values():
        for row in rows or []:
            p = row.get('period') or row.get('year')
            if p is not None:
                periods.append(int(p))
    payload['as_of'] = max(periods) if periods else None
    return payload


def render_workforce_report(payload: dict, fmt: str) -> tuple[bytes, str, str]:
    """Return (body, media_type, filename) for csv / xlsx / pdf."""
    from services._provenance import default_provenance

    fmt = (fmt or 'csv').lower()
    prov = payload.get('provenance') or default_provenance().to_dict()
    breakdowns = payload.get('breakdowns') or {}
    if fmt == 'csv':
        return _report_csv(payload, prov, breakdowns), 'text/csv; charset=utf-8', 'workforce-report.csv'
    if fmt == 'xlsx':
        return _report_xlsx(payload, prov, breakdowns), (
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ), 'workforce-report.xlsx'
    if fmt == 'pdf':
        return _report_pdf(payload, prov, breakdowns), 'application/pdf', 'workforce-report.pdf'
    raise ValueError(f'Unsupported format {fmt!r}. Use csv, xlsx or pdf.')


def _flatten_rows(kind: str, rows: list) -> list[dict]:
    out = []
    for row in rows or []:
        flat = {'breakdown': kind}
        for k, v in row.items():
            if isinstance(v, bool) or v is None:
                flat[k] = v
            elif isinstance(v, (int, float, str)):
                flat[k] = v
            else:
                continue
        out.append(flat)
    return out


def _report_csv(payload: dict, prov: dict, breakdowns: dict) -> bytes:
    import csv
    from io import StringIO

    buf = StringIO()
    buf.write(f"# provenance: {json.dumps(prov, ensure_ascii=False)}\n")
    buf.write(f"# official_forecast: {payload.get('official_forecast', False)}\n")
    buf.write(f"# note: {payload.get('note', '')}\n")
    rows = []
    for kind, data in breakdowns.items():
        rows.extend(_flatten_rows(kind, data))
    if not rows:
        buf.write('breakdown\n')
        return buf.getvalue().encode('utf-8')
    fields = []
    for row in rows:
        for k in row:
            if k not in fields:
                fields.append(k)
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode('utf-8')


def _report_xlsx(payload: dict, prov: dict, breakdowns: dict) -> bytes:
    from io import BytesIO
    from openpyxl import Workbook

    wb = Workbook()
    stamp = wb.active
    stamp.title = 'Provenance'
    stamp.append(['key', 'value'])
    for k, v in prov.items():
        stamp.append([k, str(v)])
    stamp.append(['official_forecast', str(payload.get('official_forecast', False))])
    stamp.append(['note', payload.get('note') or ''])
    for kind, data in breakdowns.items():
        ws = wb.create_sheet(kind[:31])
        rows = _flatten_rows(kind, data)
        if not rows:
            ws.append(['empty'])
            continue
        headers = []
        for row in rows:
            for k in row:
                if k not in headers:
                    headers.append(k)
        ws.append(headers)
        for row in rows:
            ws.append([row.get(h) for h in headers])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _report_pdf(payload: dict, prov: dict, breakdowns: dict) -> bytes:
    from fpdf import FPDF

    def _txt(value) -> str:
        raw = str(value).replace("\u2013", "-").replace("\u2014", "-")
        return raw.encode("latin-1", "replace").decode("latin-1")

    def _line(pdf: FPDF, text: str, h: float = 5) -> None:
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, h, _txt(text))

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    _line(pdf, "PathWise workforce planning report", 8)
    pdf.set_font("Helvetica", "", 9)
    _line(pdf, "Simulated Ethiopian structure. Not official MoLS statistics.")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    _line(pdf, "Provenance", 6)
    pdf.set_font("Helvetica", "", 9)
    for k, v in prov.items():
        _line(pdf, f"{k}: {v}")
    _line(pdf, f"official_forecast: {payload.get('official_forecast', False)}")
    pdf.ln(2)
    _line(pdf, payload.get("note") or "")
    for kind, data in breakdowns.items():
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 12)
        _line(pdf, kind, 7)
        pdf.set_font("Helvetica", "", 8)
        rows = _flatten_rows(kind, data)[:25]
        _line(pdf, f"{len(data or [])} rows (showing {len(rows)})")
        for row in rows:
            parts = []
            for k, v in list(row.items())[:5]:
                if k == "breakdown":
                    continue
                parts.append(f"{k}={v}")
            _line(pdf, " ; ".join(parts) or "-", 4)
    return bytes(pdf.output())
