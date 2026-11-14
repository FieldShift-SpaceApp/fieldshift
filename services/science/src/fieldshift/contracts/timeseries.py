"""TimeSeries: one variable of a site on the common base (ADR-3), in SI, with explicit gaps."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from fieldshift.contracts.common import (
    CanonicalUnit,
    Contract,
    DataType,
    IsoDate,
    IsoMonth,
    LocalizedText,
    Period,
    ProvenanceId,
    SchemaVersion,
    SeriesId,
    SiteId,
)

# Controlled vocabulary. New value = MINOR version.
type VariableKey = Literal[
    "air_temp_mean", "air_temp_max", "air_temp_min", "dewpoint", "rel_humidity",
    "precip", "wind_2m", "solar_rad", "surface_pressure",
    "soil_wetness_top_modeled", "soil_wetness_root_modeled",
    "soil_wetness_profile_modeled", "evap_land_modeled",
    "et0",
    "heat_days", "frost_days", "extreme_precip_days", "extreme_precip_total",
    "water_deficit", "growing_degree_days",
    "soil_moisture_surface", "soil_moisture_rootzone",
    "precip_satellite",
    "ndvi", "evi",
    "tws_anomaly",
    "et_actual",
    "elevation", "slope",
    "land_cover_class",
]  # fmt: skip


class SeriesAggregation(Contract):
    temporal: Literal["mean", "sum", "min", "max", "count", "p95", "composite", "none"]
    spatial: Literal["point", "containing_pixel", "polygon_mean", "polygon_median"]


class SeriesPoint(Contract):
    t: IsoMonth | IsoDate
    v: float | None  # gap = null, never interpolated (ADR-3)
    q: Literal["ok", "gap", "partial", "estimated"] | None = None


class KnownGap(Contract):
    start: IsoMonth
    end: IsoMonth
    reason: LocalizedText


class SeriesCoverage(Contract):
    first: IsoMonth | IsoDate
    last: IsoMonth | IsoDate
    valid_pct: float = Field(ge=0, le=100)
    known_gaps: list[KnownGap]


class SeriesBaseline(Contract):
    """Climatology used for anomalies (ADR-3)."""

    period: Period
    monthly_mean: list[float | None] = Field(min_length=12, max_length=12)  # index 0 = Jan
    provenance_id: ProvenanceId


class TimeSeries(Contract):
    id: SeriesId  # "{source}.{variable_key}.{frequency}_{aggregator}"
    site_id: SiteId
    variable_key: VariableKey
    label: LocalizedText
    unit: CanonicalUnit
    frequency: Literal["daily", "monthly", "annual", "static"]
    aggregation: SeriesAggregation
    data_type: DataType
    provenance_id: ProvenanceId
    points: list[SeriesPoint]
    coverage: SeriesCoverage
    baseline: SeriesBaseline | None = None


class SeriesBundle(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    series: list[TimeSeries]
