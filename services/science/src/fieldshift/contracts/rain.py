# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""EnsoRainSignal: heavy-rain days and rain totals in one window of the year, by ENSO phase, from
several rain sources side by side (v1.2.0); SeasonToDate: the current season so far against the
same calendar days of past years (v1.3.0).

Shape and one-document invariants only; the phase rule and thresholds are in the provenance.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, StringConstraints, model_validator

from fieldshift.contracts.common import (
    Contract,
    IsoDate,
    IsoMonth,
    LocalizedText,
    Month,
    Period,
    ProvenanceId,
    SchemaVersion,
    SiteId,
)
from fieldshift.contracts.forecast import EnsoPhase

type RainSourceId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9-]{1,47}$")]
type OniSeason = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]  # e.g. "SON"


class RainYear(Contract):
    year: int
    oni: float  # ONI of the phase season, unit delta_degC
    phase: EnsoPhase
    total_mm: float | None  # None when the window is not complete in this source
    heavy_days: int | None = Field(default=None, ge=0)


class PhaseRainStats(Contract):
    phase: EnsoPhase
    n_years: int = Field(ge=0)
    mean_heavy_days: float | None
    mean_total_mm: float | None
    median_total_mm: float | None
    years_with_heavy_day: int = Field(ge=0)


class RainSourceSignal(Contract):
    id: RainSourceId
    label: LocalizedText
    first_year: int
    last_year: int
    years: list[RainYear]
    by_phase: list[PhaseRainStats] = Field(min_length=3, max_length=3)
    provenance_id: ProvenanceId

    @model_validator(mode="after")
    def _consistent(self) -> RainSourceSignal:
        if sorted({p.phase for p in self.by_phase}) != ["el_nino", "la_nina", "neutral"]:
            raise ValueError(f"{self.id}: by_phase needs one entry per phase")
        ys = [y.year for y in self.years]
        if ys != sorted(set(ys)):
            raise ValueError(f"{self.id}: years must be unique and ascending")
        if ys and (ys[0] < self.first_year or ys[-1] > self.last_year):
            raise ValueError(f"{self.id}: years outside first_year..last_year")
        for p in self.by_phase:
            n = sum(1 for y in self.years if y.phase == p.phase and y.total_mm is not None)
            if n != p.n_years:
                raise ValueError(f"{self.id}/{p.phase}: n_years {p.n_years} != {n} complete years")
        return self


class EnsoRainSignal(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    label: LocalizedText
    months: list[Month] = Field(min_length=1, max_length=12)  # civil months of the window
    phase_season: OniSeason  # ONI season that sets the phase of each year
    heavy_rain_mm: float = Field(gt=0)  # a heavy-rain day has rain >= this value
    oni_provenance_id: ProvenanceId
    sources: list[RainSourceSignal] = Field(min_length=1)
    notes: list[LocalizedText] = Field(default_factory=list)  # e.g. a source that was not usable

    @model_validator(mode="after")
    def _unique(self) -> EnsoRainSignal:
        ids = [s.id for s in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source ids must be unique")
        return self


# --- v1.3.0: SeasonToDate ---------------------------------------------------------------------


class MonthToDate(Contract):
    month: IsoMonth
    n_days: int = Field(ge=1)  # days of this month inside the window that have a value
    total_mm: float = Field(ge=0)
    climatology_mean_mm: float | None  # same calendar days, mean over the climatology years


class SeasonToDateSource(Contract):
    """One rain source over the window of the current year, set against the same calendar days of
    past years: chosen comparison years and the mean per ENSO phase."""

    id: RainSourceId
    label: LocalizedText
    window: Period  # days actually used for this source (inclusive), last one = its cut-off
    n_days: int = Field(ge=1)
    total_mm: float = Field(ge=0)
    heavy_days: int = Field(ge=0)
    wettest_day: IsoDate
    wettest_day_mm: float = Field(ge=0)
    months: list[MonthToDate] = Field(min_length=1)
    same_days: list[RainYear] = Field(default_factory=list)  # e.g. 2023, same calendar days
    climatology: Period  # first and last day of the climatology years used for by_phase
    by_phase: list[PhaseRainStats] = Field(min_length=3, max_length=3)
    provenance_id: ProvenanceId

    @model_validator(mode="after")
    def _consistent(self) -> SeasonToDateSource:
        if sorted({p.phase for p in self.by_phase}) != ["el_nino", "la_nina", "neutral"]:
            raise ValueError(f"{self.id}: by_phase needs one entry per phase")
        if not self.window.start <= self.wettest_day <= self.window.end:
            raise ValueError(f"{self.id}: wettest_day outside the window")
        if self.wettest_day_mm > self.total_mm or self.heavy_days > self.n_days:
            raise ValueError(f"{self.id}: wettest day or heavy days exceed the window")
        if sum(m.n_days for m in self.months) != self.n_days:
            raise ValueError(f"{self.id}: months n_days do not add up to n_days")
        ms = [m.month for m in self.months]
        if ms != sorted(set(ms)):
            raise ValueError(f"{self.id}: months must be unique and ascending")
        ys = [y.year for y in self.same_days]
        if ys != sorted(set(ys)):
            raise ValueError(f"{self.id}: same_days years must be unique and ascending")
        return self


class CurrentEnso(Contract):
    """ENSO state of the current year: the latest published ONI season, since the phase season
    of the climatology may not be complete yet."""

    season: OniSeason
    year: int
    oni: float  # unit delta_degC
    phase: EnsoPhase
    provenance_id: ProvenanceId


class ReportedFact(Contract):
    """A statement published by a third party (e.g. a crop bulletin), kept apart from the
    measurements: reported, not measured by FieldShift."""

    id: RainSourceId
    text: LocalizedText
    reported_by: str = Field(min_length=1)
    published: IsoDate
    url: str = Field(min_length=1)
    provenance_id: ProvenanceId


class SeasonToDate(Contract):
    """Rain of the current season so far at a site (v1.3.0): window total, heavy-rain days,
    comparison years and the mean of the same calendar days by ENSO phase, per source; plus
    reported third-party facts, kept apart."""

    schema_version: SchemaVersion
    site_id: SiteId
    label: LocalizedText
    year: int
    cutoff: IsoDate  # last day requested; a source can end earlier (its own window.end)
    heavy_rain_mm: float = Field(gt=0)
    phase_season: OniSeason  # ONI season that sets the phase of each climatology year
    current: CurrentEnso
    oni_provenance_id: ProvenanceId
    sources: list[SeasonToDateSource] = Field(min_length=1)
    reported: list[ReportedFact] = Field(default_factory=list)
    notes: list[LocalizedText] = Field(default_factory=list)

    @model_validator(mode="after")
    def _consistent(self) -> SeasonToDate:
        ids = [s.id for s in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("source ids must be unique")
        rids = [r.id for r in self.reported]
        if len(rids) != len(set(rids)):
            raise ValueError("reported ids must be unique")
        for s in self.sources:
            if s.window.end > self.cutoff or int(s.window.start[:4]) != self.year:
                raise ValueError(f"{s.id}: window outside year {self.year} / cutoff {self.cutoff}")
            if s.climatology.end >= s.window.start:
                raise ValueError(f"{s.id}: climatology must end before the window")
            for y in s.same_days:
                if y.year >= self.year:
                    raise ValueError(f"{s.id}: comparison year {y.year} is not a past year")
        return self
