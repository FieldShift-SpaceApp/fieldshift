"""Agricultural year per site (ADR-7). No logic uses season or hemisphere.

Parity with apps/web/src/lib/agyear.ts through packages/contracts/fixtures/agyear-cases.json.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Literal

_ISO = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])(-\d{2})?$")


def _check_start_month(start_month: int) -> None:
    if not 1 <= start_month <= 12:
        raise ValueError(f"start_month must be 1..12, got {start_month}")


def _year_month(t: date | str) -> tuple[int, int]:
    if isinstance(t, date):
        return t.year, t.month
    match = _ISO.match(t)
    if not match:
        raise ValueError(f"expected YYYY-MM or YYYY-MM-DD, got {t!r}")
    return int(match.group(1)), int(match.group(2))


def ag_year_of(t: date | str, start_month: int) -> int:
    """`year` if `month >= start_month`, else `year - 1`. Accepts date, YYYY-MM or YYYY-MM-DD."""
    _check_start_month(start_month)
    year, month = _year_month(t)
    return year if month >= start_month else year - 1


def ag_month_index(month: int, start_month: int) -> int:
    """Position of a civil month inside the agricultural year: 0 = start_month … 11."""
    _check_start_month(start_month)
    if not 1 <= month <= 12:
        raise ValueError(f"month must be 1..12, got {month}")
    return (month - start_month) % 12


def ag_year_label(ag_year: int, label: Literal["single", "split"]) -> str:
    """'single' -> "2024"; 'split' -> "2024/25" (agricultural year crossing the new year)."""
    if label == "single":
        return str(ag_year)
    if label == "split":
        return f"{ag_year}/{(ag_year + 1) % 100:02d}"
    raise ValueError(f"label must be 'single' or 'split', got {label!r}")
