"""
DOC1 step 7 — Analytic Hierarchy Process, structurally separate from learners.

Pairwise comparison matrix in; principal-eigenvector weights out; consistency
ratio gated at 0.1. CR above that is refused — no usable weights. Output is
displayed beside SHAP ranks, never blended into a score and never imported by
ml/model1, ml/model2, or a training script.
"""
from ml.ahp.saaty import (  # noqa: F401
    CR_MAX,
    AhpRefused,
    consistency_ratio,
    display_ranks,
    principal_eigenvector,
    weigh,
)
