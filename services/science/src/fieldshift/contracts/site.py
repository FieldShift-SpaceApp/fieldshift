"""Site: configuration of each demo site (Story 2.2, AC2)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from fieldshift.contracts.common import (
    Contract,
    IsoDateTime,
    LocalizedText,
    Month,
    ProvenanceId,
    Ref,
    SchemaVersion,
    SiteId,
)


class GeoJSONPolygon(Contract):
    """WGS84, RFC 7946: positions are [lon, lat]; every ring is closed (last = first)."""

    type: Literal["Polygon"]
    coordinates: list[list[list[float]]] = Field(min_length=1)

    @field_validator("coordinates")
    @classmethod
    def _rings(cls, rings: list[list[list[float]]]) -> list[list[list[float]]]:
        for ring in rings:
            if len(ring) < 4:
                raise ValueError("polygon ring needs >= 4 positions")
            for pos in ring:
                if len(pos) != 2:
                    raise ValueError("position must be [lon, lat]")
                lon, lat = pos
                if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                    raise ValueError(f"position out of range: {pos}")
            if ring[0] != ring[-1]:
                raise ValueError("polygon ring must be closed (last position = first)")
        return rings


class GeoPoint(Contract):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ProvenancedValue(Contract):
    value: float
    provenance_id: ProvenanceId


class AgYear(Contract):
    start_month: Month
    label: Literal["single", "split"]  # split → "2024/25"


class SiteContext(Contract):
    region: LocalizedText
    summary: LocalizedText
    refs: list[Ref]


class Validation(Contract):
    name: str
    at: IsoDateTime


type Country = Literal["US", "BR"]
type Hemisphere = Literal["N", "S"]
type UnitSystem = Literal["metric", "imperial"]


class Site(Contract):
    schema_version: SchemaVersion
    id: SiteId
    name: LocalizedText
    country: Country
    hemisphere: Hemisphere  # informative only (ADR-7)
    timezone: str  # IANA
    point: GeoPoint  # field centroid
    field: GeoJSONPolygon
    area_ha: ProvenancedValue  # computed (geodesic)
    elevation_m: ProvenancedValue  # SRTM, or the POWER header in mode N2
    ag_year: AgYear
    default_units: UnitSystem  # FR23 / Q9
    context: SiteContext
    validated_by: Validation | None  # Story 2.3, AC6


class SitesIndexEntry(Contract):
    id: SiteId
    name: LocalizedText
    country: Country
    hemisphere: Hemisphere
    default_units: UnitSystem
    summary: LocalizedText


class SitesIndex(Contract):
    """data/sites/index.json (landing page, T1)."""

    schema_version: SchemaVersion
    sites: list[SitesIndexEntry]
