"""Guard for the units fixture (ADR-7).

Unit conversion only exists at display time (apps/web/src/lib/units.ts). This test is not
production code: it checks, against an independent reference, that the fixture the TS code
consumes is right — in particular delta_degC x1.8 without the +32.
"""

import json
from pathlib import Path

import pytest

from fieldshift.contracts.common import CANONICAL_UNITS

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE = json.loads(
    (REPO_ROOT / "packages" / "contracts" / "fixtures" / "units-cases.json").read_text(
        encoding="utf-8"
    )
)

# Independent reference (factors exact by definition: 1 in = 25.4 mm; 1 ft = 0.3048 m;
# 1 ac = 4046.8564224 m²; 1 mph = 0.44704 m/s).
IMPERIAL = {
    "degC": ("degF", lambda v: v * 1.8 + 32),
    "delta_degC": ("delta_degF", lambda v: v * 1.8),
    "degC_d": ("degF_d", lambda v: v * 1.8),
    "mm": ("in", lambda v: v / 25.4),
    "mm/d": ("in/d", lambda v: v / 25.4),
    "mm/month": ("in/month", lambda v: v / 25.4),
    "m": ("ft", lambda v: v / 0.3048),
    "ha": ("ac", lambda v: v * 10_000 / 4046.8564224),
    "m/s": ("mph", lambda v: v / 0.44704),
}


def _reference(value: float, unit: str, system: str) -> tuple[float, str]:
    if system == "imperial" and unit in IMPERIAL:
        target, fn = IMPERIAL[unit]
        return fn(value), target
    return value, unit


@pytest.mark.parametrize(
    "case", FIXTURE["cases"], ids=lambda c: f"{c['value']}{c['unit']}->{c['system']}"
)
def test_case_matches_reference(case):
    assert case["unit"] in CANONICAL_UNITS
    value, unit = _reference(case["value"], case["unit"], case["system"])
    assert unit == case["expected_unit"]
    assert abs(value - case["expected_value"]) <= FIXTURE["tolerance"]


def test_delta_degc_never_adds_32():
    deltas = [
        c for c in FIXTURE["cases"] if c["unit"] == "delta_degC" and c["system"] == "imperial"
    ]
    assert any(c["value"] == 0 and c["expected_value"] == 0 for c in deltas)
    for c in deltas:
        assert abs(c["expected_value"] - c["value"] * 1.8) <= FIXTURE["tolerance"]
