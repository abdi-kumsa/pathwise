"""
Loader for the executable specification in docs/spec/.

Both feedback documents are transcribed into YAML there — 20 attribute
categories with every named variable, DOC1's 7-step methodology, DOC2's 44
widgets, and the per-dashboard access scopes. That transcription is the contract
for this whole piece of work, so it needs one reader rather than three.

Three consumers:

    tests/test_spec_coverage.py   asserts every id is claimed by real code
    scripts/spec_report.py        prints the coverage burn-down
    backend/routers/methodology.py  serves the priority tiers and the
                                    collection-priority panel of W.ADM.04

── The one rule this module enforces in its API shape ────────────────────────

DOC1 line 234 says the percentages are priorities for *data collection*, not
weights to impose on a learner. So the accessor is named
`collection_priority()` and there is deliberately no `weight()` or `weights()`
function to reach for. If fixed pre-training weights are ever needed, DOC1 step
7 routes that through ml/ahp/ instead — a separate methodology, never these
numbers.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Iterator

import yaml

def _spec_dir() -> Path:
    """Resolve docs/spec in both the repo layout and the Docker mount."""
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / "docs" / "spec",  # repo: backend/spec_registry.py
        Path("/docs/spec"),                    # docker: ./docs mounted at /docs
        here.parent / "docs" / "spec",
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


SPEC_DIR = _spec_dir()

# The five spec files, keyed by the short name used throughout the tests.
_FILES = {
    'model1':      'model1_attributes.yaml',
    'model2':      'model2_attributes.yaml',
    'methodology': 'methodology.yaml',
    'widgets':     'widgets.yaml',
    'scopes':      'scopes.yaml',
}


class SpecError(RuntimeError):
    """Raised when the registry itself is malformed — a missing file, a
    duplicate id, a priority table that does not sum to 100. Distinct from a
    coverage failure, which means the spec is fine but the code has not caught
    up with it yet."""


@functools.lru_cache(maxsize=None)
def load(name: str) -> dict:
    """Parse one spec file. Cached — these are read many times per test run."""
    try:
        filename = _FILES[name]
    except KeyError:
        raise SpecError(f"unknown spec {name!r}; expected one of {sorted(_FILES)}")

    path = SPEC_DIR / filename
    if not path.exists():
        raise SpecError(f"spec file missing: {path}")

    with path.open(encoding='utf-8') as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise SpecError(f"{filename} did not parse to a mapping")
    return data


def load_all() -> dict[str, dict]:
    """Every spec file, keyed by short name."""
    return {name: load(name) for name in _FILES}


def waivers() -> list[dict]:
    """Wave 8 product caveats. Not DOC1/DOC2 ids — must not excuse a missing widget."""
    path = SPEC_DIR / "waivers.yaml"
    if not path.exists():
        raise SpecError(f"spec file missing: {path}")
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict) or not isinstance(data.get("waivers"), list):
        raise SpecError("waivers.yaml must contain a waivers list")
    return data["waivers"]


# ── Attributes (DOC1) ─────────────────────────────────────────────────────────

def models() -> list[str]:
    """The two model spec names, in document order."""
    return ['model1', 'model2']


def categories(model: str) -> list[dict]:
    """The 10 attribute categories of one model, in document order."""
    return load(model)['categories']


def variables(model: str) -> Iterator[dict]:
    """Every named variable of one model, with its parent category attached.

    Each yielded dict carries the variable's own fields plus `category_id` and
    `source_table`, so a caller checking "does this column exist" knows which
    table to look in without walking back up the tree.
    """
    for cat in categories(model):
        for var in cat.get('variables', []):
            yield {
                **var,
                'category_id':   cat['id'],
                'category_name': cat['name'],
                'source_table':  cat.get('source_table'),
            }


def all_variables() -> Iterator[dict]:
    """Every named variable across both models, with `model` attached."""
    for model in models():
        for var in variables(model):
            yield {**var, 'model': load(model)['model']['id']}


def columns_for(var: dict) -> list[str]:
    """The column names one variable requires.

    A variable normally maps to a single column, but several map to a set — a
    score distribution needs mean, sd and quartiles; a lag needs lag-1 and
    lag-2. Those extras live under `also`, and all of them must be present for
    the variable to count as satisfied.
    """
    cols = [var['column']] if var.get('column') else []
    return cols + list(var.get('also') or [])


def collection_priority(category_id: str) -> int:
    """The DOC1 data-collection priority of one category, as a percentage.

    Deliberately NOT named `weight`. See the module docstring — these numbers
    must never reach a learner's loss function or reweight a training sample.
    """
    for model in models():
        for cat in categories(model):
            if cat['id'] == category_id:
                return cat['collection_priority']
    raise SpecError(f"no such category: {category_id}")


def priority_tiers(model: str) -> list[dict]:
    """The 3-tier summary from the end of DOC1 (M1 70/18/12, M2 55/30/15)."""
    return load(model)['priority_tiers']


def source_tables() -> dict[str, list[str]]:
    """source_table -> the category ids that feed from it.

    Drives the generator in Wave 1 and the pipeline monitor in W.ADM.02: one
    table per category, so every attribute has an owner.
    """
    out: dict[str, list[str]] = {}
    for model in models():
        for cat in categories(model):
            table = cat.get('source_table')
            if table:
                out.setdefault(table, []).append(cat['id'])
    return out


# ── Methodology (DOC1) ────────────────────────────────────────────────────────

def procedure() -> list[dict]:
    """DOC1's 7 recommended-procedure steps, in order."""
    return load('methodology')['procedure']


def ranking_constraints() -> list[dict]:
    """The honesty rules that bind how DOC2's "ranked" widgets may be built —
    most importantly RANK.R1, that fit classification enters no ranking."""
    return load('methodology')['ranking_constraints']


# ── Widgets and scopes (DOC2) ─────────────────────────────────────────────────

def dashboards() -> list[dict]:
    """DOC2's five dashboards, in document order."""
    return load('widgets')['dashboards']


def widgets() -> Iterator[dict]:
    """All 44 widgets, each with `dashboard_id` and `role` attached."""
    for dash in dashboards():
        for w in dash['widgets']:
            yield {**w, 'dashboard_id': dash['id'], 'role': dash['role']}


def widget(widget_id: str) -> dict:
    for w in widgets():
        if w['id'] == widget_id:
            return w
    raise SpecError(f"no such widget: {widget_id}")


def widgets_for_role(role: str) -> list[dict]:
    return [w for w in widgets() if w['role'] == role]


def architecture() -> dict:
    """DOC2's three-model architecture plus the mandatory constraint layer."""
    return load('widgets')['architecture']


def scopes() -> list[dict]:
    """Per-dashboard audience and data-scope rules from DOC2's section heads."""
    return load('scopes')['dashboards']


def scope_for_role(role: str) -> dict:
    for s in scopes():
        if s['role'] == role:
            return s
    raise SpecError(f"no scope declared for role: {role}")


# ── Ids and integrity ─────────────────────────────────────────────────────────

def all_ids() -> list[str]:
    """Every id in the registry, in a stable order.

    This is the full surface both documents define. `scripts/spec_report.py`
    counts against it, and it is what "nothing in the two documents may be
    missing" means concretely.
    """
    ids: list[str] = []
    for model in models():
        spec = load(model)
        for layer in spec['model'].get('architecture', {}).get('layers', []):
            ids.append(layer['id'])
        for cat in spec['categories']:
            ids.append(cat['id'])
            ids.extend(v['id'] for v in cat.get('variables', []))
        ids.extend(t['id'] for t in spec.get('priority_tiers', []))
        ids.extend(t['id'] for t in spec.get('targets', []))
        for req in (spec.get('forecasting') or {}).values():
            ids.append(req['id'])
        ids.extend(e['id'] for e in spec.get('ethiopia_rationale', []))

    ids.extend(s['id'] for s in procedure())
    ids.extend(r['id'] for r in ranking_constraints())

    arch = architecture()
    ids.extend(c['id'] for c in arch['components'])
    ids.append(arch['constraint_layer']['id'])
    ids.extend(w['id'] for w in widgets())

    for scope in scopes():
        ids.append(scope['id'])
        ids.extend(r['id'] for r in scope['rules'])
    ids.extend(r['id'] for r in load('scopes')['global_rules'])

    return ids


def duplicate_ids() -> list[str]:
    """Ids appearing more than once. Must be empty — ids are the contract, and
    a duplicate means two requirements are being tracked as one."""
    seen: set[str] = set()
    dupes: list[str] = []
    for i in all_ids():
        if i in seen:
            dupes.append(i)
        seen.add(i)
    return dupes


def summary() -> dict[str, Any]:
    """Counts for the report header."""
    return {
        'attributes':   sum(1 for _ in all_variables()),
        'categories':   sum(len(categories(m)) for m in models()),
        'widgets':      sum(1 for _ in widgets()),
        'dashboards':   len(dashboards()),
        'procedure':    len(procedure()),
        'source_tables': len(source_tables()),
        'total_ids':    len(all_ids()),
    }
