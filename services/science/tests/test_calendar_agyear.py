"""Paridade do calendário agrícola (ADR-7): Python e TS passam pelo mesmo arquivo de casos."""

import json
from datetime import date
from pathlib import Path

import pytest

from fieldshift.calendar.agyear import ag_month_index, ag_year_label, ag_year_of

REPO_ROOT = Path(__file__).resolve().parents[3]
CASES_FILE = REPO_ROOT / "packages" / "contracts" / "fixtures" / "agyear-cases.json"


def _cases() -> list[dict]:
    return json.loads(CASES_FILE.read_text(encoding="utf-8"))["cases"]


def test_fixture_has_cases_for_both_conventions():
    cases = _cases()
    assert len(cases) >= 10
    assert {c["label"] for c in cases} == {"single", "split"}
    assert len({c["start_month"] for c in cases}) >= 3


@pytest.mark.parametrize("case", _cases(), ids=lambda c: f"{c['t']}@{c['start_month']}")
def test_fixture_case(case):
    assert ag_year_of(case["t"], case["start_month"]) == case["ag_year"]
    month = int(case["t"][5:7])
    assert ag_month_index(month, case["start_month"]) == case["ag_month_index"]
    assert ag_year_label(case["ag_year"], case["label"]) == case["ag_year_label"]


def test_accepts_date_objects():
    assert ag_year_of(date(2025, 3, 1), 9) == 2024
    assert ag_year_of(date(2025, 9, 1), 9) == 2025


def test_split_label_wraps_century():
    assert ag_year_label(1999, "split") == "1999/00"


@pytest.mark.parametrize("bad", [0, 13, -1])
def test_rejects_invalid_start_month(bad):
    with pytest.raises(ValueError):
        ag_year_of("2024-05", bad)


@pytest.mark.parametrize("bad", ["2024", "2024-13", "24-05-01", "2024/05"])
def test_rejects_invalid_time(bad):
    with pytest.raises(ValueError):
        ag_year_of(bad, 9)


def test_rejects_unknown_label():
    with pytest.raises(ValueError):
        ag_year_label(2024, "season")  # type: ignore[arg-type]
