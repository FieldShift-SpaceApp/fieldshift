"""Metric and MonthlyProfile (climate indices, FR2, FR4, FR25)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from fieldshift.contracts.common import (
    CanonicalUnit,
    Contract,
    DataType,
    LocalizedText,
    Period,
    ProvenanceId,
    SchemaVersion,
    SiteId,
)
from fieldshift.contracts.evidence import Confidence

# Controlled vocabulary of the concept-agnostic climate indices (architecture, section on
# concept-agnostic indices; issue #22). Lets the app find an index without parsing `id`.
# Thresholds are not part of the key: they live in the provenance `method.parameters`.
# New value = MINOR version.
type IndexKey = Literal[
    "heat_days", "frost_days",
    "extreme_precip_days", "extreme_precip_total", "extreme_precip_threshold",
    "water_deficit", "growing_degree_days",
    "et0",
]  # fmt: skip


class MetricComparison(Contract):
    """'Before vs. now' (⏸ D5 decides which periods are shown)."""

    baseline_value: float
    baseline_period: Period
    delta: float
    delta_unit: CanonicalUnit  # e.g. 'delta_degC', 'days', 'mm'


class Metric(Contract):
    id: str  # e.g. "heat_days_gt35c.annual_mean.2006_2025"
    label: LocalizedText
    value: float
    unit: CanonicalUnit
    period: Period
    data_type: DataType
    provenance_id: ProvenanceId
    comparison: MetricComparison | None = None
    confidence: Confidence | None = None
    tags: list[str] = Field(default_factory=list)  # e.g. ["impact_finding"] (FR25)
    index_key: IndexKey | None = None  # v1.1.0


class MonthlyProfile(Contract):
    id: str  # e.g. "frost_probability.by_month.1991_2020"
    label: LocalizedText
    unit: CanonicalUnit
    # 12 values in CIVIL order; the UI reorders them by agricultural year
    values: list[float | None] = Field(min_length=12, max_length=12)
    period: Period
    data_type: DataType
    provenance_id: ProvenanceId
    index_key: IndexKey | None = None  # v1.1.0


class ClimateIndices(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    metrics: list[Metric]
    profiles: list[MonthlyProfile]
