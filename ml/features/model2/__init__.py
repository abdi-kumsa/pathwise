"""Model 2 feature modules — one file per DOC1 category (M2.C1–C10)."""
from . import (
    c1_labour,
    c2_sector,
    c3_formal_informal,
    c4_vacancies,
    c5_skills,
    c6_public,
    c7_fdi,
    c8_macro,
    c9_demographics,
    c10_shocks,
)

FEATURE_MODULES = (
    c1_labour,
    c2_sector,
    c3_formal_informal,
    c4_vacancies,
    c5_skills,
    c6_public,
    c7_fdi,
    c8_macro,
    c9_demographics,
    c10_shocks,
)
