"""SiteManifest: layers, contract versions and degraded mode (NFR14, IR4)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from fieldshift.contracts.common import (
    Contract,
    IsoDateTime,
    LocalizedText,
    SchemaVersion,
    SeriesId,
    SiteId,
)

type LayerId = Literal[
    "power", "smap", "imerg", "modis_ndvi", "landsat_ndvi", "grace", "srtm",
    "openet", "cdl", "mapbiomas", "satveg", "ecostress",
]  # fmt: skip

type LayerReasonCode = Literal[
    "AUTH_REQUIRED", "SOURCE_TIMEOUT", "NO_DATA_FOR_AREA", "QUOTA_EXCEEDED",
    "NOT_EXTRACTED_YET", "OUT_OF_REGION", "CUT_BY_FLIGHT_RULE",
]  # fmt: skip


class LayerReason(Contract):
    code: LayerReasonCode
    message: LocalizedText


class LayerStatus(Contract):
    id: LayerId
    status: Literal["available", "partial", "unavailable", "not_applicable"]
    reason: LayerReason | None = None
    series_ids: list[SeriesId]


class PipelineInfo(Contract):
    git_sha: str
    command: str
    package_version: str


class ManifestFile(Contract):
    path: str
    contract: str
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    required: bool


class SiteManifest(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    generated_at: IsoDateTime
    pipeline: PipelineInfo
    contracts: dict[str, SchemaVersion]  # { site: "1.0.0", provenance: "1.0.0", … }
    files: list[ManifestFile]
    layers: list[LayerStatus]
