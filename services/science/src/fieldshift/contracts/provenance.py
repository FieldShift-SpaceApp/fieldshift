"""Provenance: the record every number on screen points to (FR19; VL1 data layer)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from fieldshift.contracts.common import (
    CanonicalUnit,
    Contract,
    DataType,
    IsoDateTime,
    LocalizedText,
    Period,
    ProvenanceId,
    Ref,
    SchemaVersion,
    SiteId,
)


class ProvenanceSource(Contract):
    """Required for satellite_observed and modeled."""

    dataset: str
    provider: str
    product: str
    version: str
    collection_id: str | None = None


class ProvenanceVariable(Contract):
    code: str
    name: LocalizedText
    unit: CanonicalUnit
    native_unit: str | None = None


class ProvenanceSpatial(Contract):
    resolution: str
    resolution_m: float | None = None
    support: Literal["point", "polygon", "containing_pixel", "regional"]  # ADR-3


class ProvenanceTemporal(Contract):
    resolution: Literal["daily", "3-hourly", "16-day", "monthly", "annual", "static"]
    period: Period


class ProvenanceMethod(Contract):
    """Required for computed; `doc_anchor` points to content/methods (VL1)."""

    name: str
    ref: Ref
    doc_anchor: str
    # v1.1.0: parameters the method was run with (thresholds, base temperature, reference
    # period...), so a number can be traced to the exact setting. Units go in the key name,
    # e.g. {"tmax_threshold_degC": 35.0}.
    parameters: dict[str, float | str] | None = None


class ProvenanceAccess(Contract):
    """Required for satellite_observed and modeled."""

    url: str
    doi: str | None = None
    accessed_at: IsoDateTime
    terms_url: str
    license: str | None = None


# v1.2.0: who the data belongs to, kept apart on screen and in RESOURCES.md:
# nasa = NASA data; partner = data of a space agency partner of the challenge (e.g. ESA
# Copernicus); other_public = other public sources (IBGE, NOAA, BCB, MAPA, ...).
type AttributionGroup = Literal["nasa", "partner", "other_public"]


class Attribution(Contract):
    group: AttributionGroup
    name: str = Field(min_length=1)  # e.g. "ESA Copernicus Sentinel-2 L2A"
    credit: str | None = None  # credit line the licence asks for, verbatim


class Provenance(Contract):
    id: ProvenanceId
    data_type: DataType
    title: LocalizedText
    source: ProvenanceSource | None = None
    variable: ProvenanceVariable
    spatial: ProvenanceSpatial
    temporal: ProvenanceTemporal
    aggregation: LocalizedText
    method: ProvenanceMethod | None = None
    inputs: list[ProvenanceId] = Field(default_factory=list)
    authored_by: str | None = None
    refs: list[Ref] = Field(default_factory=list)
    access: ProvenanceAccess | None = None
    limitations: list[LocalizedText]
    # v1.2.0, optional: one entry per data owner behind this number (a computed record lists the
    # owners of its inputs). Empty = not declared yet.
    attribution: list[Attribution] = Field(default_factory=list)

    @model_validator(mode="after")
    def _fr19_completeness(self) -> Provenance:
        """VL1 (data layer): FR19 fields required for each data type."""
        if self.data_type in ("satellite_observed", "modeled"):
            if self.source is None or self.access is None:
                raise ValueError(f"{self.id}: {self.data_type} requires source and access (FR19)")
            if not (self.source.version or self.source.collection_id):
                raise ValueError(f"{self.id}: set version or collection_id (FR19)")
        if self.data_type == "computed" and (self.method is None or not self.inputs):
            raise ValueError(f"{self.id}: computed requires method and inputs (lineage)")
        if self.data_type == "user_provided" and (not self.authored_by or not self.refs):
            raise ValueError(f"{self.id}: user_provided requires authored_by and refs")
        return self


class ProvenanceRegistry(Contract):
    schema_version: SchemaVersion
    site_id: SiteId | Literal["global"]
    records: dict[ProvenanceId, Provenance]

    @model_validator(mode="after")
    def _keys_match_ids(self) -> ProvenanceRegistry:
        for key, record in self.records.items():
            if key != record.id:
                raise ValueError(f"registry key {key!r} != record id {record.id!r}")
        return self
