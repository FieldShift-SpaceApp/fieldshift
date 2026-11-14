# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Daily event flags (ADR-3: counted on daily data, then aggregated with `count`).

Thresholds are parameters, not constants: the heat threshold is set per site by the agronomist
(architecture, Data Models > Metric). Frost uses the architecture definition, Tmin <= 0 degC.
"""

from __future__ import annotations

FROST_TMIN_C = 0.0


def is_heat_day(tmax_c: float | None, threshold_c: float) -> bool | None:
    """Tmax strictly above the threshold. `None` input stays unknown (never counted as no-event)."""
    if tmax_c is None:
        return None
    return tmax_c > threshold_c


def is_frost_day(tmin_c: float | None, threshold_c: float = FROST_TMIN_C) -> bool | None:
    """Tmin at or below the threshold (default 0 degC)."""
    if tmin_c is None:
        return None
    return tmin_c <= threshold_c


def as_count(flag: bool | None) -> float | None:
    """1.0 / 0.0 for a monthly `sum`, keeping unknown days as `None` so the month becomes a gap."""
    return None if flag is None else float(flag)
