#!/usr/bin/env python3
"""Write docs/DELIVERABLE_MEMO.md from the spec registry."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend import spec_registry as S  # noqa: E402


def _sat(obj: dict) -> str:
    sat = obj.get("satisfied_by") or {}
    parts = []
    for key in ("endpoint", "component", "file", "module", "service", "artefact", "report"):
        if sat.get(key):
            parts.append(f"{key}: `{sat[key]}`")
    for extra in sat.get("also") or []:
        parts.append(f"also: `{extra}`")
    if sat.get("also_endpoint"):
        parts.append(f"also: `{sat['also_endpoint']}`")
    return "; ".join(parts) if parts else "—"


def main() -> int:
    lines = [
        "# Deliverable memo",
        "",
        "Generated from `docs/spec/` via `scripts/deliverable_memo.py`.",
        "Coverage freeze: **259/259** (`python scripts/spec_report.py`).",
        "",
        "This is the per-document response: every DOC1 category and variable,",
        "every DOC2 widget, mapped to the artefact that discharges it.",
        "",
        "---",
        "",
        "## DOC1 — categories and variables",
        "",
        "| Id | Name | Model | Satisfied by |",
        "|---|---|---|---|",
    ]
    for cat in [*S.categories("model1"), *S.categories("model2")]:
        sat = cat.get("source_table")
        where = f"table: `data/ethiopia/{sat}.parquet`" if sat else _sat(cat)
        lines.append(f"| `{cat['id']}` | {cat.get('name', '')} | {cat['id'].split('.')[0]} | {where} |")
        for var in cat.get("variables") or []:
            cols = ", ".join(f"`{c}`" for c in S.columns_for(var)) or "—"
            lines.append(
                f"| `{var['id']}` | {var.get('name', '')} | {var['id'].split('.')[0]} | {cols or '—'} |"
            )

    lines += [
        "",
        "## DOC1 — procedure",
        "",
        "| Id | Step | Satisfied by |",
        "|---|---|---|",
    ]
    for step in S.procedure():
        text = " ".join(step["text"].split()).replace("|", "/")
        lines.append(f"| `{step['id']}` | {step['step']}. {text[:90]} | {_sat(step)} |")

    lines += [
        "",
        "## DOC2 — widgets (44)",
        "",
        "| Id | Widget | Role | Endpoint | Component |",
        "|---|---|---|---|---|",
    ]
    for w in S.widgets():
        sat = w["satisfied_by"]
        lines.append(
            f"| `{w['id']}` | {w.get('widget', w.get('name', ''))} | {w['role']} | "
            f"`{sat['endpoint']}` | `{sat['component']}` |"
        )

    lines += [
        "",
        "## Waivers (caveats, not missing widgets)",
        "",
        "| Id | Caveat | Retires when |",
        "|---|---|---|",
    ]
    for w in S.waivers():
        caveat = " ".join(w["caveat"].split())
        retire = " ".join(w["retires_when"].split())
        lines.append(f"| `{w['id']}` | {caveat} | {retire} |")

    lines += [
        "",
        "## What we did not do",
        "",
        "- Official CSA / MoE / ESS replacement files. Every Ethiopia figure stays `tier: simulated`.",
        "- Training with AHP or `collection_priority`. SHAP and AHP stay in separate panels.",
        "- Replacing `education_service.get_investment_priority` into W.MOE.05. The yaml ranker stays on its own route; the page uses policy-priority.",
        "- Deleting leftover US tool routes. Wave 9 hid them from role nav; artefacts stay on disk (WV.US1).",
        "- Dark mode.",
        "- Ensemble stacking rebuild.",
        "- Real 5 / 10 / 20 % admission-risk thresholds.",
        "- Tagging `v1.0.0` (not in this wave unless asked).",
        "- Recording the walkthrough video. The click script is [WALKTHROUGH.md](WALKTHROUGH.md).",
        "",
        "## Verification",
        "",
        "```text",
        "python scripts/spec_report.py",
        "pytest tests/test_spec_coverage.py -m \"integrity or honesty or coverage\"",
        "pytest tests/test_honesty_live.py tests/test_scopes.py tests/test_ahp.py tests/test_constraints.py",
        "cd frontend && npm test",
        "```",
        "",
        "No Playwright / browser MCP in this environment (same as Wave 7). Substitute:",
        "live API matrix in `tests/test_honesty_live.py` and `tests/test_scopes.py` plus",
        "Vitest. Record the five-role video from [WALKTHROUGH.md](WALKTHROUGH.md).",
        "",
    ]
    out = ROOT / "docs" / "DELIVERABLE_MEMO.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
