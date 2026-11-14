"""RetrospectiveCheck (FR24): published even when the result is negative."""

from __future__ import annotations

from typing import Literal

from fieldshift.contracts.common import (
    Contract,
    LocalizedText,
    Period,
    Ref,
    SchemaVersion,
    SiteId,
)
from fieldshift.contracts.evidence import Evidence


class RetrospectiveEvent(Contract):
    """Event chosen by the agronomist (Q12)."""

    name: LocalizedText
    period: Period
    source: Ref


class RetrospectiveCheck(Contract):
    id: str
    site_id: SiteId
    event: RetrospectiveEvent
    observed: list[Evidence]  # what the NASA data recorded
    result: Literal["confirms", "does_not_confirm", "inconclusive"]
    discussion: LocalizedText
    limitations: list[LocalizedText]
    checked_by: str


class ValidationFile(Contract):
    schema_version: SchemaVersion
    site_id: SiteId
    checks: list[RetrospectiveCheck]
