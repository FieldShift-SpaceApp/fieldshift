# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""ADR-3 monthly aggregation: sum vs. mean, complete-month rule, gaps stay null."""

from datetime import date, timedelta

import pytest

from fieldshift.harmonize.monthly import gap_runs, to_monthly
from fieldshift.indices.events import as_count, is_frost_day, is_heat_day


def days(start: date, n: int, value: float = 1.0) -> dict[date, float | None]:
    return {start + timedelta(days=i): value for i in range(n)}


def test_sum_and_mean_over_complete_months():
    daily = days(date(2023, 1, 1), 31 + 28, 2.0)
    s = to_monthly(daily, "sum")
    m = to_monthly(daily, "mean")
    assert [x.month for x in s] == ["2023-01", "2023-02"]
    assert [x.value for x in s] == pytest.approx([62.0, 56.0])
    assert [x.value for x in m] == pytest.approx([2.0, 2.0])


def test_leap_february_needs_29_days():
    daily = days(date(2024, 2, 1), 28)
    assert to_monthly(daily, "sum")[0].value is None
    daily[date(2024, 2, 29)] = 1.0
    assert to_monthly(daily, "sum")[0].value == pytest.approx(29.0)


def test_one_missing_day_makes_the_month_a_gap_never_filled():
    daily = days(date(2023, 1, 1), 31 + 28 + 31)
    daily[date(2023, 2, 10)] = None
    out = to_monthly(daily, "mean")
    assert [x.value for x in out] == [1.0, None, 1.0]
    assert out[1].valid_days == 27 and out[1].days_in_month == 28
    assert gap_runs(out) == [("2023-02", "2023-02")]


def test_gap_runs_merge_contiguous_months_and_trailing_run():
    daily = days(date(2023, 1, 1), 365)
    for d in (date(2023, 3, 5), date(2023, 4, 5), date(2023, 12, 31)):
        daily[d] = None
    assert gap_runs(to_monthly(daily, "sum")) == [("2023-03", "2023-04"), ("2023-12", "2023-12")]


def test_empty_series():
    assert to_monthly({}, "sum") == []


def test_event_flags_keep_unknown_days_unknown():
    assert is_heat_day(35.1, 35.0) is True
    assert is_heat_day(35.0, 35.0) is False  # strictly above
    assert is_frost_day(0.0) is True  # Tmin <= 0 degC
    assert is_frost_day(0.1) is False
    assert is_frost_day(None) is None
    assert as_count(None) is None and as_count(True) == 1.0


def test_frost_days_counted_daily_then_summed_per_month():
    tmin = {date(2023, 7, d): (-1.0 if d <= 3 else 5.0) for d in range(1, 32)}
    counts = {d: as_count(is_frost_day(t)) for d, t in tmin.items()}
    assert to_monthly(counts, "sum")[0].value == 3.0
