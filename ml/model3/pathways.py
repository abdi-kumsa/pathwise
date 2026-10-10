"""
M3.4 — programme-to-occupation pathway graph.

Nodes are MoE programmes, occupations and sectors. Edges are the Ethiopia
join backbone (programme → field → occupation → sector), which is also the
mapping the skills heatmap uses.
"""
from __future__ import annotations

from ml.features.model1 import c1_enrollment
from ml.features.model2 import c4_vacancies, c5_skills


def pathway_graph() -> dict:
    enroll = c1_enrollment.frame()
    vac = c4_vacancies.frame()
    skills = c5_skills.frame()

    programs = []
    if not enroll.empty:
        cols = [c for c in ("program", "field", "band") if c in enroll.columns]
        programs = (
            enroll[cols].drop_duplicates().sort_values("program").to_dict(orient="records")
            if cols else []
        )

    occupations = []
    edges = []
    if not vac.empty:
        occ_cols = [c for c in ("occupation", "field", "sector") if c in vac.columns]
        occupations = vac[occ_cols].drop_duplicates().sort_values("occupation").to_dict(orient="records")
        for row in occupations:
            program = next((p for p in programs if p.get("field") == row.get("field")), None)
            if program:
                edges.append({
                    "source": program["program"],
                    "source_type": "program",
                    "target": row["occupation"],
                    "target_type": "occupation",
                    "field": row.get("field"),
                    "sector": row.get("sector"),
                })
                if row.get("sector"):
                    edges.append({
                        "source": row["occupation"],
                        "source_type": "occupation",
                        "target": row["sector"],
                        "target_type": "sector",
                        "field": row.get("field"),
                    })

    skill_rows = []
    if not skills.empty:
        latest = int(skills["year"].max())
        now = skills[skills["year"] == latest]
        keep = [c for c in (
            "field", "technical_skill_demand", "digital_skill_demand",
            "soft_skill_demand", "emerging_skill_demand",
            "skill_shortage_index", "skill_oversupply_index",
        ) if c in now.columns]
        skill_rows = now[keep].to_dict(orient="records")

    return {
        "programs": programs,
        "occupations": occupations,
        "edges": edges,
        "skills": skill_rows,
        "note": (
            "Edges follow the Ethiopia join backbone: one programme per MoE field, "
            "one occupation per field. Not an official occupational classification."
        ),
    }
