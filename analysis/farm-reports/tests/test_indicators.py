# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Unit tests of the farm-level choices on top of the ZarcNM rules (no network, no imagery)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import indicators as ind  # noqa: E402


def test_c_range_reads_the_norm_bands_with_the_ruler_rmse():
    assert ind.c_range(None) is None
    assert ind.c_range(10.0) == (1, 1)  # 1.7-18.3% -> level 1
    assert ind.c_range(45.0) == (2, 2)  # 36.7-53.3% -> level 2
    assert ind.c_range(55.0) == (2, 3)  # 46.7-63.3% straddles 60%
    assert ind.c_range(25.0) == (1, 2)


def test_c_range_saturated_ruler_reads_three_or_four():
    assert ind.c_range(97.1) == (3, 4)
    assert ind.c_range(80.0) == (3, 4)


def test_t_range_counts_complete_years_after_the_last_signature():
    # last signature in the 1991 spring, every year observed since: 2026 - 1991 - 1 = 34 years -> level 4
    assert ind.t_range(1991, 1984, []) == (4, 4, 34, 34)
    # signature in 2022 -> 3 complete years (2023-2025) -> level 2
    assert ind.t_range(2022, 1984, []) == (2, 2, 3, 3)
    # signature in 2016, 2024 not observed -> lower end treats 2024 as a possible tillage
    assert ind.t_range(2016, 1984, [2024]) == (1, 4, 1, 9)


def test_t_range_without_signature_starts_before_the_first_observation():
    assert ind.t_range(None, 1984, []) == (4, 4, 42, 42)
    assert ind.t_range(None, None, []) is None


def test_d_range_weighted_median_and_level4_flag():
    assert ind.d_range(None, None) is None
    assert ind.d_range({"1": 0.2, "2": 0.5, "3": 0.3}, 0.1) == (2, 2)
    assert ind.d_range({"1": 0.1, "2": 0.3, "3": 0.6}, 0.2) == (3, 3)
    assert ind.d_range({"1": 0.1, "2": 0.3, "3": 0.6}, 0.55) == (3, 4)
    assert ind.d_range({"1": 0.6, "2": 0.3, "3": 0.1}, 0.0) == (1, 1)


def test_nm_range_best_case_and_locks():
    # all observable indicators at level 4 and soil at 4 -> NM4
    r = ind.nm_range((4, 4), (4, 4), (4, 4), 5.0, False)
    assert (r["nm_min"], r["nm_max"]) == (4, 4)
    assert r["contour_to_confirm"] is True
    # diversity at level 1 with straw at 3-4 -> mean 3.33-3.50 -> NM3 (one indicator at level 1 is no lock)
    r = ind.nm_range((4, 4), (3, 4), (1, 1), 2.0, False)
    assert (r["nm_min"], r["nm_max"]) == (3, 3)
    assert r["contour_to_confirm"] is False
    # mostly fallow winters: the literal 'consecutive soybean' reading sets the lower end to NM1
    r = ind.nm_range((4, 4), (3, 4), (1, 1), 2.0, True)
    assert r["nm_min"] == 1
    assert "IN 2/2025, item 3.2.1-II" in r["locks"]


def test_nm_range_two_indicators_at_level_two_cap_nm2():
    r = ind.nm_range((2, 2), (2, 2), (3, 3), 4.0, False)
    assert r["nm_max"] == 2


def test_nm_range_needs_all_three_indicators():
    assert ind.nm_range(None, (4, 4), (3, 3), 4.0, False) is None
    assert ind.band_label(None) == "not assessed"


@pytest.mark.parametrize("lo,hi,label", [(3, 4, "NM3-NM4"), (4, 4, "NM4"), (1, 2, "NM1-NM2")])
def test_band_label(lo, hi, label):
    assert ind.band_label({"nm_min": lo, "nm_max": hi}) == label


def test_size_class_by_fiscal_modules():
    import grids

    assert grids.size_class(4.0) == "small"
    assert grids.size_class(4.01) == "medium"
    assert grids.size_class(15.0) == "medium"
    assert grids.size_class(15.5) == "large"


def test_car_request_filters_one_municipality_and_has_no_personal_fields():
    import fetch_car

    url = fetch_car.url_for("4306106")
    assert "sicar_imoveis_rs" in url and "cod_municipio_ibge%3D4306106" in url
    assert set(fetch_car.KEEP) == {"cod_imovel", "area", "m_fiscal", "tipo_imovel", "status_imovel"}
