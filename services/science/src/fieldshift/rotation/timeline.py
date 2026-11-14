# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Soil-cover derivation rule v1 (architecture, Data Models: Rotation; FR4, FR21, FR22).

1. Position of a month in the cycle: `year_index × 12 + ((month − start_month) mod 12)`;
   cycle length `L = cycle_years × 12`.
2. A segment covers the positions from `pos(start)` to `pos(end)` cyclically: when
   `pos(end) < pos(start)` it wraps around the end of the cycle.
3. The first `establishment_months` of a segment are `transition`; the rest is `soil.main`.
4. Overlapping segments: the most protective state wins (covered > residue > transition > bare).
5. A month no segment covers is `bare`. `bare_months_per_year` = bare months ÷ `cycle_years`.

Only the site's `start_month` is used: no season, no hemisphere (ADR-7).
"""

from __future__ import annotations

import calendar

from fieldshift.calendar.agyear import ag_month_index
from fieldshift.contracts import Metric, Period, Rotation, RotationTimeline, SoilCoverMonth
from fieldshift.contracts.common import LocalizedText
from fieldshift.contracts.rotation import RotationMonthRef, RotationSegment, check_timeline
from fieldshift.io.rounding import round_value
from fieldshift.provenance.rotation import soil_cover_prov_id

# Rule 4: higher = more protective.
PROTECTION = {"bare": 0, "transition": 1, "residue": 2, "covered": 3}

BARE_METRIC_ID = "bare_soil_months.per_year.cycle_mean"
BARE_METRIC_LABEL = "Bare-soil months per year (mean over the rotation cycle)"


def cycle_position(ref: RotationMonthRef, start_month: int) -> int:
    """Rule 1: position of a (cycle year, civil month) in agricultural-year order."""
    return ref.year_index * 12 + ag_month_index(ref.month, start_month)


def segment_positions(seg: RotationSegment, start_month: int, cycle_years: int) -> list[int]:
    """Rule 2: positions covered by a segment, in order, wrapping around the end of the cycle."""
    length = cycle_years * 12
    first = cycle_position(seg.start, start_month)
    last = cycle_position(seg.end, start_month)
    for name, pos in (("start", first), ("end", last)):
        if pos >= length:
            raise ValueError(f"{seg.id}: {name} is outside a {cycle_years}-year cycle")
    duration = (last - first) % length + 1
    if seg.soil.establishment_months > duration:
        raise ValueError(
            f"{seg.id}: establishment_months {seg.soil.establishment_months} is longer than the "
            f"segment ({duration} months)"
        )
    return [(first + i) % length for i in range(duration)]


def cycle_period(reference_ag_year: int, start_month: int, cycle_years: int) -> Period:
    """Civil dates of the cycle laid out from the agricultural year it describes."""
    # The last agricultural year of the cycle ends in the month before start_month.
    if start_month > 1:
        end_year, end_month = reference_ag_year + cycle_years, start_month - 1
    else:
        end_year, end_month = reference_ag_year + cycle_years - 1, 12
    last_day = calendar.monthrange(end_year, end_month)[1]
    return Period(
        start=f"{reference_ag_year:04d}-{start_month:02d}-01",
        end=f"{end_year:04d}-{end_month:02d}-{last_day:02d}",
    )


def derive_timeline(
    rotation: Rotation,
    ag_year_start_month: int,
    *,
    reference_ag_year: int,
    provenance_id: str | None = None,
) -> RotationTimeline:
    """Monthly soil state over the whole cycle, in agricultural-year order (rule v1)."""
    start = ag_year_start_month
    length = rotation.cycle_years * 12
    states: list[str] = ["bare"] * length  # rule 5
    seg_ids: list[list[str]] = [[] for _ in range(length)]

    for seg in rotation.segments:
        for offset, pos in enumerate(segment_positions(seg, start, rotation.cycle_years)):
            state = "transition" if offset < seg.soil.establishment_months else seg.soil.main
            seg_ids[pos].append(seg.id)
            if len(seg_ids[pos]) == 1 or PROTECTION[state] > PROTECTION[states[pos]]:
                states[pos] = state  # rule 4

    months = [
        SoilCoverMonth(
            position=pos,
            year_index=pos // 12,
            month=(start - 1 + pos) % 12 + 1,
            state=states[pos],
            segment_ids=seg_ids[pos],
        )
        for pos in range(length)
    ]
    prov = provenance_id or soil_cover_prov_id(rotation.site_id)
    bare = sum(1 for m in months if m.state == "bare")
    timeline = RotationTimeline(
        rotation_id=rotation.id,
        months=months,
        bare_months_per_year=Metric(
            id=BARE_METRIC_ID,
            label=LocalizedText(en=BARE_METRIC_LABEL),
            value=round_value(bare / rotation.cycle_years, "count"),
            unit="count",
            period=cycle_period(reference_ag_year, start, rotation.cycle_years),
            data_type="computed",
            provenance_id=prov,
        ),
        provenance_id=prov,
    )
    check_timeline(rotation, timeline)
    return timeline
