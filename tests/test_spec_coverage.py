"""
Coverage gate for the two feedback documents.

The governing rule for this piece of work is that nothing in the client's
two feedback documents may be missing. A checklist cannot enforce that, so both
documents are transcribed into docs/spec/ and this suite walks every id in the
registry and asserts a real artefact claims it.

    pytest tests/test_spec_coverage.py -v            # everything
    pytest tests/test_spec_coverage.py -m integrity  # registry itself only
    python scripts/spec_report.py                    # the burn-down table

── Expect this suite to be red for most of the build ─────────────────────────

That is its job. The `integrity` and `honesty` tests pass from day one — they
check the registry is well formed and that the constraints we agreed with the
client hold. The `coverage` tests go green wave by wave as Waves 1-7 land, and
Phase 8.1 is "all of these pass". A red coverage test is a to-do, not a
regression; a red integrity or honesty test is a real failure.

Coverage tests are therefore reported as failures with a full list of what is
still unclaimed, rather than skipping — a skipped test is invisible in CI and
would let a missing requirement ship.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from backend import spec_registry as S

ROOT = Path(__file__).resolve().parent.parent

# Wave 1 builds these; until then the attribute-coverage tests report what is
# missing rather than erroring on a missing directory.
ETHIOPIA_DIR = ROOT / 'data' / 'ethiopia'

# Set STRICT_COVERAGE=0 to downgrade coverage failures to reported warnings
# while a wave is in progress. Phase 8.1 runs with it unset (i.e. strict).
STRICT = os.getenv('STRICT_COVERAGE', '1') != '0'


def _report(label: str, missing: list[str], total: int) -> None:
    """Fail with a complete list of what is unclaimed, not just the first item.

    Seeing all 40 missing columns at once is what makes this suite usable as a
    work queue; failing on the first one would mean 40 runs to learn the same
    thing.
    """
    if not missing:
        return
    done = total - len(missing)
    lines = '\n'.join(f'  - {m}' for m in missing)
    msg = (
        f'{label}: {done}/{total} claimed, {len(missing)} outstanding\n{lines}'
    )
    if STRICT:
        pytest.fail(msg, pytrace=False)
    else:
        pytest.skip(f'[STRICT_COVERAGE=0] {msg}')


# ══════════════════════════════════════════════════════════════════════════════
# Integrity — the registry itself. Green from day one.
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integrity
def test_all_spec_files_parse():
    specs = S.load_all()
    assert set(specs) == {'model1', 'model2', 'methodology', 'widgets', 'scopes'}


@pytest.mark.integrity
def test_waivers_are_caveats_not_coverage_holes():
    """Wave 8: residual honesty limits are written down. They must not claim a
    widget, component or endpoint is missing — coverage stays 259/259."""
    items = S.waivers()
    assert items, 'waivers.yaml is empty'
    ids = [w['id'] for w in items]
    assert ids == list(dict.fromkeys(ids)), f'duplicate waiver ids: {ids}'
    widget_ids = {w['id'] for w in S.widgets()}
    widget_endpoints = {w['satisfied_by']['endpoint'] for w in S.widgets()}
    widget_components = {w['satisfied_by']['component'] for w in S.widgets()}
    for w in items:
        assert re.match(r'^WV\.[A-Z0-9]+$', w['id']), w['id']
        assert w.get('caveat') and w.get('retires_when'), w['id']
        assert w.get('does_not_excuse') == 'widgets', w['id']
        for field in ('missing_widget', 'missing_endpoint', 'missing_component'):
            assert not w.get(field), f'{w["id"]} claims {field}'
        for claimed in w.get('missing_ids') or []:
            assert claimed not in widget_ids
            assert claimed not in widget_endpoints
            assert claimed not in widget_components


@pytest.mark.integrity
def test_no_duplicate_ids():
    """Ids are the contract. A duplicate means two distinct requirements are
    being tracked as one, so one of them can silently go missing."""
    assert S.duplicate_ids() == [], f'duplicate spec ids: {S.duplicate_ids()}'


@pytest.mark.integrity
def test_id_format():
    """Ids must be machine-readable, since other spec files cross-reference
    them (`answered_by`, `spec_ref`, `ranking_constraint_ref`)."""
    pattern = re.compile(r'^[A-Z0-9]+(\.[A-Za-z0-9_]+)*$')
    bad = [i for i in S.all_ids() if not pattern.match(i)]
    assert bad == [], f'malformed ids: {bad}'


@pytest.mark.integrity
@pytest.mark.parametrize('model', ['model1', 'model2'])
def test_collection_priorities_sum_to_100(model):
    """DOC1 lines 73 and 189: Total feature-priority allocation: 100%."""
    spec = S.load(model)
    total = sum(c['collection_priority'] for c in spec['categories'])
    assert total == spec['total_collection_priority'] == 100


@pytest.mark.integrity
@pytest.mark.parametrize('model', ['model1', 'model2'])
def test_ten_categories_per_model(model):
    """DOC1 gives each model exactly ten attribute categories."""
    assert len(S.categories(model)) == 10


@pytest.mark.integrity
@pytest.mark.parametrize('model', ['model1', 'model2'])
def test_priority_tiers_sum_to_100_and_cover_every_category(model):
    """DOC1's closing table (M1 70/18/12, M2 55/30/15). Every category must
    appear in exactly one tier, or a tier view would silently drop it."""
    tiers = S.priority_tiers(model)
    assert sum(t['combined_priority'] for t in tiers) == 100

    grouped = [c for t in tiers for c in t['groups']]
    assert sorted(grouped) == sorted(c['id'] for c in S.categories(model))
    assert len(grouped) == len(set(grouped)), 'a category is in two tiers'

    # A tier's percentage must equal the sum of its members' priorities,
    # otherwise the two tables in DOC1 contradict each other.
    for tier in tiers:
        member_sum = sum(S.collection_priority(c) for c in tier['groups'])
        assert member_sum == tier['combined_priority'], (
            f"{tier['id']}: members sum to {member_sum}, "
            f"tier declares {tier['combined_priority']}"
        )


@pytest.mark.integrity
def test_widget_count_matches_document():
    """DOC2: 9 + 10 + 8 + 9 + 8 = 44."""
    expected = S.load('widgets')['expected_widget_counts']
    for dash in S.dashboards():
        assert len(dash['widgets']) == expected[dash['id']], dash['id']
    assert sum(1 for _ in S.widgets()) == expected['total'] == 44


@pytest.mark.integrity
def test_every_widget_carries_all_five_document_columns():
    """DOC2 specified content, visualization, source/model and purpose for every
    row. The visualization type and the purpose are requirements — a gap chart
    delivered as a table has not satisfied its row — so none may be dropped."""
    required = ['widget', 'content', 'visualization', 'source_model', 'purpose']
    for w in S.widgets():
        for field in required:
            assert w.get(field), f"{w['id']} missing {field}"


@pytest.mark.integrity
def test_every_widget_declares_an_endpoint_and_component():
    for w in S.widgets():
        sat = w.get('satisfied_by') or {}
        assert sat.get('endpoint'), f"{w['id']} declares no endpoint"
        assert sat.get('component'), f"{w['id']} declares no component"


@pytest.mark.integrity
def test_every_dashboard_role_has_a_declared_scope():
    """DOC2 heads each dashboard with an audience and a scope. Scope is
    access control, so a dashboard without one is unenforceable."""
    scoped = {s['role'] for s in S.scopes()}
    for dash in S.dashboards():
        assert dash['role'] in scoped, f"{dash['id']} has no scope"
        assert S.scope_for_role(dash['role'])['scope_text']


@pytest.mark.integrity
def test_roles_match_the_deployed_role_model():
    """DOC2's five audiences must map onto the roles that already exist, or the
    RBAC in auth_service cannot enforce the scopes.

    Read from source rather than importing auth_service — that module pulls in
    jose/passlib, which the spec suite does not require.
    """
    src = (ROOT / 'backend' / 'services' / 'auth_service.py').read_text(encoding='utf-8')
    declared = set(re.findall(r'^ROLE_[A-Z]+\s+=\s+["\']([A-Z]+)["\']', src, re.M))
    assert {d['role'] for d in S.dashboards()} == declared
    for role in declared:
        assert f'ROLE_{role}' in src and 'ROLE_HOME' in src


@pytest.mark.integrity
def test_seven_procedure_steps_numbered_in_order():
    steps = S.procedure()
    assert [s['step'] for s in steps] == list(range(1, 8))
    for s in steps:
        assert s['text'] and (s.get('satisfied_by') or {}), s['id']


@pytest.mark.integrity
def test_cross_references_resolve():
    """`answered_by`, `spec_ref` and `ranking_constraint_ref` must point at real
    ids — a dangling reference is a requirement that looks handled."""
    known = set(S.all_ids())
    dangling: list[str] = []

    def check(owner: str, refs) -> None:
        if refs is None:
            return
        for r in ([refs] if isinstance(refs, str) else refs):
            if r not in known:
                dangling.append(f'{owner} -> {r}')

    for model in S.models():
        for e in S.load(model).get('ethiopia_rationale', []):
            check(e['id'], e.get('answered_by'))
    for w in S.widgets():
        check(w['id'], w.get('spec_ref'))
        check(w['id'], w.get('ranking_constraint_ref'))
    for c in S.ranking_constraints():
        applies = c.get('applies_to')
        if isinstance(applies, list):
            check(c['id'], applies)
    for dash in S.dashboards():
        check(dash['id'], dash.get('scope_ref'))

    assert dangling == [], f'dangling references: {dangling}'


@pytest.mark.integrity
def test_every_category_has_a_source_table():
    """One table per category, so each attribute has exactly one owner and
    W.ADM.02's "all feeds" list is well defined."""
    for model in S.models():
        for cat in S.categories(model):
            assert cat.get('source_table'), f"{cat['id']} has no source_table"
    assert len(S.source_tables()) == 20


# ══════════════════════════════════════════════════════════════════════════════
# Honesty — the constraints agreed with the client. Green from day one.
# ══════════════════════════════════════════════════════════════════════════════

def _python_sources() -> list[Path]:
    out: list[Path] = []
    for sub in ('backend', 'ml', 'data', 'scripts'):
        d = ROOT / sub
        if d.exists():
            out += [p for p in d.rglob('*.py') if '__pycache__' not in p.parts]
    return out


@pytest.mark.honesty
def test_collection_priority_never_used_as_a_model_weight():
    """DOC1 line 234: the percentages are priorities for data collection, "not
    as fixed weights manually imposed on a machine-learning model".

    So no training or inference code may read `collection_priority` and feed it
    to a learner. Reading it to *display* is fine — that is what W.ADM.04's
    second panel does — hence backend/routers and the report script are allowed;
    ml/ is not.
    """
    offenders = []
    for path in _python_sources():
        rel = path.relative_to(ROOT).as_posix()
        if not rel.startswith('ml/'):
            continue
        if 'collection_priority' in path.read_text(encoding='utf-8'):
            offenders.append(rel)
    assert offenders == [], (
        'ml/ code reads collection_priority — DOC1 forbids using these '
        f'percentages as model weights: {offenders}. If fixed pre-training '
        'weights are genuinely required, DOC1 step 7 routes that through '
        'ml/ahp/ as a separate methodology.'
    )


@pytest.mark.honesty
def test_learned_and_priority_never_merged():
    """PROC.S6 and W.ADM.04: data-driven feature rankings are reported
    *separately* from the proposed collection priorities. The widget declares
    two panels and never_merged; assert the declaration stays intact."""
    w = S.widget('W.ADM.04')
    assert w['never_merged'] is True
    assert w['panels'] == ['learned_importance', 'collection_priority']
    assert 'Separates learned importance' in w['purpose']

    step6 = next(s for s in S.procedure() if s['id'] == 'PROC.S6')
    assert 'separately' in step6['text']
    assert step6['constraint']


@pytest.mark.honesty
def test_fit_classification_not_ranked():
    """RANK.R1. Fit classification is near-uniform across fields (~80/13/5,
    5.3pp spread) because the generator encoded no between-group signal, so
    ranking it charts noise. Every widget that ranks must cite the constraint,
    and none may list fit as a ranking factor."""
    r1 = next(c for c in S.ranking_constraints() if c['id'] == 'RANK.R1')
    assert 'must not enter any ranking' in r1['rule']

    for w in S.widgets():
        factors = w.get('ranking_factors')
        if not factors:
            continue
        assert 'RANK.R1' in (w.get('ranking_constraint_ref') or []), (
            f"{w['id']} ranks but does not cite RANK.R1"
        )
        bad = [f for f in factors if 'fit_class' in f or f == 'fit']
        assert bad == [], f"{w['id']} ranks on fit classification: {bad}"

    # Every widget R1 names must exist, so the constraint cannot drift off the
    # widgets it is meant to bind.
    for wid in r1['applies_to']:
        S.widget(wid)


@pytest.mark.honesty
def test_ahp_kept_separate_from_learning():
    """PROC.S7: add AHP "rather than inserting subjective percentages directly
    into the ML algorithm"."""
    s7 = S.procedure()[6]
    assert s7['id'] == 'PROC.S7'
    assert s7['consistency_ratio_max'] == 0.1
    assert 'never blended' in s7['constraint']
    assert set(s7['requirements']) == {
        'pairwise_comparison_matrix',
        'principal_eigenvector_weights',
        'consistency_ratio',
    }


@pytest.mark.honesty
def test_scope_rules_are_server_side_and_token_derived():
    """SCOPE.G1-G3. Hiding a nav link is presentation, not access control; and
    any identifier selecting rows a caller is entitled to comes from the signed
    token, never client input."""
    g = {r['id']: r for r in S.load('scopes')['global_rules']}
    assert 'never access control' in g['SCOPE.G1']['rule']
    assert 'signed token' in g['SCOPE.G2']['rule']
    assert '403' in g['SCOPE.G3']['rule']

    # The existing university guard is the precedent these rules generalise.
    uni = S.scope_for_role('UNIVERSITY')
    r1 = next(r for r in uni['rules'] if r['id'] == 'SCOPE.UNI.R1')
    assert 'NEVER from a query' in r1['implementation']


@pytest.mark.honesty
def test_constraint_layer_is_declared_mandatory():
    """DOC2 line 9 and DOC1 lines 75-77: enrollment is not purely
    demand-driven. Both documents require the policy/capacity layer, so it is
    not an optional enhancement."""
    cl = S.architecture()['constraint_layer']
    assert set(cl['inputs']) == {
        'entrance_examination_eligibility',
        'placement_allocation_rules',
        'approved_intake_quotas',
        'strategic_priority_fields',
        'institutional_capacity',
    }
    layers = S.load('model1')['model']['architecture']['layers']
    assert [l['id'] for l in layers] == ['M1.L1', 'M1.L2']


# ══════════════════════════════════════════════════════════════════════════════
# Coverage — red until the waves land. This is the burn-down.
# ══════════════════════════════════════════════════════════════════════════════

def _available_columns() -> set[str]:
    """Every column present across the built Ethiopia fact tables (Wave 1)."""
    if not ETHIOPIA_DIR.exists():
        return set()
    import pandas as pd
    cols: set[str] = set()
    for path in ETHIOPIA_DIR.rglob('*.parquet'):
        cols |= set(pd.read_parquet(path).columns)
    for path in ETHIOPIA_DIR.rglob('*.csv'):
        cols |= set(pd.read_csv(path, nrows=0).columns)
    return cols


@pytest.mark.coverage
@pytest.mark.parametrize('model', ['model1', 'model2'])
def test_every_named_attribute_has_a_column(model):
    """Wave 1 + Phases 2.1/3.1. Every variable DOC1 names must exist as a real
    column in the fact table its category owns."""
    have = _available_columns()
    missing = [
        f"{v['id']} {v['name']!r} -> {col} (table {v['source_table']})"
        for v in S.variables(model)
        for col in S.columns_for(v)
        if col not in have
    ]
    total = sum(len(S.columns_for(v)) for v in S.variables(model))
    _report(f'{model} attribute columns', missing, total)


@pytest.mark.coverage
def test_every_source_table_exists():
    """One file per category — 20 tables."""
    tables = S.source_tables()
    missing = [
        f'{t} (owns {", ".join(cats)})'
        for t, cats in sorted(tables.items())
        if not list(ETHIOPIA_DIR.rglob(f'{t}.parquet'))
        and not list(ETHIOPIA_DIR.rglob(f'{t}.csv'))
    ]
    _report('source tables', missing, len(tables))


@pytest.mark.coverage
def test_every_widget_component_exists():
    """Phases 5.1-7.1. The declared component file must be on disk."""
    missing = [
        f"{w['id']} {w['widget']!r} -> {w['satisfied_by']['component']}"
        for w in S.widgets()
        if not (ROOT / w['satisfied_by']['component']).exists()
    ]
    _report('widget components', missing, sum(1 for _ in S.widgets()))


@pytest.mark.coverage
def test_every_widget_component_is_routed():
    """A component that exists but is not in the route table is unreachable, so
    the widget is not delivered."""
    app_jsx = (ROOT / 'frontend' / 'src' / 'App.jsx').read_text(encoding='utf-8')
    missing = []
    for w in S.widgets():
        component = Path(w['satisfied_by']['component'])
        if not (ROOT / component).exists():
            continue                      # covered by the test above
        if component.stem not in app_jsx:
            missing.append(f"{w['id']} -> {component.stem} not in App.jsx")
    _report('widget routes', missing, sum(1 for _ in S.widgets()))


@pytest.mark.coverage
def test_every_widget_endpoint_is_declared_by_a_router():
    """Phases 2.4/3.5/5-7. Match each declared path against the routers, so a
    widget cannot be called done while its data source is absent.

    Static check by design: it reads the router sources rather than calling a
    live server, so it runs in CI with nothing deployed. The live 200/403
    behaviour is tests/test_scopes.py's job.
    """
    routers = ROOT / 'backend' / 'routers'
    sources = {p.name: p.read_text(encoding='utf-8') for p in routers.glob('*.py')}
    blob = '\n'.join(sources.values())

    missing = []
    for w in S.widgets():
        path = w['satisfied_by']['endpoint']
        # /api is added by main.py's include_router; a router declares the rest.
        tail = path[len('/api'):] if path.startswith('/api') else path
        # A path parameter may be named anything, so compare on the literal
        # prefix up to the first parameter.
        literal = tail.split('{')[0].rstrip('/')
        if literal and literal not in blob:
            missing.append(f"{w['id']} -> {path}")
    _report('widget endpoints', missing, sum(1 for _ in S.widgets()))


@pytest.mark.coverage
def test_every_procedure_step_has_its_artefact():
    """DOC1's 7 steps each name a deliverable — the expert-validation register,
    the model-comparison report, the SHAP report, the AHP module."""
    missing = []
    for step in S.procedure():
        sat = step['satisfied_by']
        for key in ('artefact', 'report', 'module', 'component'):
            target = sat.get(key)
            if target and not (ROOT / target).exists():
                missing.append(f"{step['id']} (step {step['step']}) -> {target}")
        for extra in (sat.get('also') or []):
            if not (ROOT / extra).exists():
                missing.append(f"{step['id']} -> {extra}")
    _report('procedure artefacts', missing, len(S.procedure()))


@pytest.mark.coverage
def test_architecture_components_exist():
    """The three models plus the constraint layer (DOC2 lines 5-9)."""
    missing = []
    for comp in S.architecture()['components']:
        sat = comp.get('satisfied_by') or {}
        for target in (sat.get('module'), sat.get('service'), comp.get('spec')):
            if target and not (ROOT / target).exists():
                missing.append(f"{comp['id']} -> {target}")
    cl = S.architecture()['constraint_layer']['satisfied_by']
    if not (ROOT / cl['service']).exists():
        missing.append(f"SYS.CL -> {cl['service']}")
    _report('architecture components', missing, 4)


@pytest.mark.coverage
def test_ingestion_contract_per_source_table():
    """Phase 1.3. Each table needs a documented contract so a real ministry
    file can replace the simulated one without touching service code."""
    contracts = ROOT / 'docs' / 'spec' / 'ingestion'
    missing = [
        f'{t}.md' for t in sorted(S.source_tables())
        if not (contracts / f'{t}.md').exists()
    ]
    _report('ingestion contracts', missing, len(S.source_tables()))
