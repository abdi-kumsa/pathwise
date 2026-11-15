"""Calibration anchors for the simulated Ethiopia tables.

`calibration.yaml` holds every published figure (or labelled estimate) the
generator is calibrated to, with its source and confidence. This module loads
it, checks it is well formed, and offers the small lookups the generator needs.
Nothing in here invents a number: a missing year is interpolated between
anchors, and only between anchors.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

PATH = Path(__file__).resolve().parent / "calibration.yaml"
TIERS = {"official", "reputable", "news", "estimate"}
YEARS = list(range(2016, 2026))


@lru_cache(maxsize=1)
def load() -> dict:
    with PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def get(path: str):
    """Dotted lookup, e.g. get('exam.candidates')."""
    node = load()
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"calibration has no '{path}' (stopped at '{part}')")
        node = node[part]
    return node


def _year_values(node) -> dict[int, float]:
    """{year: value} from either {values: {...}} or {year: {value: ...}} shapes."""
    if isinstance(node, dict) and "values" in node and isinstance(node["values"], dict):
        node = node["values"]
    out = {}
    for k, v in (node or {}).items():
        try:
            year = int(k)
        except (TypeError, ValueError):
            continue
        if isinstance(v, dict):
            v = v.get("value")
        if v is not None:
            out[year] = float(v)
    return out


def series(path: str, years=YEARS) -> dict[int, float]:
    """A complete yearly series from sparse anchors.

    Linear interpolation between anchors; flat before the first and after the
    last. Raises if the path has no yearly anchors at all.
    """
    pts = _year_values(get(path))
    if not pts:
        raise KeyError(f"calibration '{path}' has no yearly values")
    known = sorted(pts)
    out = {}
    for y in years:
        if y in pts:
            out[y] = pts[y]
        elif y < known[0]:
            out[y] = pts[known[0]]
        elif y > known[-1]:
            out[y] = pts[known[-1]]
        else:
            lo = max(k for k in known if k < y)
            hi = min(k for k in known if k > y)
            w = (y - lo) / (hi - lo)
            out[y] = pts[lo] + w * (pts[hi] - pts[lo])
    return out


def regional_factor(path: str, region: str, year: int, default: float = 1.0) -> float:
    """Year factor for a region from a {region: {year: factor}} block."""
    block = get(path)
    vals = block.get(region) if isinstance(block, dict) else None
    if not vals:
        return default
    return float(vals.get(year, vals.get(str(year), default)))


def problems() -> list[str]:
    """Structural problems in the file: unknown tiers, estimates without a note,
    sourced figures without a URL or source. Empty list = well formed."""
    issues: list[str] = []

    def walk(node, where):
        if isinstance(node, dict):
            conf = node.get("confidence")
            if conf is not None:
                if conf not in TIERS:
                    issues.append(f"{where}: unknown confidence '{conf}'")
                elif conf == "estimate" and not node.get("note"):
                    issues.append(f"{where}: estimate without a note")
                elif conf != "estimate" and not (node.get("url") or node.get("source") or node.get("note")):
                    issues.append(f"{where}: {conf} figure without a source, url or note")
            for k, v in node.items():
                walk(v, f"{where}.{k}" if where else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{where}[{i}]")

    walk(load(), "")
    return issues
