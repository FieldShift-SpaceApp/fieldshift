"""Data contracts v1.1.0 between the pipeline and the app (ADR-4). Single source: these models.

⏸ Crop (D9) and Ranker (D7) depend on the concept (DECISIONS.md) and are not defined yet.
"""

from fieldshift.contracts.common import (
    CANONICAL_UNITS,
    SCHEMA_VERSION,
    Contract,
    LocalizedText,
    Period,
    Ref,
)
from fieldshift.contracts.evidence import Confidence, Evidence
from fieldshift.contracts.indices import (
    ClimateIndices,
    Metric,
    MetricComparison,
    MonthlyProfile,
)
from fieldshift.contracts.manifest import LayerStatus, SiteManifest
from fieldshift.contracts.provenance import Provenance, ProvenanceRegistry
from fieldshift.contracts.rotation import (
    Rotation,
    RotationFile,
    RotationMonthRef,
    RotationSegment,
    RotationTimeline,
    SoilCoverMonth,
)
from fieldshift.contracts.site import GeoJSONPolygon, Site, SitesIndex
from fieldshift.contracts.strategy import (
    CriterionValue,
    Strategy,
    StrategyBlocks,
    StrategySet,
    TextItem,
)
from fieldshift.contracts.timeseries import SeriesBundle, TimeSeries
from fieldshift.contracts.validation import RetrospectiveCheck, ValidationFile

# Top-level documents: each one is a published JSON file and carries `schema_version`.
TOP_LEVEL_MODELS: tuple[type[Contract], ...] = (
    Site,
    SitesIndex,
    ProvenanceRegistry,
    SeriesBundle,
    ClimateIndices,
    RotationFile,
    StrategySet,
    SiteManifest,
    ValidationFile,
)

__all__ = [
    "CANONICAL_UNITS",
    "SCHEMA_VERSION",
    "TOP_LEVEL_MODELS",
    "ClimateIndices",
    "Confidence",
    "Contract",
    "CriterionValue",
    "Evidence",
    "GeoJSONPolygon",
    "LayerStatus",
    "LocalizedText",
    "Metric",
    "MetricComparison",
    "MonthlyProfile",
    "Period",
    "Provenance",
    "ProvenanceRegistry",
    "Ref",
    "RetrospectiveCheck",
    "Rotation",
    "RotationFile",
    "RotationMonthRef",
    "RotationSegment",
    "RotationTimeline",
    "SeriesBundle",
    "Site",
    "SiteManifest",
    "SitesIndex",
    "SoilCoverMonth",
    "Strategy",
    "StrategyBlocks",
    "StrategySet",
    "TextItem",
    "TimeSeries",
    "ValidationFile",
]
