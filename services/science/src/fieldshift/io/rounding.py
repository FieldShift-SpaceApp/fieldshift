# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Rounding policy per canonical unit (architecture, Data Access Layer): readable diffs, small JSON.

Units not listed in the architecture table (`%`, `m/s`, counts) get the decimals below; the table
in the architecture is the source for the others.
"""

from __future__ import annotations

DECIMALS: dict[str, int] = {
    "degC": 1,
    "delta_degC": 1,
    "mm": 1,
    "mm/d": 1,
    "mm/month": 1,
    "ha": 1,
    "deg": 1,
    "MJ/m2/d": 2,
    "kPa": 2,
    "m3/m3": 3,
    "1": 3,
    "probability": 3,
    "m": 0,
    # not in the architecture table
    "%": 1,
    "m/s": 2,
    "days": 1,
    "count": 1,
    "degC_d": 1,
}


def round_value(value: float | None, unit: str) -> float | None:
    """Round to the unit's policy. `None` stays `None` (a gap is data too)."""
    if value is None:
        return None
    return round(value, DECIMALS[unit]) + 0.0  # + 0.0 turns -0.0 into 0.0
