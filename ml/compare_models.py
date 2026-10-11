"""
PROC.S4 facade — compare Ethiopia estimators on a chronological holdout.

This is the spec path named in docs/spec/methodology.yaml. It does not train a
third Ethiopia learner: it calls ml/model1/compare.py and ml/model2/compare.py
and adds a named historical-mean baseline so each target has ≥3 candidates
including seasonal-naive.

US LSTM / Prophet artefacts stay on the old enrollment/labour path. They are
labelled not-compared and are not mixed into Ethiopia scores.
"""
from __future__ import annotations

import json
from pathlib import Path

from ml.model1 import compare as m1
from ml.model2 import compare as m2

OUT = Path(__file__).resolve().parent / "models" / "ethiopia_comparison.json"


def compare_all() -> dict:
    """Score M1 demand and M2 employment on grouped chronological holdouts."""
    enrollment = m1.compare_estimators()
    employment = m2.compare_estimators()
    m2_targets = employment.get("targets") or [{
        "id": "M2.employment",
        "target": employment.get("target", "employment_level"),
        **employment,
    }]
    result = {
        "validation": "grouped chronological holdout (last two observed years per series)",
        "random_split": False,
        "targets": [
            {
                "id": "M1.enrollment",
                "target": "program_enrollment_count",
                "candidates": sorted(enrollment["estimators"]),
                **enrollment,
            },
            *[
                {
                    **block,
                    "candidates": sorted((block.get("estimators") or {}).keys()),
                }
                for block in m2_targets
            ],
        ],
        "us_models_not_compared": sorted(set(
            list(enrollment.get("not_compared") or [])
            + list(employment.get("not_compared") or [])
        )),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    out = compare_all()
    print(json.dumps(out, indent=2))
