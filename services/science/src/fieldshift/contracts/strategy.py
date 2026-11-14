"""Strategy (core) and StrategySet (FR5, FR6, FR10).

`criteria`, `requirements` and `generator` are extension points (⏸ §0.1 decides keys and
methods); this module holds only the shape that holds for any concept.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from fieldshift.contracts.common import (
    CanonicalUnit,
    Contract,
    LocalizedText,
    ProvenanceId,
    SchemaVersion,
    SiteId,
)
from fieldshift.contracts.evidence import Confidence, Evidence
from fieldshift.contracts.rotation import Rotation, RotationTimeline, check_timeline


class TextItem(Contract):
    text: LocalizedText
    provenance_ids: list[ProvenanceId] = Field(default_factory=list)


class StrategyBlocks(Contract):
    why: list[TextItem] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)  # VL2, VL3
    benefits: list[TextItem] = Field(min_length=1)
    gaps: list[TextItem] = Field(min_length=1)  # NEVER empty (VL2)
    local_review: list[TextItem] = Field(min_length=1)  # "Needs local review"


class CriterionValue(Contract):
    """⏸ keys and computation depend on D6, D7, D18, D19."""

    value: float
    unit: CanonicalUnit
    better: Literal["higher", "lower"]
    provenance_id: ProvenanceId
    confidence: Confidence


class StrategyRequirements(Contract):
    """⏸ extension (FR16): basis of the constraint filters."""

    irrigation: bool
    livestock: bool
    equipment: list[str]


class StrategyGenerator(Contract):
    """⏸ D8."""

    method_id: str
    version: str
    provenance_id: ProvenanceId


class Strategy(Contract):
    id: str
    site_id: SiteId
    is_current: bool  # IR3: exactly 1 per StrategySet
    name: LocalizedText
    rotation_id: str
    blocks: StrategyBlocks
    confidence: Confidence
    criteria: dict[str, CriterionValue]  # ⏸ extension (FR3)
    requirements: StrategyRequirements
    generator: StrategyGenerator


class StrategySet(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    rotations: list[Rotation]
    timelines: list[RotationTimeline]
    strategies: list[Strategy] = Field(min_length=3)  # FR5

    @model_validator(mode="after")
    def _consistent(self) -> StrategySet:
        current = sum(s.is_current for s in self.strategies)
        if current != 1:
            raise ValueError(f"exactly 1 strategy must have is_current=true (got {current})")
        ids = [s.id for s in self.strategies]
        if len(ids) != len(set(ids)):
            raise ValueError("strategy ids must be unique")
        rotations = {r.id: r for r in self.rotations}
        for s in self.strategies:
            if s.site_id != self.site_id:
                raise ValueError(f"strategy {s.id}: site_id {s.site_id!r} != {self.site_id!r}")
            if s.rotation_id not in rotations:
                raise ValueError(f"strategy {s.id}: rotation_id {s.rotation_id!r} not in set")
        for t in self.timelines:
            if t.rotation_id not in rotations:
                raise ValueError(f"timeline rotation_id {t.rotation_id!r} not in set")
            check_timeline(rotations[t.rotation_id], t)
        return self
