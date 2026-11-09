"""
PROC.S4 facade — compare Ethiopia estimators on a rolling-origin backtest.

The spec path named in docs/spec/methodology.yaml. Every estimated target has
four candidates, two of them naive baselines (seasonal-naive and historical
mean), scored at horizons 1–5 from every origin with enough history. No random
split. The request path uses the lowest-error candidate per horizon, and the
choice is recorded on every forecast row.

US LSTM / Prophet artefacts are labelled not-compared and are not mixed into
Ethiopia scores.
"""
from __future__ import annotations

import json
from pathlib import Path

from ml.model1 import compare as m1
from ml.model2 import compare as m2

OUT = Path(__file__).resolve().parent / "models" / "ethiopia_comparison.json"


def compare_all() -> dict:
    enrollment = m1.compare_estimators()
    labour = m2.compare_estimators()
    result = {
        "validation": "rolling-origin backtest per series (origins 2019 onwards, horizons 1–5)",
        "random_split": False,
        "targets": [
            {k: v for k, v in enrollment.items() if k != "not_compared"},
            *labour["targets"],
        ],
        "derived_targets": labour["derived_targets"],
        "us_models_not_compared": sorted(set(enrollment["not_compared"] + labour["not_compared"])),
        "accuracy_note": (
            "Errors measure how well each estimator recovers the simulated generator's "
            "process, not Ethiopian reality. They become ministry-relevant only when the "
            "same backtest runs on official series."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    out = compare_all()
    for t in out["targets"]:
        print(t["id"], t["selected_for_request_path"])
