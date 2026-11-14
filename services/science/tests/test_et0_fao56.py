# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""FAO-56 Penman-Monteith against the worked examples of the FAO-56 text.

Values transcribed from https://www.fao.org/4/x0490e/x0490e07.htm (Example 8) and
https://www.fao.org/4/x0490e/x0490e08.htm (Example 18), checked on 2026-11-14.
"""

from datetime import date

import pytest

from fieldshift.indices.et0 import (
    actual_vapour_pressure_from_rh_minmax,
    et0_fao56_daily,
    extraterrestrial_radiation,
    net_longwave_radiation,
    net_radiation,
    pressure_from_elevation,
    sat_vapour_pressure,
)

# Example 18: Uccle (Brussels), 6 July (J = 187), 50°48'N, 100 m
UCCLE = {"lat_deg": 50.80, "elevation_m": 100.0, "day": date(2025, 7, 6)}
TMAX, TMIN, RHMAX, RHMIN = 21.5, 12.3, 84.0, 63.0
U2 = 2.078  # 10 km/h at 10 m, converted with eq. 47
RS = 22.07  # from sunshine hours (eq. 35), as computed in the example


def test_example_18_intermediate_values():
    assert sat_vapour_pressure(TMAX) == pytest.approx(2.564, abs=5e-4)
    assert sat_vapour_pressure(TMIN) == pytest.approx(1.431, abs=5e-4)
    ea = actual_vapour_pressure_from_rh_minmax(TMIN, TMAX, RHMIN, RHMAX)
    assert ea == pytest.approx(1.409, abs=5e-4)
    assert pressure_from_elevation(100.0) == pytest.approx(100.1, abs=0.05)
    ra = extraterrestrial_radiation(UCCLE["lat_deg"], UCCLE["day"])
    assert ra == pytest.approx(41.09, abs=0.01)
    rso = (0.75 + 2e-5 * 100) * ra
    assert rso == pytest.approx(30.90, abs=0.01)
    assert net_longwave_radiation(TMIN, TMAX, ea, RS, rso) == pytest.approx(3.71, abs=0.01)
    assert net_radiation(tmin_c=TMIN, tmax_c=TMAX, ea_kpa=ea, rs=RS, **UCCLE) == pytest.approx(
        13.28, abs=0.01
    )


def test_example_18_et0_daily():
    """Published result: ET0 = 2.81 + 1.07 = 3.88 ≈ 3.9 mm/day."""
    ea = actual_vapour_pressure_from_rh_minmax(TMIN, TMAX, RHMIN, RHMAX)
    et0 = et0_fao56_daily(
        tmin_c=TMIN, tmax_c=TMAX, ea_kpa=ea, wind_2m=U2, rs=RS,
        pressure_kpa=pressure_from_elevation(100.0), **UCCLE,
    )  # fmt: skip
    assert et0 == pytest.approx(3.88, abs=0.02)


def test_example_8_extraterrestrial_radiation_southern_hemisphere():
    """3 September (J = 246) at 20°S: Ra = 32.2 MJ m-2 day-1 (latitude negative in the south)."""
    assert extraterrestrial_radiation(-20.0, date(2025, 9, 3)) == pytest.approx(32.2, abs=0.05)


def test_polar_night_does_not_crash():
    assert extraterrestrial_radiation(80.0, date(2025, 12, 21)) == pytest.approx(0.0, abs=1e-6)
