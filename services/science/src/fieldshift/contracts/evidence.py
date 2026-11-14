"""Evidence (an item of the "Evidence" block, FR6) and Confidence (FR10)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from fieldshift.contracts.common import (
    CanonicalUnit,
    Contract,
    DataType,
    LocalizedText,
    Period,
    ProvenanceId,
    SeriesId,
)


class Confidence(Contract):
    level: Literal["high", "medium", "low"]
    reason: LocalizedText
    independent_sources: int = Field(ge=0)  # distinct dataset families (VL4)

    @model_validator(mode="after")
    def _vl4(self) -> Confidence:
        # The cross-file validator recomputes this number from provenance_ids.
        if self.level == "high" and self.independent_sources < 2:
            raise ValueError("VL4: level 'high' requires independent_sources >= 2")
        return self


class Evidence(Contract):
    """VL3: every evidence item has a number, a dataset and a period."""

    id: str
    statement: LocalizedText
    value: float
    unit: CanonicalUnit
    period: Period
    dataset_label: str = Field(min_length=1)
    series_ids: list[SeriesId]
    provenance_ids: list[ProvenanceId] = Field(min_length=1)
    data_type: DataType
    confidence: Confidence
