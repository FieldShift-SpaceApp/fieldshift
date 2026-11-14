# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Daily -> calendar month (ADR-3).

Rule (conservative, stated in the provenance `aggregation` text): a month gets a value only when
every calendar day of that month has a valid daily value. Otherwise the month is `null` with
`q = "gap"`. Nothing is interpolated or filled.
"""

from __future__ import annotations

import calendar
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from typing import Literal

type Aggregator = Literal["mean", "sum"]


@dataclass(frozen=True)
class MonthValue:
    month: str  # YYYY-MM
    value: float | None
    valid_days: int
    days_in_month: int

    @property
    def complete(self) -> bool:
        return self.value is not None


def iter_months(first: date, last: date) -> list[tuple[int, int]]:
    months = []
    y, m = first.year, first.month
    while (y, m) <= (last.year, last.month):
        months.append((y, m))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return months


def to_monthly(daily: Mapping[date, float | None], how: Aggregator) -> list[MonthValue]:
    """Aggregate a daily series to calendar months, from the first to the last day present."""
    if not daily:
        return []
    days = sorted(daily)
    out: list[MonthValue] = []
    for y, m in iter_months(days[0], days[-1]):
        n_days = calendar.monthrange(y, m)[1]
        values = [daily.get(date(y, m, d)) for d in range(1, n_days + 1)]
        valid = [v for v in values if v is not None]
        value: float | None = None
        if len(valid) == n_days:
            value = sum(valid) if how == "sum" else sum(valid) / n_days
        out.append(MonthValue(f"{y:04d}-{m:02d}", value, len(valid), n_days))
    return out


def gap_runs(months: list[MonthValue]) -> list[tuple[str, str]]:
    """Contiguous runs of months without a value, as (first, last) YYYY-MM pairs."""
    runs: list[tuple[str, str]] = []
    start: str | None = None
    prev: str | None = None
    for mv in months:
        if not mv.complete:
            start = start or mv.month
            prev = mv.month
        elif start is not None:
            runs.append((start, prev or start))
            start = None
    if start is not None:
        runs.append((start, prev or start))
    return runs
