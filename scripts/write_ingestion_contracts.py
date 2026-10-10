#!/usr/bin/env python3
"""Write one ingestion contract markdown file per DOC1 source table."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend import spec_registry as S

SOURCE = {
    "enrollment_history": ("MoE EMIS", "annual"),
    "admissions_funnel": ("MoE EMIS / HEI registrar", "annual"),
    "exam_placement": ("EAES / MoE placement", "annual"),
    "capacity_quota": ("MoE intake circulars", "annual"),
    "demographics": ("ESS / CSA", "annual"),
    "cohort_progression": ("MoE EMIS", "annual"),
    "graduate_outcomes": ("MoLS / graduate tracer", "annual"),
    "institution_capacity": ("HERQA / HEI returns", "annual"),
    "finance_support": ("MoE / HEI finance", "annual"),
    "macro_regional": ("NBE / ESS", "annual"),
    "labour_history": ("ESS LFS / UEUS", "annual"),
    "sector_output": ("ESS national accounts", "annual"),
    "formal_informal": ("ESS LFS", "annual"),
    "vacancies": ("MoLS / job boards", "quarterly"),
    "skills_demand": ("MoLS skills survey", "annual"),
    "public_hiring": ("Civil Service Commission", "annual"),
    "fdi_industrial": ("EIC / IPDC", "annual"),
    "macro_financial": ("NBE", "monthly/annual"),
    "labour_demographics": ("ESS", "annual"),
    "shocks_seasonality": ("derived / NBE commodity", "annual"),
}

OUT = ROOT / "docs" / "spec" / "ingestion"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cats = {c["source_table"]: c for m in S.models() for c in S.categories(m)}
    for table, cat in sorted(cats.items()):
        src, cadence = SOURCE.get(table, ("awaiting-source", "unknown"))
        cols = []
        for var in cat.get("variables", []):
            cols.append(f"- `{var['column']}` — {var['name']} ({var['id']})")
            for extra in var.get("also") or []:
                cols.append(f"- `{extra}` — additional series for {var['id']}")
        body = f"""# {table}

**Serves:** {cat['id']} {cat['name']}  
**Collection priority:** {cat['collection_priority']}%  
**Intended source:** {src}  
**Refresh cadence:** {cadence}  
**Currency / units:** ETB where monetary; percentages as 0–100.  
**Provenance:** generated files are `simulated`. A real ministry file can replace
`data/ethiopia/{table}.parquet` without changing service code if these columns
and keys are preserved.

## Keys

Grain includes the natural dimensions of the category (institution, campus,
region, program, sector, occupation, year as applicable) plus `year` covering
2016–2025 so lag-2 and 5-year rolling windows are computable.

## Columns

{chr(10).join(cols)}

## Replacement rule

Drop the simulated parquet/CSV in place. `backend/services/_validate.py` must
pass before the new file is served.
"""
        (OUT / f"{table}.md").write_text(body, encoding="utf-8")
        print(f"  {table}.md")


if __name__ == "__main__":
    main()
