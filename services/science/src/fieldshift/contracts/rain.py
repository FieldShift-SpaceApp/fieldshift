# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""EnsoRainSignal: heavy-rain days and rain totals in one window of the year, by ENSO phase, from
several rain sources side by side (v1.2.0).

Shape and one-document invariants only; the phase rule and thresholds are in the provenance.
"""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, StringConstraints, model_validator

from fieldshift.contracts.common import (
    Contract,
    LocalizedText,
    Month,
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
