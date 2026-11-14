# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Concept-agnostic climate indices on DAILY data, before monthly aggregation (ADR-3; issue #22).

Every threshold is a parameter (`IndexParams`). The defaults are generic placeholders, not a
crop or site decision: the agronomist sets them per site in `site.yaml` (`indices:` block, see
`load_index_params`). A day missing an input stays `None`, so the month that contains it becomes a
gap (never counted as "no event").

Definitions:
- heat day: Tmax > `heat_tmax_c` (strict);
- frost day: Tmin <= `frost_tmin_c` (architecture definition; ETCCDI FD uses Tmin < 0 degC);
- growing degree-days: max(0, (Tmax + Tmin) / 2 - `gdd_base_c`) (McMaster & Wilhelm 1997, method 1);
- extreme precipitation: precip > P95 of wet-day (>= `wet_day_mm`) precipitation in the baseline
  period (ETCCDI R95p threshold, Zhang et al. 2011); `extreme_precip_days` counts those days and
  `extreme_precip_total` sums their precipitation (ETCCDI R95pTOT);
- climatic water deficit: ET0 - precip (mm/d; > 0 = deficit, < 0 = surplus).

Percentile: linear interpolation between order statistics (Hyndman & Fan 1996, type 7).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields
from datetime import date
from pathlib import Path

import yaml

from fieldshift.errors import PipelineError
from fieldshift.harmonize.monthly import MonthValue
from fieldshift.indices.events import FROST_TMIN_C, as_count, is_frost_day, is_heat_day

type Daily = Mapping[date, float | None]


@dataclass(frozen=True)
class IndexParams:
    """Thresholds of the indices. Defaults are generic placeholders (see module docstring)."""

    heat_tmax_c: float = 35.0  # architecture example ("heat_days_gt35c"); per site (agronomist)
    frost_tmin_c: float = FROST_TMIN_C  # architecture: Tmin <= 0 degC
    gdd_base_c: float = 10.0  # generic base; per crop once the crops are decided (D9)
    wet_day_mm: float = 1.0  # ETCCDI wet day
    extreme_percentile: float = 95.0  # ETCCDI R95p
    baseline_start_year: int = 1991  # ADR-3: POWER baseline 1991-2020
    baseline_end_year: int = 2020

    def __post_init__(self) -> None:
        if not 0 < self.extreme_percentile < 100:
            raise PipelineError("indices.extreme_percentile must be in (0, 100)")
        if self.wet_day_mm < 0:
            raise PipelineError("indices.wet_day_mm must be >= 0")
        if self.baseline_end_year < self.baseline_start_year:
            raise PipelineError("indices.baseline_end_year < baseline_start_year")

    @property
    def baseline_years(self) -> range:
        return range(self.baseline_start_year, self.baseline_end_year + 1)

    @property
    def baseline_tag(self) -> str:
        return f"{self.baseline_start_year}_{self.baseline_end_year}"


# Parameters a site may set; the rest are fixed by the method definitions above.
SITE_SETTABLE = ("heat_tmax_c", "frost_tmin_c", "gdd_base_c")


def load_index_params(site_yaml: Path | None) -> tuple[IndexParams, frozenset[str]]:
    """Read the optional `indices:` block of a site.yaml.

    Returns the parameters and the names that were set by the site (the others are defaults,
    which the provenance declares as placeholders). Unknown keys fail (catches typos).
    """
    if site_yaml is None or not site_yaml.is_file():
        return IndexParams(), frozenset()
    raw = yaml.safe_load(site_yaml.read_text(encoding="utf-8")) or {}
    block = raw.get("indices") or {}
    if not isinstance(block, dict):
        raise PipelineError(f"{site_yaml}: `indices` must be a mapping")
    unknown = set(block) - set(SITE_SETTABLE)
    if unknown:
        raise PipelineError(
            f"{site_yaml}: unknown indices key(s) {sorted(unknown)}; allowed: {list(SITE_SETTABLE)}"
        )
    values: dict[str, float] = {}
    for key, value in block.items():
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise PipelineError(f"{site_yaml}: indices.{key} must be a number")
        values[key] = float(value)
    known = {f.name for f in fields(IndexParams)}
    assert set(values) <= known
    return IndexParams(**values), frozenset(values)


# --- daily indices ---------------------------------------------------------------------------


def heat_day(tmax_c: float | None, threshold_c: float) -> float | None:
    """1.0 / 0.0 per day (Tmax > threshold); None stays None (month becomes a gap)."""
    return as_count(is_heat_day(tmax_c, threshold_c))


def frost_day(tmin_c: float | None, threshold_c: float) -> float | None:
    """1.0 / 0.0 per day (Tmin <= threshold)."""
    return as_count(is_frost_day(tmin_c, threshold_c))


def growing_degree_days(tmax_c: float | None, tmin_c: float | None, base_c: float) -> float | None:
    """McMaster & Wilhelm (1997), method 1 (simple average, no upper cutoff)."""
    if tmax_c is None or tmin_c is None:
        return None
    return max(0.0, (tmax_c + tmin_c) / 2.0 - base_c)


def water_deficit(et0_mm: float | None, precip_mm: float | None) -> float | None:
    if et0_mm is None or precip_mm is None:
        return None
    return et0_mm - precip_mm


def percentile_linear(values: Iterable[float], p: float) -> float:
    """Hyndman & Fan (1996) type 7 (numpy/R default): x[h] with h = (n - 1) p / 100, 0-based."""
    xs = sorted(values)
    if not xs:
        raise ValueError("percentile of an empty sample")
    h = (len(xs) - 1) * p / 100.0
    lo = math.floor(h)
    hi = min(lo + 1, len(xs) - 1)
    return xs[lo] + (h - lo) * (xs[hi] - xs[lo])


def wet_day_percentile(precip: Daily, years: range, wet_day_mm: float, p: float) -> float | None:
    """P-th percentile of wet-day precipitation over `years`.

    `None` unless every day of those years is present and valid (no partial baseline).
    """
    sample: list[float] = []
    n_expected = sum(366 if _leap(y) else 365 for y in years)
    n_valid = 0
    for day, value in precip.items():
        if day.year in years and value is not None:
            n_valid += 1
            if value >= wet_day_mm:
                sample.append(value)
    if n_valid != n_expected or not sample:
        return None
    return percentile_linear(sample, p)


def _leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def daily_map(*series: Daily, fn) -> dict[date, float | None]:
    """Apply `fn` day by day over the union of days; a day absent from any input is None."""
    days = sorted(set().union(*(s.keys() for s in series)))
    return {d: fn(*(s.get(d) for s in series)) for d in days}


# --- climatology (baseline period) ------------------------------------------------------------


def _by_year_month(months: list[MonthValue]) -> dict[tuple[int, int], float | None]:
    return {(int(m.month[:4]), int(m.month[5:])): m.value for m in months}


def monthly_climatology(months: list[MonthValue], years: range) -> list[float | None]:
    """12 civil-month means over `years`. A month is None unless every year has a value."""
    table = _by_year_month(months)
    out: list[float | None] = []
    for m in range(1, 13):
        values = [table.get((y, m)) for y in years]
        out.append(None if any(v is None for v in values) else sum(values) / len(values))
    return out


def annual_mean_of_totals(months: list[MonthValue], years: range) -> float | None:
    """Mean over `years` of the yearly total (sum of 12 months). None unless all months exist."""
    table = _by_year_month(months)
    totals: list[float] = []
    for y in years:
        values = [table.get((y, m)) for m in range(1, 13)]
        if any(v is None for v in values):
            return None
        totals.append(sum(values))
    return sum(totals) / len(totals)
