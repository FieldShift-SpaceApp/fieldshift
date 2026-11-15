# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""BareSoilCalendar: observed share of cropland without green cover, by fortnight (v1.2.0).

Satellite-observed counterpart of the rotation-derived soil-cover timeline: one value per
fortnight (median and range over the years), from two sensors side by side.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, model_validator

from fieldshift.contracts.common import (
    Contract,
    LocalizedText,
    Month,
    Period,
    ProvenanceId,
    SchemaVersion,
    SiteId,
)

type Percent = Annotated[float, Field(ge=0, le=100)]


class FortnightCover(Contract):
    index: int = Field(ge=0, le=23)  # 0 = 1-15 January … 23 = 16-31 December (civil order)
    month: Month
    half: Literal[1, 2]  # 1 = days 1-15, 2 = day 16 to the end of the month
    s2_median_pct: Percent | None
    s2_min_pct: Percent | None
    s2_max_pct: Percent | None
    s2_years: int = Field(ge=0)
    modis_median_pct: Percent | None
    modis_years: int = Field(ge=0)

    @model_validator(mode="after")
    def _ordered(self) -> FortnightCover:
        if self.index != (self.month - 1) * 2 + self.half - 1:
            raise ValueError(f"fortnight {self.index}: month/half do not match the index")
        trio = (self.s2_min_pct, self.s2_median_pct, self.s2_max_pct)
        if any(v is None for v in trio) != all(v is None for v in trio):
            raise ValueError(f"fortnight {self.index}: give all of min/median/max or none")
        if trio[0] is not None and not (trio[0] <= trio[1] <= trio[2]):  # type: ignore[operator]
            raise ValueError(f"fortnight {self.index}: expected min <= median <= max")
        if (self.s2_median_pct is None) != (self.s2_years == 0):
            raise ValueError(f"fortnight {self.index}: s2 value is null only with 0 years")
        if (self.modis_median_pct is None) != (self.modis_years == 0):
            raise ValueError(f"fortnight {self.index}: modis value is null only with 0 years")
        return self


class BareSoilCalendar(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    period: Period  # years the medians and ranges summarize
    ndvi_threshold: float = Field(gt=0, lt=1)  # "without green cover" = NDVI below this value
    fortnights: list[FortnightCover] = Field(min_length=24, max_length=24)
    s2_provenance_id: ProvenanceId
    modis_provenance_id: ProvenanceId
    caveats: list[LocalizedText] = Field(min_length=1)  # shown with the chart, not in a footnote

    @model_validator(mode="after")
    def _civil_order(self) -> BareSoilCalendar:
        if [f.index for f in self.fortnights] != list(range(24)):
            raise ValueError("fortnights must be 0..23 in order")
        return self
