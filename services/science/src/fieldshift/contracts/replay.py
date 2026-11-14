# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""EventTimeline: a dated replay of one season, each event with its numbers and sources (v1.2.0).

Used for the "2023 replay" complement; the shape is season-agnostic.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import Field, StringConstraints, model_validator

from fieldshift.contracts.common import (
    CanonicalUnit,
    Contract,
    IsoDate,
    LocalizedText,
    Period,
    ProvenanceId,
    Ref,
    SchemaVersion,
    SiteId,
)

type ReplayEventKind = Literal["forecast", "planting_window", "credit", "yield", "outcome"]
# Units used only by replay values (not canonical display units, ADR-7): money per hectare in
# constant reais (the price base is in the provenance record) and crop yield.
type ReplayExtraUnit = Literal["BRL/ha", "kg/ha"]
type ReplayKey = Annotated[str, StringConstraints(pattern=r"^[a-z0-9][a-z0-9._-]{0,63}$")]


class ReplayValue(Contract):
    key: ReplayKey
    label: LocalizedText
    value: float
    unit: CanonicalUnit | ReplayExtraUnit


class ReplayEvent(Contract):
    id: ReplayKey
    kind: ReplayEventKind
    date: IsoDate | None = None  # a dated publication or decision
    period: Period | None = None  # a window or an annual statistic
    title: LocalizedText
    detail: LocalizedText
    values: list[ReplayValue] = Field(default_factory=list)
    provenance_id: ProvenanceId
    refs: list[Ref] = Field(min_length=1)

    @model_validator(mode="after")
    def _when(self) -> ReplayEvent:
        if (self.date is None) == (self.period is None):
            raise ValueError(f"{self.id}: give exactly one of date or period")
        keys = [v.key for v in self.values]
        if len(keys) != len(set(keys)):
            raise ValueError(f"{self.id}: value keys must be unique")
        return self

    @property
    def start(self) -> str:
        return self.date if self.date is not None else self.period.start  # type: ignore[union-attr]


class EventTimeline(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    id: ReplayKey
    title: LocalizedText
    period: Period
    # Narrative order (the sequence the replay tells). Each event carries its own date or period,
    # so an annual statistic can follow a dated alert without pretending to be one day.
    events: list[ReplayEvent] = Field(min_length=1)

    @model_validator(mode="after")
    def _within(self) -> EventTimeline:
        ids = [e.id for e in self.events]
        if len(ids) != len(set(ids)):
            raise ValueError("event ids must be unique")
        for e in self.events:
            end = e.date if e.date is not None else e.period.end  # type: ignore[union-attr]
            if e.start < self.period.start or end > self.period.end:
                raise ValueError(f"{e.id}: outside the timeline period")
        return self
