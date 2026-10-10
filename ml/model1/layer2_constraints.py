"""
M1.L2 — policy and capacity constraint layer.

Deterministic and inspectable. Not a learned model. Applied in declared order
to an unconstrained demand table. Each row keeps both figures plus the
constraint that actually bound it (or `none` when demand already sat inside
every cap).

Order (DOC1 / DOC2 constraint-layer inputs):

  1. program_suspension          — closed programmes take zero
  2. esslce_eligibility          — pass-rate haircut on demand
  3. entrance_exam_cutoff        — score mean vs programme cutoff
  4. approved_intake_quota       — MoE intake circular
  5. available_seats             — seats offered this cycle
  6. program_capacity            — physical/staff capacity
  7. band_allocation             — 70:30 natural:social national directive
"""
from __future__ import annotations

import pandas as pd

from ml.features.model1 import c3_exam, c4_quota

CONSTRAINT_ORDER = (
    "program_suspension",
    "esslce_eligibility",
    "entrance_exam_cutoff",
    "approved_intake_quota",
    "available_seats",
    "program_capacity",
    "band_allocation",
)

NATURAL_SHARE = 0.70
SOCIAL_SHARE = 0.30


def _caps_for_year(
    quota: pd.DataFrame, exam: pd.DataFrame, quota_year: int, exam_year: int,
) -> pd.DataFrame:
    keys = ["institution", "campus", "region", "program"]
    cap_cols = [
        "program_suspension_flag", "approved_intake_quota", "available_seats",
        "program_capacity", "strategic_priority_flag", "exam_pass_rate_pct",
        "band_allocation_ratio", "exam_score_mean", "program_cutoff_score",
    ]
    q = quota[quota["year"] == quota_year].copy()
    e = exam[exam["year"] == exam_year].copy()
    if "field" in q.columns and "field" in e.columns:
        q = q.merge(
            e[[c for c in (
                "field", "exam_pass_rate_pct", "band_allocation_ratio",
                "exam_score_mean", "program_cutoff_score",
            ) if c in e.columns]].drop_duplicates("field"),
            on="field",
            how="left",
        )
    keep = [c for c in keys + cap_cols if c in q.columns]
    return q[keep].drop_duplicates(keys)


def apply_constraints(
    unconstrained: pd.DataFrame,
    quota: pd.DataFrame | None = None,
    exam: pd.DataFrame | None = None,
    natural_share: float = NATURAL_SHARE,
    social_share: float = SOCIAL_SHARE,
) -> pd.DataFrame:
    """Return unconstrained + constrained + binding_constraint per row.

    `natural_share` / `social_share` default to the 70:30 directive. The
    scenario engine (Wave 4.5) may pass other values; the request-path
    baseline is unchanged when they are omitted.
    """
    quota = quota if quota is not None else c4_quota.frame()
    exam = exam if exam is not None else c3_exam.frame()

    frames = []
    latest_quota_year = int(quota["year"].max())
    latest_exam_year = int(exam["year"].max())

    for year in unconstrained["academic_year"].unique():
        q_year = min(int(year), latest_quota_year)
        e_year = min(int(year), latest_exam_year)
        caps = _caps_for_year(quota, exam, q_year, e_year)
        demand = unconstrained[unconstrained["academic_year"] == year].copy()
        merge_keys = [
            c for c in ("institution", "campus", "region", "program")
            if c in demand.columns and c in caps.columns
        ]
        merged = demand.merge(caps, on=merge_keys, how="left", suffixes=("", "_cap"))
        frames.append(_constrain_year(merged, int(year), natural_share, social_share))

    return pd.concat(frames, ignore_index=True) if frames else unconstrained.copy()


def _constrain_year(
    df: pd.DataFrame,
    year: int,
    natural_share: float = NATURAL_SHARE,
    social_share: float = SOCIAL_SHARE,
) -> pd.DataFrame:
    demand = df["unconstrained_demand"].astype(float).clip(lower=0)
    constrained = demand.copy()
    binding = pd.Series(["none"] * len(df), index=df.index)

    suspended = df.get("program_suspension_flag")
    if suspended is not None:
        mask = suspended.fillna(False).astype(bool)
        constrained = constrained.where(~mask, 0.0)
        binding = binding.where(~mask, "program_suspension")

    pass_rate = df.get("exam_pass_rate_pct", pd.Series(100.0, index=df.index)).fillna(100.0)
    eligible = demand * (pass_rate.clip(0, 100) / 100.0)
    tighter = (constrained > eligible) & (binding != "program_suspension")
    constrained = constrained.where(~tighter, eligible)
    binding = binding.where(~tighter, "esslce_eligibility")

    if "program_cutoff_score" in df.columns and "exam_score_mean" in df.columns:
        cutoff = df["program_cutoff_score"].astype(float)
        mean = df["exam_score_mean"].astype(float)
        safe = cutoff.where(cutoff != 0)
        ratio = (mean / safe).clip(lower=0.3, upper=1.0).fillna(1.0)
        cutoff_cap = demand * ratio
        tighter = (constrained > cutoff_cap) & (binding != "program_suspension")
        constrained = constrained.where(~tighter, cutoff_cap)
        binding = binding.where(~tighter, "entrance_exam_cutoff")

    for name, col in (
        ("approved_intake_quota", "approved_intake_quota"),
        ("available_seats", "available_seats"),
        ("program_capacity", "program_capacity"),
    ):
        if col not in df.columns:
            continue
        cap = df[col].astype(float)
        cap = cap.where(cap.notna(), constrained)
        tighter = (constrained > cap) & (binding != "program_suspension")
        constrained = constrained.where(~tighter, cap)
        binding = binding.where(~tighter, name)

    constrained, binding = _apply_band_directive(
        df, constrained, binding, natural_share, social_share,
    )

    out = df[
        [c for c in (
            "institution", "campus", "region", "program", "field", "band",
            "academic_year", "horizon_step", "unconstrained_demand",
            "seasonal_naive", "ols_lags", "selected_model",
            "interval_low", "interval_high",
        ) if c in df.columns]
    ].copy()
    out["constrained_enrollment"] = constrained.clip(lower=0).round(1)
    out["binding_constraint"] = binding
    out["constraint_loss"] = (
        out["unconstrained_demand"] - out["constrained_enrollment"]
    ).clip(lower=0).round(1)
    out["academic_year"] = year
    return out


def _apply_band_directive(
    df: pd.DataFrame,
    constrained: pd.Series,
    binding: pd.Series,
    natural_share: float = NATURAL_SHARE,
    social_share: float = SOCIAL_SHARE,
) -> tuple[pd.Series, pd.Series]:
    """Cut the over-represented band so natural:social sits at the directive.

    Under-represented programmes are not inflated — the directive is a cap,
    not a fill. If one band is absent there is nothing to rebalance against.
    """
    if social_share <= 0:
        return constrained, binding
    band = df.get("band")
    if band is None:
        field_band = df.get("band_allocation_ratio")
        if field_band is None:
            return constrained, binding
        natural = field_band.fillna(0.5) >= 0.5
    else:
        natural = band.fillna("").eq("Natural science")

    nat_total = float(constrained[natural].sum())
    soc_total = float(constrained[~natural].sum())
    if nat_total <= 0 or soc_total <= 0:
        return constrained, binding

    total = nat_total + soc_total
    if nat_total / total <= natural_share + 1e-9:
        return constrained, binding

    target_nat = soc_total * (natural_share / social_share)
    scale = target_nat / nat_total if nat_total else 1.0
    scaled = constrained.copy()
    scaled.loc[natural] = constrained.loc[natural] * scale
    reduced = natural & (scale < 1.0) & (binding != "program_suspension")
    binding = binding.where(~reduced, "band_allocation")
    return scaled, binding


def explain_rules() -> dict:
    return {
        "order": list(CONSTRAINT_ORDER),
        "band_directive": {
            "natural_science": NATURAL_SHARE,
            "social_science": SOCIAL_SHARE,
        },
        "inspectable": True,
        "learned": False,
        "notes": (
            "Each row's binding_constraint is the last rule that reduced the "
            "figure. `none` means unconstrained demand already sat inside every cap."
        ),
    }
