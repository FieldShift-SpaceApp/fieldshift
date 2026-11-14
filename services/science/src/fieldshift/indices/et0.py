# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Reference evapotranspiration ET0, FAO-56 Penman-Monteith, daily time step.

Source: Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). Crop evapotranspiration -
Guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56.
https://www.fao.org/4/x0490e/x0490e00.htm (equation numbers below refer to it).

Written in plain Python instead of pyet: pyet 1.5.0 (latest on PyPI, 2026-11-14) requires
pandas < 3.0 and xarray, which conflicts with the stack (pandas 3.1.1). The equations are short
and the tests check them against the FAO-56 worked examples (8 and 18).
"""

from __future__ import annotations

import math
from datetime import date

SOLAR_CONSTANT = 0.0820  # MJ m-2 min-1 (eq. 21)
STEFAN_BOLTZMANN = 4.903e-9  # MJ K-4 m-2 day-1 (eq. 39)
ALBEDO_GRASS = 0.23  # hypothetical grass reference crop (eq. 38)


def sat_vapour_pressure(t_c: float) -> float:
    """e°(T) in kPa (eq. 11)."""
    return 0.6108 * math.exp(17.27 * t_c / (t_c + 237.3))


def actual_vapour_pressure_from_dewpoint(tdew_c: float) -> float:
    """ea in kPa from the dewpoint (eq. 14), the method FAO-56 prefers."""
    return sat_vapour_pressure(tdew_c)


def actual_vapour_pressure_from_rh_minmax(
    tmin_c: float, tmax_c: float, rhmin_pct: float, rhmax_pct: float
) -> float:
    """ea in kPa from RHmax and RHmin (eq. 17)."""
    return (
        sat_vapour_pressure(tmin_c) * rhmax_pct / 100.0
        + sat_vapour_pressure(tmax_c) * rhmin_pct / 100.0
    ) / 2.0


def pressure_from_elevation(elevation_m: float) -> float:
    """Atmospheric pressure in kPa from elevation (eq. 7)."""
    return 101.3 * ((293.0 - 0.0065 * elevation_m) / 293.0) ** 5.26


def extraterrestrial_radiation(lat_deg: float, day: date) -> float:
    """Ra in MJ m-2 day-1 (eqs. 21-25). Southern latitudes are negative."""
    j = day.timetuple().tm_yday
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * j / 365)
    delta = 0.409 * math.sin(2 * math.pi * j / 365 - 1.39)
    x = -math.tan(phi) * math.tan(delta)
    ws = math.acos(max(-1.0, min(1.0, x)))  # clamp: polar day / polar night
    return (
        24
        * 60
        / math.pi
        * SOLAR_CONSTANT
        * dr
        * (ws * math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.sin(ws))
    )


def net_longwave_radiation(
    tmin_c: float, tmax_c: float, ea_kpa: float, rs: float, rso: float
) -> float:
    """Rnl in MJ m-2 day-1 (eq. 39). Rs/Rso is capped at 1.0 as FAO-56 requires."""
    ratio = min(rs / rso, 1.0) if rso > 0 else 1.0
    tk4 = ((tmax_c + 273.16) ** 4 + (tmin_c + 273.16) ** 4) / 2
    return STEFAN_BOLTZMANN * tk4 * (0.34 - 0.14 * math.sqrt(ea_kpa)) * (1.35 * ratio - 0.35)


def net_radiation(
    *, tmin_c: float, tmax_c: float, ea_kpa: float, rs: float, lat_deg: float, elevation_m: float,
    day: date,
) -> float:  # fmt: skip
    """Rn in MJ m-2 day-1 (eqs. 37, 38, 39, 40)."""
    ra = extraterrestrial_radiation(lat_deg, day)
    rso = (0.75 + 2e-5 * elevation_m) * ra
    rns = (1 - ALBEDO_GRASS) * rs
    return rns - net_longwave_radiation(tmin_c, tmax_c, ea_kpa, rs, rso)


def et0_fao56_daily(
    *,
    tmin_c: float,
    tmax_c: float,
    ea_kpa: float,
    wind_2m: float,
    rs: float,
    pressure_kpa: float,
    lat_deg: float,
    elevation_m: float,
    day: date,
) -> float:
    """ET0 in mm day-1 (eq. 6), with G = 0 for the daily step (eq. 42) and Tmean from eq. 9.

    `rs` is incoming shortwave radiation in MJ m-2 day-1 (NASA POWER ALLSKY_SFC_SW_DWN, community
    AG). `pressure_kpa` is the surface pressure; use `pressure_from_elevation` if it is unknown.
    """
    tmean = (tmax_c + tmin_c) / 2
    es = (sat_vapour_pressure(tmax_c) + sat_vapour_pressure(tmin_c)) / 2  # eq. 12
    slope = 4098 * sat_vapour_pressure(tmean) / (tmean + 237.3) ** 2  # eq. 13
    gamma = 0.000665 * pressure_kpa  # eq. 8
    rn = net_radiation(
        tmin_c=tmin_c, tmax_c=tmax_c, ea_kpa=ea_kpa, rs=rs, lat_deg=lat_deg,
        elevation_m=elevation_m, day=day,
    )  # fmt: skip
    g = 0.0
    numerator = 0.408 * slope * (rn - g) + gamma * 900 / (tmean + 273) * wind_2m * (es - ea_kpa)
    return numerator / (slope + gamma * (1 + 0.34 * wind_2m))
