"""Saaty AHP: eigenvector weights and consistency ratio.

CR > 0.1 means the pairwise judgements are inconsistent. This module refuses
those matrices rather than returning a number that looks fine.
"""
from __future__ import annotations

from typing import Any

import numpy as np

CR_MAX = 0.1

# Saaty's random-index table (n = 1..10).
_RI = {
    1: 0.0,
    2: 0.0,
    3: 0.58,
    4: 0.90,
    5: 1.12,
    6: 1.24,
    7: 1.32,
    8: 1.41,
    9: 1.45,
    10: 1.49,
}


class AhpRefused(ValueError):
    """Raised when CR exceeds 0.1 — weights must not be used."""

    def __init__(self, consistency_ratio: float, detail: dict[str, Any]):
        super().__init__(
            f"AHP consistency ratio {consistency_ratio:.4f} exceeds {CR_MAX}"
        )
        self.consistency_ratio = consistency_ratio
        self.detail = detail


def _as_matrix(raw: list[list[float]]) -> np.ndarray:
    arr = np.asarray(raw, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise ValueError("pairwise matrix must be square")
    if arr.shape[0] < 2:
        raise ValueError("pairwise matrix must be at least 2×2")
    if np.any(arr <= 0):
        raise ValueError("pairwise entries must be positive")
    return arr


def principal_eigenvector(matrix: list[list[float]]) -> tuple[float, np.ndarray]:
    """Largest-eigenvalue pair; the vector is normalised to sum to 1."""
    arr = _as_matrix(matrix)
    values, vectors = np.linalg.eig(arr)
    idx = int(np.argmax(values.real))
    lam = float(values[idx].real)
    vec = np.abs(vectors[:, idx].real)
    total = float(vec.sum())
    if total <= 0:
        raise ValueError("principal eigenvector is degenerate")
    return lam, vec / total


def consistency_ratio(matrix: list[list[float]]) -> dict[str, Any]:
    """Return CR, CI, lambda_max. n≤2 is defined as perfectly consistent."""
    arr = _as_matrix(matrix)
    n = int(arr.shape[0])
    lam, weights = principal_eigenvector(matrix)
    if n <= 2:
        cr, ci = 0.0, 0.0
    else:
        ci = (lam - n) / (n - 1)
        ri = _RI.get(n)
        if ri is None:
            raise ValueError(f"no Saaty RI for n={n}; use 3–10 criteria")
        cr = 0.0 if ri == 0 else ci / ri
    usable = cr <= CR_MAX
    return {
        "n": n,
        "lambda_max": round(lam, 6),
        "consistency_index": round(float(ci), 6),
        "consistency_ratio": round(float(cr), 6),
        "usable": usable,
        "weights": [round(float(w), 6) for w in weights] if usable else None,
    }


def weigh(
    matrix: list[list[float]],
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Principal-eigenvector weights, or AhpRefused when CR > 0.1."""
    report = consistency_ratio(matrix)
    names = list(labels) if labels else [f"c{i+1}" for i in range(report["n"])]
    if len(names) != report["n"]:
        raise ValueError("labels length must match matrix order")
    if not report["usable"]:
        raise AhpRefused(report["consistency_ratio"], {
            "refused": True,
            "reason": "consistency_ratio_exceeds_0.1",
            "consistency_ratio": report["consistency_ratio"],
            "consistency_index": report["consistency_index"],
            "lambda_max": report["lambda_max"],
            "weights": None,
            "labels": names,
        })
    weights = {
        name: value for name, value in zip(names, report["weights"])
    }
    return {
        "refused": False,
        "consistency_ratio": report["consistency_ratio"],
        "consistency_index": report["consistency_index"],
        "lambda_max": report["lambda_max"],
        "weights": weights,
        "labels": names,
        "sum": round(sum(weights.values()), 6),
    }


def display_ranks(
    ahp_weights: dict[str, float],
    learned: list[dict[str, Any]],
    *,
    feature_key: str = "feature",
    score_key: str = "importance",
) -> list[dict[str, Any]]:
    """Place AHP ranks next to learned/SHAP ranks. Never a blended score."""
    shap_order = [
        row[feature_key]
        for row in sorted(
            learned,
            key=lambda r: abs(float(r.get(score_key) or 0)),
            reverse=True,
        )
    ]
    shap_rank = {name: i + 1 for i, name in enumerate(shap_order)}
    ahp_order = sorted(ahp_weights.items(), key=lambda kv: kv[1], reverse=True)
    ahp_rank = {name: i + 1 for i, (name, _) in enumerate(ahp_order)}
    names = list(dict.fromkeys([*ahp_weights, *shap_order]))
    rows = []
    for name in names:
        rows.append({
            "feature": name,
            "ahp_rank": ahp_rank.get(name),
            "ahp_weight": ahp_weights.get(name),
            "learned_rank": shap_rank.get(name),
            "blended": False,
        })
    return rows
