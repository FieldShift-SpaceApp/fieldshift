# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Daily soil water balance per crop sequence, ported from FieldShift team research (script 29, unchanged formulas).

ET0: FAO-56 Penman-Monteith (eq. 6) from daily NASA POWER (Tmax, Tmin, Tmean, relative humidity, wind at 2 m, solar radiation).
Rain: daily GPM IMERG V07.
Bucket: one layer with available water capacity AWC = 75 mm (Franchini et al. 2012);
  ETc = Kc x ET0; ETa = ETc x min(1, A / (0.5 x AWC)); water above AWC leaves as drainage/runoff.
Kc in three stages (vegetative / flowering-grain fill / maturation): soybean 0.5/1.15/0.5 (Farias et al. 2001),
  maize 0.7/1.2/0.6 (Embrapa 2009), wheat 0.75/0.85/0.65 (Cunha et al. 2001), as cited by Battisti, Sentelhas & Pilau (2012);
  canola 0.35/1.0/0.35 and black oat 0.3/1.15/0.25 (FAO-56 Table 12). Fallow with straw: Kc 0.3 (assumption).
SOWING DATES AND STAGE LENGTHS ARE ASSUMPTIONS TO BE VALIDATED BY AN AGRONOMIST (tables CROPS and SEQUENCES).
Indicator: water satisfaction index WSI = ETa / ETc in the critical stage (flowering-grain fill).
"Water short" = WSI < 0.70 (Franchini et al. 2012 threshold for no-till soybean).
"""

import datetime as dt
import math

import numpy as np
import pandas as pd

ALTITUDE_M = 410.0  # Cruz Alta altitude, used for all seven municipalities (declared limit)
AWC_MM = 75.0

# crop: (Kc vegetative, Kc critical, Kc maturation, days vegetative, days critical, days maturation)
CROPS = {
    "soy": (0.5, 1.15, 0.5, 45, 55, 30),
    "soy_late": (0.5, 1.15, 0.5, 40, 50, 30),
    "maize": (0.7, 1.2, 0.6, 60, 45, 35),
    "wheat": (0.75, 0.85, 0.65, 60, 45, 35),
    "canola": (0.35, 1.0, 0.35, 55, 55, 40),
    "oat_cover": (0.3, 1.15, 0.25, 40, 60, 20),
    "autumn_cover": (0.3, 1.0, 1.0, 30, 30, 0),
}
# sequences: list of (crop, month, day of sowing) inside the agricultural year Apr(Y-1) -> Mar(Y)   [ASSUMPTIONS]
SEQUENCES = {
    "soy after winter fallow": [("soy", 11, 1)],
    "soy after wheat": [("wheat", 6, 15), ("soy_late", 11, 20)],
    "early maize after oat cover": [("oat_cover", 5, 1), ("maize", 9, 1)],
}
SUMMER = {"soy", "soy_late", "maize"}


def et0_penman_monteith(row: pd.Series, lat: float) -> float:
    tx, tn, tm = row.power_tmax_c, row.power_tmin_c, row.power_tmean_c
    rh, u2, rs = row.power_rh_pct, row.power_wind2m_m_s, row.power_srad_mj_m2
    doy = row.name.timetuple().tm_yday
    pres = 101.3 * ((293 - 0.0065 * ALTITUDE_M) / 293) ** 5.26
    gamma = 0.000665 * pres

    def es(t: float) -> float:
        return 0.6108 * math.exp(17.27 * t / (t + 237.3))

    es_mean = (es(tx) + es(tn)) / 2
    ea = es_mean * rh / 100
    delta = 4098 * es(tm) / (tm + 237.3) ** 2
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    decl = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(-math.tan(phi) * math.tan(decl))
    ra = 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(decl) + math.cos(phi) * math.cos(decl) * math.sin(ws))
    rso = (0.75 + 2e-5 * ALTITUDE_M) * ra
    rns = 0.77 * rs
    rnl = (
        4.903e-9
        * ((tx + 273.16) ** 4 + (tn + 273.16) ** 4)
        / 2
        * (0.34 - 0.14 * math.sqrt(max(ea, 0.01)))
        * (1.35 * min(rs / rso, 1) - 0.35)
    )
    rn = rns - rnl
    return max(0.0, (0.408 * delta * rn + gamma * 900 / (tm + 273) * u2 * (es_mean - ea)) / (delta + gamma * (1 + 0.34 * u2)))


def crop_plan(seq: list, year: int):
    """Per day of the agricultural year (1 Apr Y-1 .. 31 Mar Y): Kc, living fraction (0-1), critical-stage crop name or ''."""
    days = pd.date_range(dt.date(year - 1, 4, 1), dt.date(year, 3, 31))
    kc = np.full(len(days), 0.3)
    alive = np.zeros(len(days))
    crit = np.array([""] * len(days), dtype=object)
    for crop, month, day in seq:
        k1, k2, k3, n1, n2, n3 = CROPS[crop]
        s = (dt.date(year - 1, month, day) - dt.date(year - 1, 4, 1)).days
        for i in range(s, min(len(days), s + n1 + n2 + n3)):
            t = i - s
            if t < n1:
                kc[i] = k1 + (k2 - k1) * max(0, (t - n1 * 0.5)) / (n1 * 0.5)
                alive[i] = min(1, t / (n1 * 0.8))
            elif t < n1 + n2:
                kc[i] = k2
                alive[i] = 1
                crit[i] = crop
            else:
                kc[i] = k2 + (k3 - k2) * (t - n1 - n2) / max(n3, 1)
                alive[i] = 1
    return days, kc, alive, crit


def run_sequence(d: pd.DataFrame, seq: list, awc: float = AWC_MM) -> pd.Series:
    """Summer-crop WSI per harvest year (2001-2025; years with >10% missing rain are skipped). d: daily frame with et0."""
    store = awc * 0.7
    out = {}
    for year in range(2001, 2026):
        days, kc, _alive, crit = crop_plan(seq, year)
        sub = d.reindex(days)
        rain = sub.imerg_precip_mm.values
        et0 = sub.et0.values
        if np.isnan(rain).mean() > 0.1:
            store = awc * 0.7
            continue
        rain = np.nan_to_num(rain)
        etc = kc * et0
        eta = np.zeros(len(days))
        for i in range(len(days)):
            ks = min(1, store / (0.5 * awc))
            eta[i] = etc[i] * ks
            store = store + rain[i] - eta[i]
            if store > awc:
                store = awc
            store = max(store, 0)
        for c in set(crit) - {""}:
            if c in SUMMER:
                m = crit == c
                out[year] = eta[m].sum() / etc[m].sum()
    return pd.Series(out, name="wsi_summer")
