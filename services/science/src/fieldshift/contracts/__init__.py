"""Data contracts v1.3.0 between the pipeline and the app (ADR-4). Single source: these models.

⏸ Crop (D9) and Ranker (D7) depend on the concept (DECISIONS.md) and are not defined yet.
"""

from fieldshift.contracts.baresoil import BareSoilCalendar, FortnightCover
from fieldshift.contracts.common import (
    CANONICAL_UNITS,
    SCHEMA_VERSION,
    Contract,
    LocalizedText,
    Period,
    Ref,
)
from fieldshift.contracts.evidence import Confidence, Evidence
from fieldshift.contracts.forecast import (
    ForecastRecord,
    ForecastScore,
    ForecastScorecard,
    ForecastSource,
    ObservedWinter,
)
from fieldshift.contracts.indices import (
    ClimateIndices,
    Metric,
    MetricComparison,
    MonthlyProfile,
)
from fieldshift.contracts.manifest import LayerStatus, SiteManifest
from fieldshift.contracts.provenance import Attribution, Provenance, ProvenanceRegistry
from fieldshift.contracts.rain import (
    CurrentEnso,
    EnsoRainSignal,
    MonthToDate,
    PhaseRainStats,
    RainSourceSignal,
    RainYear,
    ReportedFact,
    SeasonToDate,
    SeasonToDateSource,
)
from fieldshift.contracts.replay import EventTimeline, ReplayEvent, ReplayValue
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
    ForecastScorecard,  # v1.2.0
    EventTimeline,  # v1.2.0
    BareSoilCalendar,  # v1.2.0
    EnsoRainSignal,  # v1.2.0
    SeasonToDate,  # v1.3.0
)

__all__ = [
    "CANONICAL_UNITS",
    "SCHEMA_VERSION",
    "TOP_LEVEL_MODELS",
    "Attribution",
    "BareSoilCalendar",
    "ClimateIndices",
    "Confidence",
    "Contract",
    "CriterionValue",
    "CurrentEnso",
    "EnsoRainSignal",
    "EventTimeline",
    "Evidence",
    "ForecastRecord",
    "ForecastScore",
    "ForecastScorecard",
    "ForecastSource",
    "FortnightCover",
    "GeoJSONPolygon",
    "LayerStatus",
    "LocalizedText",
    "Metric",
    "MetricComparison",
    "MonthToDate",
    "MonthlyProfile",
    "ObservedWinter",
    "Period",
    "PhaseRainStats",
    "Provenance",
    "ProvenanceRegistry",
    "RainSourceSignal",
    "RainYear",
    "Ref",
    "ReplayEvent",
    "ReplayValue",
    "ReportedFact",
    "RetrospectiveCheck",
    "Rotation",
    "RotationFile",
    "RotationMonthRef",
    "RotationSegment",
    "RotationTimeline",
    "SeasonToDate",
    "SeasonToDateSource",
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
