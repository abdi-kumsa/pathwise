"""
Provenance stamp for every data-bearing API response.

Wave 0 of the feedback-document plan: every series must say where it came from
and how far it can be trusted. The Ethiopia re-base (Wave 1) will change the
*values* in this stamp; the shape stays.

    simulated  — generated or benchmark data, never official statistics
    official   — a real ministry / statistics-agency file
    derived    — computed from other stamped series (ratios, ranks, forecasts)

`stamp()` is the only writer. There is no helper that silently drops the block.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any, Optional

# Mirrors backend/services/_datasets.py::DATASET_LABEL. Duplicated on purpose
# so this module stays importable without pandas.
DATASET_LABEL = "Simulated Ethiopian structure · 2016–2025"

TIERS = ("simulated", "official", "derived")


@dataclass(frozen=True)
class Provenance:
    source: str
    tier: str
    as_of: str
    method: str
    caveat: Optional[str] = None

    def __post_init__(self) -> None:
        if self.tier not in TIERS:
            raise ValueError(f"tier must be one of {TIERS}, got {self.tier!r}")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if d.get("caveat") is None:
            d.pop("caveat")
        return d


def default_provenance() -> Provenance:
    """The stamp that applies until Wave 1 retires the US benchmark data."""
    return Provenance(
        source="Simulated Ethiopian structure",
        tier="simulated",
        as_of="2016–2025",
        method="seeded generator in data/ethiopia/generate.py",
        caveat=(
            "Simulated Ethiopian structure (real regions, HEIs, MoE bands). "
            "Not official MoE, MoLS or ESS statistics."
        ),
    )


def stamp(payload: dict, prov: Optional[Provenance] = None) -> dict:
    """Return a shallow copy of `payload` with a `provenance` block.

    Existing `provenance` is left alone — a service that already stamped a
    more specific source (a single table, a model run) wins over the default.
    Also fills `dataset_label` when missing, so older UI that reads that field
    keeps working.
    """
    if not isinstance(payload, dict):
        raise TypeError("stamp() only accepts a dict payload")
    out = dict(payload)
    if "provenance" not in out:
        out["provenance"] = (prov or default_provenance()).to_dict()
    if "dataset_label" not in out:
        out["dataset_label"] = DATASET_LABEL
    return out


def attach_default_if_missing(body: bytes) -> bytes:
    """Middleware helper: stamp a JSON object body, leave everything else."""
    try:
        data = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return body
    if not isinstance(data, dict) or "provenance" in data:
        return body
    return json.dumps(stamp(data), ensure_ascii=False).encode("utf-8")
