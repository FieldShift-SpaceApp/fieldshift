"""Shared conventions and types of the contracts (architecture Data Models; ADR-4, ADR-7).

SI-assisted: architecture by Aria (@architect); implementation with Claude Code; human review
required.

Named aliases (`type X = ...`) become their own `$defs` entry in the JSON Schema and an
`export type X = ...` in the generated TypeScript.
"""

from __future__ import annotations

from typing import Annotated, Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# 1.1.0 is a MINOR bump (issue #22): additions only, nothing removed or renamed.
SCHEMA_VERSION = "1.1.0"

type SchemaVersion = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+$")]
type SiteId = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{1,31}$")]
type ProvenanceId = Annotated[str, StringConstraints(pattern=r"^prov:[a-z0-9:._-]+$")]
type SeriesId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9._-]+$")]
type IsoDate = Annotated[
    str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")
]
type IsoMonth = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
type IsoDateTime = Annotated[
    str,
    StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$"),
]
type Month = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

# FR9: the 4 data types
type DataType = Literal["satellite_observed", "modeled", "computed", "user_provided"]

# ADR-7: canonical units. Conversion happens only at display time.
type CanonicalUnit = Literal[
    "degC", "delta_degC", "degC_d",
    "mm", "mm/d", "mm/month",
    "m3/m3", "MJ/m2/d", "m/s", "kPa", "%",
    "m", "ha", "deg",
    "days", "count", "probability", "1",
]  # fmt: skip

CANONICAL_UNITS: frozenset[str] = frozenset(get_args(CanonicalUnit.__value__))


class Contract(BaseModel):
    """Base of every contract: rejects unknown keys (catches typos in human-written YAML)."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class LocalizedText(Contract):
    """NFR15: Portuguese can be added without refactoring."""

    en: str = Field(min_length=1)
    pt: str | None = None


class Ref(Contract):
    label: str
    url: str | None = None
    doi: str | None = None
    citation: str | None = None


class Period(Contract):
    """Inclusive period."""

    start: IsoDate
    end: IsoDate

    @model_validator(mode="after")
    def _ordered(self) -> Period:
        if self.end < self.start:
            raise ValueError(f"period.end {self.end} < period.start {self.start}")
        return self
