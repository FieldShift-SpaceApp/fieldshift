# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Soil-cover rule v1 (Story 2.3, AC2 and AC5; FR4, FR21, FR22).

Cases: cycle crossing the new year, double crop, perennial over several cycle years, explicit and
implicit bare soil, wrap at the end of the cycle, and the same rotation in both hemispheres.
Rotations here are built in code and are TEST FIXTURES, not agronomic data.
"""

import pytest
from pydantic import ValidationError

from fieldshift.contracts import Rotation, RotationSegment
from fieldshift.rotation.timeline import cycle_period, derive_timeline, segment_positions

REF = [{"label": "TEST FIXTURE: not a calendar source"}]


def seg(
    sid: str,
    role: str,
    *,
    start: tuple[int, int],
    end: tuple[int, int],
    main: str = "covered",
    est: int = 1,
) -> RotationSegment:
    return RotationSegment.model_validate(
        {
            "id": sid,
            "label": {"en": f"TEST FIXTURE {sid}"},
            "role": role,
            "crop_id": None if role == "fallow" else f"test-fixture-{sid}",
            "start": {"year_index": start[0], "month": start[1]},
            "end": {"year_index": end[0], "month": end[1]},
            "soil": {"main": main, "establishment_months": est},
            "irrigated": False,
            "refs": REF,
        }
    )


def rotation(cycle_years: int, segments: list[RotationSegment]) -> Rotation:
    return Rotation(
        id="test-fixture-rotation",
        site_id="test-fixture",
        name={"en": "TEST FIXTURE rotation"},
        kind="current",
        cycle_years=cycle_years,
        segments=segments,
        data_type="user_provided",
        provenance_id="prov:user:test-fixture:rotation-current",
    )


def derive(rot: Rotation, start_month: int):
    return derive_timeline(rot, start_month, reference_ag_year=2000)


def by_month(tl) -> dict[int, str]:
    assert len({m.year_index for m in tl.months}) == 1, "only for one-year cycles"
    return {m.month: m.state for m in tl.months}


def test_double_crop_with_fallow_wrapping_the_ag_year():
    """Ag year from September: soy Oct->Feb, second crop Feb->Jun, bare fallow Jul->Sep (wraps)."""
    rot = rotation(
        1,
        [
            seg("soy", "cash_crop", start=(0, 10), end=(0, 2)),
            seg("corn2", "second_crop", start=(0, 2), end=(0, 6)),
            seg("fallow", "fallow", start=(0, 7), end=(0, 9), main="bare", est=0),
        ],
    )
    tl = derive(rot, 9)

    assert [m.month for m in tl.months] == [9, 10, 11, 12, 1, 2, 3, 4, 5, 6, 7, 8]
    state = by_month(tl)
    assert state[10] == "transition"  # soy establishment
    assert state[2] == "covered"  # overlap: the most protective state wins
    assert {mo for mo, s in state.items() if s == "bare"} == {7, 8, 9}
    assert tl.bare_months_per_year.value == 3
    assert tl.bare_months_per_year.unit == "count"
    assert tl.bare_months_per_year.data_type == "computed"
    feb = next(m for m in tl.months if m.month == 2)
    assert feb.segment_ids == ["soy", "corn2"]


def test_cycle_crossing_the_civil_year_counts_both_sides():
    """A crop from November to March, ag year from January: the cycle wraps inside the year."""
    rot = rotation(1, [seg("crop", "cash_crop", start=(0, 11), end=(0, 3))])
    state = by_month(derive(rot, 1))
    assert state[11] == "transition"
    assert {mo for mo, s in state.items() if s == "covered"} == {12, 1, 2, 3}
    assert {mo for mo, s in state.items() if s == "bare"} == set(range(4, 11))


def test_months_without_any_segment_are_bare_with_no_segment_ids():
    rot = rotation(1, [seg("crop", "cash_crop", start=(0, 5), end=(0, 8))])
    tl = derive(rot, 5)
    uncovered = [m for m in tl.months if not m.segment_ids]
    assert [m.month for m in uncovered] == [9, 10, 11, 12, 1, 2, 3, 4]
    assert all(m.state == "bare" for m in uncovered)
    assert tl.bare_months_per_year.value == 8


def test_perennial_spans_several_cycle_years_with_one_establishment():
    """Alfalfa-like stand over 3+ years of a 5-year cycle (ag year from October)."""
    rot = rotation(
        5,
        [
            seg("stand", "forage_perennial", start=(0, 4), end=(3, 9), est=2),
            seg("grain", "cash_crop", start=(3, 10), end=(4, 7)),
            seg("fallow", "fallow", start=(4, 8), end=(4, 9), main="residue", est=0),
        ],
    )
    tl = derive(rot, 10)
    assert len(tl.months) == 60
    stand = [m for m in tl.months if "stand" in m.segment_ids]
    assert (stand[0].year_index, stand[0].month) == (0, 4)
    assert (stand[-1].year_index, stand[-1].month) == (3, 9)
    assert [m.state for m in stand[:2]] == ["transition", "transition"]
    assert all(m.state == "covered" for m in stand[2:])  # no re-establishment each year
    # Year 0 from October to March is before the stand: the only bare months of the cycle.
    bare = [(m.year_index, m.month) for m in tl.months if m.state == "bare"]
    assert bare == [(0, 10), (0, 11), (0, 12), (0, 1), (0, 2), (0, 3)]
    assert tl.bare_months_per_year.value == pytest.approx(1.2)
    assert [m.state for m in tl.months if "fallow" in m.segment_ids] == ["residue", "residue"]


def test_segment_wrapping_the_end_of_the_cycle():
    """Fallow from the last month of year 1 into the first month of year 0 (2-year cycle)."""
    rot = rotation(
        2,
        [
            seg("crop", "cash_crop", start=(0, 2), end=(1, 12)),
            seg("fallow", "fallow", start=(1, 12), end=(0, 1), main="residue", est=0),
        ],
    )
    tl = derive(rot, 1)
    assert tl.months[0].segment_ids == ["fallow"] and tl.months[0].state == "residue"
    assert tl.months[-1].segment_ids == ["crop", "fallow"] and tl.months[-1].state == "covered"
    assert tl.bare_months_per_year.value == 0


def test_residue_beats_a_crop_still_establishing():
    rot = rotation(
        1,
        [
            seg("straw", "fallow", start=(0, 6), end=(0, 8), main="residue", est=0),
            seg("cover", "cover_crop", start=(0, 8), end=(0, 11), est=1),
        ],
    )
    state = by_month(derive(rot, 6))
    assert state[8] == "residue"
    assert state[9] == "covered"


def test_whole_cycle_segment_is_allowed():
    rot = rotation(1, [seg("perennial", "forage_perennial", start=(0, 7), end=(0, 6),
                           est=0)])  # fmt: skip
    tl = derive(rot, 7)
    assert all(m.state == "covered" for m in tl.months)
    assert tl.bare_months_per_year.value == 0


def test_segment_longer_than_the_cycle_is_rejected():
    with pytest.raises(ValidationError, match="year_index 1 >= cycle_years 1"):
        rotation(1, [seg("long", "cash_crop", start=(0, 3), end=(1, 3))])


def test_establishment_longer_than_the_segment_is_rejected():
    rot = rotation(1, [seg("short", "cash_crop", start=(0, 3), end=(0, 4), est=3)])
    with pytest.raises(ValueError, match="establishment_months 3 is longer than the segment"):
        derive(rot, 1)


def test_segment_positions_are_cyclic():
    s = seg("x", "cash_crop", start=(0, 11), end=(0, 2))
    assert segment_positions(s, 9, 1) == [2, 3, 4, 5]
    assert segment_positions(s, 12, 1) == [11, 0, 1, 2]


@pytest.mark.parametrize("start_month", [1, 4, 7, 9, 10, 12])
def test_axis_starts_at_the_site_start_month(start_month):
    tl = derive(rotation(1, [seg("c", "cash_crop", start=(0, 5), end=(0, 6))]), start_month)
    months = [m.month for m in tl.months]
    assert months[0] == start_month
    assert sorted(months) == list(range(1, 13))
    assert [m.position for m in tl.months] == list(range(12))


def _shift(month: int, by: int) -> int:
    return (month - 1 + by) % 12 + 1


@pytest.mark.parametrize("cycle_years", [1, 2])
def test_same_rotation_shifted_between_hemispheres_has_the_same_bare_months(cycle_years):
    """Nevada-like ag year from October vs. Brazil-like from April: only start_month differs."""
    north = [
        seg("grain", "cash_crop", start=(0, 10), end=(0, 6)),
        seg("cover", "cover_crop", start=(cycle_years - 1, 8), end=(cycle_years - 1, 9)),
    ]
    south = [
        seg(
            s.id,
            s.role,
            start=(s.start.year_index, _shift(s.start.month, 6)),
            end=(s.end.year_index, _shift(s.end.month, 6)),
            main=s.soil.main,
            est=s.soil.establishment_months,
        )  # fmt: skip
        for s in north
    ]
    tl_n = derive(rotation(cycle_years, north), 10)
    tl_s = derive(rotation(cycle_years, south), 4)

    assert [m.state for m in tl_n.months] == [m.state for m in tl_s.months]
    assert [_shift(m.month, 6) for m in tl_n.months] == [m.month for m in tl_s.months]
    assert tl_n.bare_months_per_year.value == tl_s.bare_months_per_year.value
    # Northern grain from October to June leaves July bare; in the south the same month is January.
    assert next(m for m in tl_n.months if m.month == 7 and m.year_index == 0).state == "bare"
    assert next(m for m in tl_s.months if m.month == 1 and m.year_index == 0).state == "bare"


@pytest.mark.parametrize(
    ("start_month", "cycle_years", "expected"),
    [
        (9, 2, ("2000-09-01", "2002-08-31")),
        (1, 1, ("2000-01-01", "2000-12-31")),
        (3, 1, ("2000-03-01", "2001-02-28")),
        (10, 5, ("2000-10-01", "2005-09-30")),
    ],
)
def test_metric_period_covers_the_cycle(start_month, cycle_years, expected):
    period = cycle_period(2000, start_month, cycle_years)
    assert (period.start, period.end) == expected


def test_timeline_points_to_the_soil_cover_method_by_default():
    tl = derive(rotation(1, [seg("c", "cash_crop", start=(0, 5), end=(0, 6))]), 1)
    assert tl.provenance_id == "prov:computed:test-fixture:soil-cover:monthly"
    assert tl.bare_months_per_year.provenance_id == tl.provenance_id
    assert tl.rotation_id == "test-fixture-rotation"
