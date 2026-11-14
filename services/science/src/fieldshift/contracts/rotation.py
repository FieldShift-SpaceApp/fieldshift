"""Rotation, RotationSegment and RotationTimeline (FR21, AP6, Story 2.3).

The timeline derivation (rule v1) belongs to `fieldshift.rotation`; this module holds only the
shape and the invariants that fit in one document.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from fieldshift.contracts.common import (
    Contract,
    LocalizedText,
    Month,
    ProvenanceId,
    Ref,
    SchemaVersion,
    SiteId,
)
from fieldshift.contracts.indices import Metric

type SegmentRole = Literal["cash_crop", "second_crop", "cover_crop", "forage_perennial", "fallow"]
type SoilState = Literal["covered", "residue", "transition", "bare"]


class RotationMonthRef(Contract):
    """Position inside the cycle: cycle year (relative to the agricultural year) + CIVIL month."""

    year_index: int = Field(ge=0)
    month: Month


class SegmentSoil(Contract):
    main: Literal["covered", "residue", "bare"]  # fallow with straw = 'residue'
    establishment_months: int = Field(ge=0)  # first months in 'transition'


class RotationSegment(Contract):
    id: str
    label: LocalizedText
    role: SegmentRole
    crop_id: str | None  # ⏸ crop catalog ref (D9); null for fallow
    start: RotationMonthRef  # inclusive
    end: RotationMonthRef  # inclusive; may wrap around the end of the cycle
    soil: SegmentSoil
    irrigated: bool
    refs: list[Ref]  # source of the planting/harvest calendar (Story 2.3, AC3)


class Rotation(Contract):
    id: str
    site_id: SiteId
    name: LocalizedText
    kind: Literal["current", "alternative"]
    cycle_years: int = Field(ge=1)
    segments: list[RotationSegment] = Field(min_length=1)
    data_type: Literal["user_provided", "computed"]
    provenance_id: ProvenanceId

    @model_validator(mode="after")
    def _segments_within_cycle(self) -> Rotation:
        ids = [s.id for s in self.segments]
        if len(ids) != len(set(ids)):
            raise ValueError(f"{self.id}: segment ids must be unique")
        for seg in self.segments:
            for ref in (seg.start, seg.end):
                if ref.year_index >= self.cycle_years:
                    raise ValueError(
                        f"{self.id}/{seg.id}: year_index {ref.year_index} >= cycle_years "
                        f"{self.cycle_years}"
                    )
        return self


class SoilCoverMonth(Contract):
    position: int = Field(ge=0)  # 0 … cycle_years*12-1, in agricultural-year order
    year_index: int = Field(ge=0)
    month: Month
    state: SoilState
    segment_ids: list[str]


class RotationTimeline(Contract):
    """Derived by the pipeline (data_type 'computed')."""

    rotation_id: str
    months: list[SoilCoverMonth]  # length = cycle_years × 12
    bare_months_per_year: Metric  # mean over the cycle
    provenance_id: ProvenanceId  # method "soil-cover-derivation v1"


def check_timeline(rotation: Rotation, timeline: RotationTimeline) -> None:
    """Invariants between a rotation and its timeline."""
    if timeline.rotation_id != rotation.id:
        raise ValueError(f"timeline.rotation_id {timeline.rotation_id!r} != {rotation.id!r}")
    expected = rotation.cycle_years * 12
    if len(timeline.months) != expected:
        raise ValueError(
            f"{rotation.id}: timeline has {len(timeline.months)} months; "
            f"cycle_years × 12 = {expected}"
        )
    if [m.position for m in timeline.months] != list(range(expected)):
        raise ValueError(f"{rotation.id}: timeline positions must be 0..{expected - 1} in order")


class RotationFile(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    rotation: Rotation
    timeline: RotationTimeline

    @model_validator(mode="after")
    def _consistent(self) -> RotationFile:
        if self.rotation.site_id != self.site_id:
            raise ValueError(f"rotation.site_id {self.rotation.site_id!r} != {self.site_id!r}")
        check_timeline(self.rotation, self.timeline)
        return self
