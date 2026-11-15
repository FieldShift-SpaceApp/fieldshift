# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Unit tests of the voucher targeting (no network, no raw data)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import targeting as tg  # noqa: E402

A = tg.Assumptions()


def farm(idx, ha, nm4=(4, 4), nm3=(3, 3), nm2=(2, 2), declared=None, assessed=True, size="medium"):
    return tg.Farm(
        idx=idx,
        cropland_ha=ha,
        declared_ha=declared if declared is not None else ha,
        size_class=size,
        assessed=assessed,
        nm_by_soil={4: nm4, 3: nm3, 2: nm2, 1: (1, 1)},
    )


def test_soil_test_cost_follows_the_10_ha_grid_and_two_layers():
    # 2 chemical analyses (0-20, 20-40 cm) at R$ 50 + 1 texture at R$ 40 per sampling area of <= 10 ha
    assert tg.soil_test_cost(10.0, A) == 140
    assert tg.soil_test_cost(10.01, A) == 280
    assert tg.soil_test_cost(0.5, A) == 140
    assert tg.soil_test_cost(100.0, A) == 1400  # R$ 14/ha in the first year, ~R$ 5/ha/yr over 24 months
    assert tg.soil_test_cost(10.0, tg.Assumptions(fixed_cost_per_farm_brl=300)) == 440


def test_soil_distribution_sums_to_one():
    d = tg.soil_distribution(tg.Assumptions(p_soil_favourable=0.3, share_level4_given_favourable=0.5))
    assert d == pytest.approx({4: 0.15, 3: 0.15, 2: 0.7})
    with pytest.raises(ValueError):
        tg.soil_distribution(tg.Assumptions(p_soil_favourable=1.2))


def test_outcome_expected_subsidy_gain():
    f = farm(0, 100.0)
    o = tg.outcome(f, A)  # 25% NM4, 25% NM3, 50% NM2
    assert o.p_nm3plus == pytest.approx(0.5)
    assert o.p_nm4 == pytest.approx(0.25)
    gain = (0.25 * 0.20 + 0.25 * 0.15 + 0.5 * 0.10) * 488 * 100
    assert o.subsidy_gain_brl == pytest.approx(gain)
    assert o.subsidy_total_brl == pytest.approx((0.25 * 0.40 + 0.25 * 0.35 + 0.5 * 0.30) * 488 * 100)


def test_contour_not_confirmed_drops_to_nm1():
    f = farm(0, 100.0)
    o = tg.outcome(f, tg.Assumptions(p_contour_confirmed=0.0))
    assert o.p_nm3plus == 0 and o.subsidy_gain_brl == 0
    assert o.subsidy_total_brl == pytest.approx(0.20 * 488 * 100)
    flat = farm(1, 100.0)
    flat.contour_needed = False  # mean slope < 3%: the contour rule does not apply
    assert tg.outcome(flat, tg.Assumptions(p_contour_confirmed=0.0)).p_nm3plus == pytest.approx(0.5)


def test_lower_end_of_the_range_is_the_default():
    f = farm(0, 100.0, nm4=(3, 4))
    assert tg.outcome(f, A).p_nm4 == 0
    assert tg.outcome(f, tg.Assumptions(range_end="upper")).p_nm4 == pytest.approx(0.25)


def test_fill_skips_what_does_not_fit_and_keeps_going():
    cost = {1: 60.0, 2: 50.0, 3: 30.0}
    assert tg.fill([1, 2, 3], cost, 100) == [1, 3]
    assert tg.fill([1, 2, 3], cost, 10) == []


def test_greedy_prefers_nm4_ranges_and_skips_unassessed():
    good = farm(1, 100.0)
    weak = farm(2, 100.0, nm4=(2, 2), nm3=(2, 2))
    unknown = farm(3, 100.0, assessed=False)
    outs = {f.idx: tg.outcome(f, A) for f in (good, weak)}
    order = tg.greedy_order([good, weak, unknown], outs, "subsidy")
    assert order == [1, 2]


def test_families_objective_puts_small_properties_first():
    big = farm(1, 300.0, declared=320)
    small = farm(2, 20.0, declared=30, nm4=(3, 3))
    outs = {f.idx: tg.outcome(f, A) for f in (big, small)}
    assert tg.greedy_order([big, small], outs, "families") == [2, 1]
    assert tg.greedy_order([big, small], outs, "subsidy")[0] == 1


def test_first_come_is_reproducible_and_bounded():
    farms = [farm(i, 10.0 * (i + 1)) for i in range(20)]
    outs = {f.idx: tg.outcome(f, A) for f in farms}
    r1 = tg.first_come(farms, outs, 2000, runs=50)
    r2 = tg.first_come(farms, outs, 2000, runs=50)
    assert r1 == r2
    assert r1["spent_brl"]["p95"] <= 2000
    assert r1["farms"]["p05"] <= r1["farms"]["mean"] <= r1["farms"]["p95"]
