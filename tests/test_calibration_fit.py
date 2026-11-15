"""The simulated Ethiopia tables stay close to the published figures they are
calibrated to (data/ethiopia/reference/calibration.yaml).

These are tolerance checks on the generated parquet files, not on a model:
they fail if someone edits the generator and the data drifts away from the
sources, or if the calibration file loses its sources.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
ETH = ROOT / "data" / "ethiopia"
sys.path.insert(0, str(ETH / "reference"))

import calibration as C  # noqa: E402


def _t(name: str) -> pd.DataFrame:
    return pd.read_parquet(ETH / f"{name}.parquet")


# ── the file itself ───────────────────────────────────────────────────────────

def test_calibration_file_is_well_formed():
    assert C.problems() == []


def test_every_section_the_generator_reads_is_present():
    for path in ("exam.candidates", "exam.public_placement", "macro.gdp_growth_pct",
                 "macro.inflation_pct", "macro.etb_per_usd", "labour.urban_unemployment_pct",
                 "population.regions_2022", "programmes.intake_weight", "disruption.institutions"):
        assert C.get(path)


def test_series_interpolates_between_anchors_only():
    s = C.series("exam.candidates")
    assert s[2022] == 896520
    assert min(s[2021], s[2023]) <= s[2022] or s[2022] >= s[2021]
    assert set(s) == set(C.YEARS)


# ── generated data against the anchors ────────────────────────────────────────

def test_exam_candidates_match_the_published_series():
    exam = _t("exam_placement").groupby("year")["exam_candidates_count"].sum()
    for year, v in C.series("exam.candidates").items():
        assert abs(exam[year] - v) / v < 0.01, (year, exam[year], v)


def test_pass_rates_collapse_after_the_2022_reform():
    exam = _t("exam_placement")
    w = exam.assign(p=exam["exam_candidates_count"] * exam["exam_pass_rate_pct"] / 100).groupby("year")
    rate = w["p"].sum() / w["exam_candidates_count"].sum() * 100
    assert rate[2021] > 35
    assert 2.5 < rate[2022] < 5.0, rate[2022]          # published 3.3%
    assert 2.5 < rate[2023] < 5.0, rate[2023]          # published 3.2%
    assert 7.0 < rate[2025] < 10.5, rate[2025]         # published 8.4-8.9%


def test_direct_placement_after_the_reform_matches_published_passers():
    placed = _t("exam_placement").groupby("year")["placed_count"].sum()
    assert abs(placed[2022] - 29909) / 29909 < 0.1
    assert abs(placed[2025] - 48929) / 48929 < 0.1


def test_public_intake_follows_national_placement():
    hist = _t("enrollment_history")
    pub = hist[hist["institution_type"] == "public"].groupby("year")["program_enrollment_count"].sum()
    share = float(C.get("programmes.modelled_public_share.value"))
    for year, v in C.series("exam.public_placement").items():
        assert abs(pub[year] - v * share) / (v * share) < 0.08, (year, pub[year], v * share)
    assert pub[2022] < 0.75 * pub[2021], "the 2022 reform must cut intake"


def test_tigray_universities_admit_nobody_during_the_war():
    hist = _t("enrollment_history")
    tg = hist[hist["region"] == "Tigray"].groupby("year")["program_enrollment_count"].sum()
    assert tg[2022] == 0 and tg[2023] == 0
    assert tg[2021] < 0.5 * tg[2019]
    assert 0 < tg[2025] < tg[2019], "partial recovery after the August 2023 reopening"
    quota = _t("capacity_quota")
    closed = quota[(quota["region"] == "Tigray") & quota["year"].isin([2022, 2023])]
    assert closed["program_suspension_flag"].all()
    assert (closed["available_seats"] == 0).all()


def test_tigray_reads_as_disrupted_in_the_labour_market():
    lab = _t("labour_history")
    tg = lab[lab["region"] == "Tigray"].groupby("year")["unemployment_rate_pct"].mean()
    others = lab[lab["region"] != "Tigray"].groupby("year")["unemployment_rate_pct"].mean()
    assert tg[2022] > 2 * others[2022]
    emp = lab[lab["region"] == "Tigray"].groupby("year")["employment_level"].sum()
    assert emp[2022] < 0.65 * emp[2020]


def test_programmes_exist_only_where_institutions_teach_them():
    hist = _t("enrollment_history")
    aastu = set(hist[hist["institution"] == "Addis Ababa Science and Technology University"]["field"])
    assert "Medicine & Health Sciences" not in aastu
    for inst in ("Unity University", "St. Mary's University"):
        fields = set(hist[hist["institution"] == inst]["field"])
        assert not fields & {"Law", "Education"}, inst       # MoE ban on private law/teacher education
    assert hist["institution"].nunique() == 19


def test_urban_unemployment_tracks_the_survey_series():
    lab = _t("labour_history")
    addis = lab[(lab["region"] == "Addis Ababa") & (lab["sector"] != "Agriculture")]
    rate = addis.groupby("year")["unemployment_rate_pct"].mean()
    assert 15 < rate[2021] < 30, rate[2021]                  # LFS 2021: 22.1%


def test_agoa_cut_shows_in_the_parks():
    fdi = _t("fdi_industrial")
    hawassa = fdi[fdi["industrial_park"] == "Hawassa Industrial Park"].set_index("year")["expected_employment"]
    assert hawassa[2022] < hawassa[2021] - 3000              # NBE: 4,321 jobs lost
    mekelle = fdi[fdi["industrial_park"] == "Mekelle Industrial Park"].set_index("year")
    assert not mekelle.loc[2022, "industrial_park_operational_flag"]


def test_macro_series_are_the_published_ones():
    m = _t("macro_financial").set_index("year")
    assert m.loc[2022, "inflation_rate_pct"] == pytest.approx(33.9)
    assert m.loc[2025, "exchange_rate_etb_usd"] > 2 * m.loc[2023, "exchange_rate_etb_usd"], "2024 float"
    assert m.loc[2020, "gdp_growth_rate_pct"] == pytest.approx(6.1)


def test_shock_table_names_the_shock():
    s = _t("shocks_seasonality")
    tg = s[(s["region"] == "Tigray") & (s["year"] == 2022)].iloc[0]
    assert tg["external_shock_flag"] and "conflict" in tg["shock_type"]
    assert s[s["year"] == 2020]["shock_type"].str.contains("covid").all()


def test_every_table_is_still_labelled_simulated():
    for path in ETH.glob("*.parquet"):
        df = pd.read_parquet(path, columns=["provenance"])
        assert set(df["provenance"].unique()) == {"simulated"}, path.name
