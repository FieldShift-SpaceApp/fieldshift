# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Every Table 1 row, every item 3.2 interval and every item 3.2.1 lock, with cases taken from the norm text."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import zarcnm_rules as zr  # noqa: E402

ALL4 = {"V%": 4, "Ca": 4, "m%": 4, "T": 4, "C": 4, "D": 4}
FLAT_DEEP = zr.SiteFacts(slope_pct=1.0, useful_soil_depth_cm=200)

SOY = zr.Crop("soybean", ("Glycine max",), ("Fabaceae",), days=130)
WHEAT = zr.Crop("wheat", ("Triticum aestivum",), ("Poaceae",), days=150)
CORN = zr.Crop("corn", ("Zea mays",), ("Poaceae",), days=140)
OAT_COVER_LONG = zr.Crop("black oat", ("Avena strigosa",), ("Poaceae",), is_cover=True, days=150)
OAT_COVER_SHORT = zr.Crop("black oat", ("Avena strigosa",), ("Poaceae",), is_cover=True, days=60)
VETCH_COVER_LONG = zr.Crop("vetch", ("Vicia sativa",), ("Fabaceae",), is_cover=True, days=150)
RADISH_COVER = zr.Crop("radish", ("Raphanus sativus",), ("Brassicaceae",), is_cover=True, days=60)


# ---------------- Table 1 row 1: V% by CEC ----------------
@pytest.mark.parametrize(
    ("v", "cec", "level"),
    [
        (34.9, 4.9, 1),
        (35, 4.9, 2),
        (39.9, 4.9, 2),
        (40, 4.9, 3),
        (49.9, 4.9, 3),
        (50, 4.9, 4),
        (39.9, 5, 1),
        (40, 5, 2),
        (44.9, 9.9, 2),
        (45, 9.9, 3),
        (54.9, 9.9, 3),
        (55, 9.9, 4),
        (49.9, 10, 1),
        (50, 10, 2),
        (54.9, 10, 2),
        (55, 10, 3),
        (64.9, 10, 3),
        (65, 10, 4),
    ],
)
def test_base_saturation_rows_by_cec(v, cec, level):
    assert zr.level_base_saturation(v, cec) == level


def test_base_saturation_rejects_impossible_values():
    with pytest.raises(ValueError):
        zr.level_base_saturation(101, 8)
    with pytest.raises(ValueError):
        zr.level_base_saturation(50, -1)


# ---------------- rows 2-5 ----------------
@pytest.mark.parametrize(("ca", "level"), [(0.49, 1), (0.5, 2), (0.99, 2), (1.0, 3), (1.49, 3), (1.5, 4)])
def test_calcium(ca, level):
    assert zr.level_calcium(ca) == level


@pytest.mark.parametrize(("m", "level"), [(20, 1), (35, 1), (19.9, 2), (10, 2), (9.9, 3), (5, 3), (4.9, 4), (0, 4)])
def test_aluminium_saturation(m, level):
    assert zr.level_aluminium_saturation(m) == level


@pytest.mark.parametrize(("t", "level"), [(0, 1), (2, 1), (3, 2), (4, 2), (5, 3), (7, 3), (8, 4), (30, 4)])
def test_years_without_tillage(t, level):
    assert zr.level_years_without_tillage(t) == level


def test_years_without_tillage_wants_complete_years():
    with pytest.raises(ValueError):
        zr.level_years_without_tillage(7.5)  # "em anos completos" (item 2.1-IV)


@pytest.mark.parametrize(("c", "level"), [(0, 1), (29.9, 1), (30, 2), (59.9, 2), (60, 3), (89.9, 3), (90, 4), (100, 4)])
def test_straw_cover(c, level):
    assert zr.level_straw_cover(c) == level


def test_straw_cover_rejects_out_of_range():
    with pytest.raises(ValueError):
        zr.level_straw_cover(120)


# ---------------- row 6: diversity, with item 2.4 ----------------
def test_diversity_level1_soybean_only():
    assert zr.level_diversity([SOY, SOY, SOY]) == 1


def test_diversity_level2_soy_wheat_succession():
    assert zr.level_diversity([SOY, WHEAT] * 3) == 2


def test_diversity_level2_needs_four_crops():
    assert zr.level_diversity([SOY, WHEAT, SOY]) == 1


def test_diversity_level3_one_long_cover():
    assert zr.level_diversity([SOY, WHEAT, SOY, OAT_COVER_LONG, SOY, WHEAT]) == 3


def test_diversity_level3_three_short_covers_branch():
    assert zr.level_diversity([SOY, OAT_COVER_SHORT] * 3) == 3


def test_diversity_level3_branch_still_needs_six_crops():
    # INTERPRETATION: the 6-crop minimum also applies to the "3 covers of more than 45 days" branch
    assert zr.level_diversity([SOY, OAT_COVER_SHORT, OAT_COVER_SHORT, OAT_COVER_SHORT]) == 2


def test_diversity_cover_must_last_more_than_45_days():
    too_short = zr.Crop("oat", ("Avena strigosa",), ("Poaceae",), is_cover=True, days=45)
    assert zr.level_diversity([SOY, too_short] * 3) == 2


def test_diversity_long_cover_must_include_a_grass():
    # item 2.4-IV: covers of more than 4 months must include grasses; a solo vetch of 150 days counts only as >45 d
    assert zr.level_diversity([SOY, WHEAT, SOY, VETCH_COVER_LONG, SOY, WHEAT]) == 2


def test_diversity_four_months_boundary():
    four_months = zr.Crop("oat", ("Avena strigosa",), ("Poaceae",), is_cover=True, days=121)
    longer = zr.Crop("oat", ("Avena strigosa",), ("Poaceae",), is_cover=True, days=122)
    base = [SOY, WHEAT, SOY, WHEAT, SOY]
    assert zr.level_diversity([*base, four_months]) == 2
    assert zr.level_diversity([*base, longer]) == 3


def test_diversity_level4_four_species_long_cover_and_two_more_covers():
    seq = [SOY, OAT_COVER_LONG, CORN, RADISH_COVER, SOY, OAT_COVER_SHORT]
    assert zr.level_diversity(seq) == 4


def test_diversity_level4_needs_four_species():
    assert zr.level_diversity([SOY, OAT_COVER_LONG] * 3) == 3


def test_diversity_level4_needs_two_covers_besides_the_long_one():
    # INTERPRETATION: "1 cover > 4 months E 2 covers > 45 days" = 3 covers in all
    seq = [SOY, OAT_COVER_LONG, CORN, WHEAT, SOY, RADISH_COVER]
    assert zr.level_diversity(seq) == 3


def test_diversity_item_2_4_I_third_crop_grass_replaces_short_cover():
    # text example: "trigo ou aveia branca após milho 2ª safra"
    wheat_third = zr.Crop(
        "wheat after 2nd-crop corn", ("Triticum aestivum",), ("Poaceae",), days=120, short_window_grass=True
    )
    seq = [SOY, CORN, wheat_third, SOY, OAT_COVER_SHORT, SOY, OAT_COVER_SHORT]
    assert zr.level_diversity(seq) == 3
    plain = zr.Crop("wheat", ("Triticum aestivum",), ("Poaceae",), days=120)
    assert zr.level_diversity([SOY, CORN, plain, SOY, OAT_COVER_SHORT, SOY, OAT_COVER_SHORT]) == 2


def test_diversity_item_2_4_II_grazed_cover_still_counts():
    grazed = zr.Crop("oat grazed", ("Avena strigosa",), ("Poaceae",), is_cover=True, days=150, grazed=True)
    assert zr.level_diversity([SOY, WHEAT, SOY, grazed, SOY, WHEAT]) == 3


def test_diversity_item_2_4_III_conserved_forage_not_counted():
    silage = zr.Crop("oat silage", ("Avena sativa",), ("Poaceae",), days=120, conserved_forage=True)
    assert zr.level_diversity([SOY, WHEAT, SOY, silage]) == 1  # 3 counted crops < 4
    assert zr.count_diversity([SOY, silage]).crops == 1


def test_diversity_item_2_4_V_pasture_12_months_waives_crop_count():
    pasture = zr.Crop(
        "pasture",
        ("Urochloa brizantha", "Lolium multiflorum"),
        ("Poaceae",),
        is_cover=True,
        days=400,
        pasture_months=13,
    )
    seq = [SOY, pasture, RADISH_COVER, OAT_COVER_SHORT]  # 4 crops, 5 species, 3 families
    assert zr.level_diversity(seq) == 4


# ---------------- item 3.2: intervals of the mean ----------------
@pytest.mark.parametrize(("mi", "nm"), [(1.0, 1), (1.75, 1), (1.76, 2), (2.75, 2), (2.76, 3), (3.50, 3), (3.51, 4)])
def test_nm_from_mean_intervals(mi, nm):
    assert zr.nm_from_mean(mi) == nm


def test_classify_all_level4_is_nm4():
    r = zr.classify(ALL4, FLAT_DEEP)
    assert (r.nm, r.mean, r.locks) == (4, 4.0, ())


def test_classify_mean_exactly_3_50_is_nm3():
    r = zr.classify({"V%": 4, "Ca": 4, "m%": 4, "T": 4, "C": 3, "D": 2}, FLAT_DEEP)
    assert r.mean == 3.5 and r.nm == 3


def test_item_2_2_missing_indicator_blocks_classification():
    with pytest.raises(zr.IncompleteIndicatorsError):
        zr.classify({"V%": 4, "Ca": 4, "m%": None, "T": 4, "C": 4, "D": 4})
    with pytest.raises(zr.IncompleteIndicatorsError):
        zr.classify({"T": 4, "C": 4, "D": 4})


# ---------------- item 3.2.1 locks ----------------
def test_lock_I_contour_missing_on_slope_gives_nm1():
    r = zr.classify(ALL4, zr.SiteFacts(slope_pct=3.0, contour_share=0.74, useful_soil_depth_cm=200))
    assert r.nm == 1 and r.locks[0].citation == "IN 2/2025, item 3.2.1-I"


def test_lock_I_contour_on_75_percent_passes():
    assert zr.classify(ALL4, zr.SiteFacts(slope_pct=8, contour_share=0.75, useful_soil_depth_cm=200)).nm == 4


def test_lock_I_does_not_apply_below_3_percent():
    assert zr.classify(ALL4, zr.SiteFacts(slope_pct=2.99, contour_share=0.0, useful_soil_depth_cm=200)).nm == 4


def test_lock_I_unknown_slope_is_reported_not_assumed():
    r = zr.classify(ALL4)
    assert r.nm == 4
    assert any("3.2.1-I" in u for u in r.unverified) and any("209/2026" in u for u in r.unverified)


def test_lock_II_soy_on_soy_gives_nm1():
    r = zr.classify(ALL4, zr.SiteFacts(slope_pct=0, consecutive_soybean=True, useful_soil_depth_cm=200))
    assert r.nm == 1


def test_lock_III_legume_only_limits_to_nm2():
    r = zr.classify(ALL4, zr.SiteFacts(slope_pct=0, legume_only_succession=True, useful_soil_depth_cm=200))
    assert r.nm == 2


def test_lock_IV_a_two_indicators_at_level1_gives_nm1_regardless_of_mean():
    levels = {"V%": 4, "Ca": 4, "m%": 4, "T": 4, "C": 1, "D": 1}  # mean 3.0 would be NM3
    r = zr.classify(levels, FLAT_DEEP)
    assert r.nm_from_mean == 3 and r.nm == 1


def test_lock_IV_b_two_indicators_at_level2_gives_nm2():
    levels = {"V%": 4, "Ca": 4, "m%": 4, "T": 4, "C": 2, "D": 2}  # mean 3.33
    assert zr.classify(levels, FLAT_DEEP).nm == 2


def test_lock_IV_b_one_level1_and_one_level2_gives_nm2():
    levels = {"V%": 4, "Ca": 4, "m%": 4, "T": 4, "C": 1, "D": 2}  # mean 3.17
    assert zr.classify(levels, FLAT_DEEP).nm == 2


def test_lock_IV_single_level1_alone_does_not_lock():
    levels = {"V%": 4, "Ca": 4, "m%": 4, "T": 4, "C": 4, "D": 1}  # mean 3.5 -> NM3
    r = zr.classify(levels, FLAT_DEEP)
    assert r.nm == 3 and r.locks == ()


def test_lock_V_a_aluminium_level1_with_high_mean_gives_nm2():
    levels = {"V%": 4, "Ca": 4, "m%": 1, "T": 4, "C": 4, "D": 4}  # mean 3.5 -> NM3
    r = zr.classify(levels, FLAT_DEEP)
    assert r.nm == 2 and r.locks[-1].citation == "IN 2/2025, item 3.2.1-V-a"


def test_lock_V_b_aluminium_level2_with_high_mean_gives_nm3():
    levels = {"V%": 4, "Ca": 4, "m%": 2, "T": 4, "C": 4, "D": 4}  # mean 3.67 -> NM4
    r = zr.classify(levels, FLAT_DEEP)
    assert r.nm == 3


def test_lock_V_only_when_mean_is_level3_or_4():
    levels = {"V%": 2, "Ca": 2, "m%": 2, "T": 3, "C": 3, "D": 3}  # mean 2.5 -> NM2 (IV-b also NM2)
    r = zr.classify(levels, FLAT_DEEP)
    assert r.nm == 2 and not any("3.2.1-V" in lock.citation for lock in r.locks)


def test_most_restrictive_lock_wins():
    facts = zr.SiteFacts(slope_pct=0, legume_only_succession=True, consecutive_soybean=True, useful_soil_depth_cm=200)
    assert zr.classify(ALL4, facts).nm == 1


# ---------------- Portaria 209/2026 item 2.4: useful soil depth ----------------
@pytest.mark.parametrize(("zus", "cap"), [(45, 1), (49, 1), (60, 1), (61, 2), (80, 2), (81, 3), (100, 3), (101, 4)])
def test_depth_cap(zus, cap):
    assert zr.depth_cap(zus) == cap


def test_shallow_soil_example_from_portaria_stays_nm1():
    # text example: Neossolos Litólicos with Zus < 50 cm stay at NM1
    r = zr.classify(ALL4, zr.SiteFacts(slope_pct=0, useful_soil_depth_cm=45))
    assert r.nm == 1


# ---------------- sequence helpers ----------------
def test_consecutive_soybean_literal_reading_of_fallow():
    assert zr.has_consecutive_soybean([SOY, SOY, SOY]) is True
    assert zr.has_consecutive_soybean([SOY, WHEAT, SOY]) is False


def test_legume_only_succession():
    assert zr.has_legume_only_succession([SOY, VETCH_COVER_LONG, SOY]) is True
    oat_vetch = zr.Crop(
        "oat+vetch", ("Avena strigosa", "Vicia sativa"), ("Poaceae", "Fabaceae"), is_cover=True, days=150
    )
    assert zr.has_legume_only_succession([SOY, oat_vetch, SOY]) is False
    assert zr.has_legume_only_succession([SOY, SOY]) is True


def test_subsidy_table_cgsr_111():
    assert zr.SUBSIDY_PCT_SOY == {1: 20, 2: 30, 3: 35, 4: 40}
