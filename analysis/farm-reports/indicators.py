# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""From satellite measurements of one farm to Table 1 levels and the satellite-side NM range (pure functions).

Every rule of the norm comes from analysis/zarcnm-precheck/zarcnm_rules.py (IN SPA/MAPA 2/2025 and Portaria
SPA/MAPA 209/2026, transcribed there with item numbers). What is decided here, and stated as a choice:
- C (straw cover, Table 1 row 5): median Embrapa-ruler cover of the farm's observed no-green cropland pixels; the
  ruler's RMSE (8.3 points) widens the level range, and a cover >= 80% (the ruler's saturation) reads "3 or 4".
- T (years without tillage, row 4): complete years since the last spring with a bare-soil signature on the farm
  (>= SIGNATURE_SHARE of its clear cropland probable bare soil in one scene); the lower end of the range also
  treats every unobserved year after that as a possible tillage year.
- D (diversity, row 6): the level reached by at least half of the farm's classified cropland pixels (weighted
  median); "4" is only an upper end when at least half of the pixels have the cover durations of level 4
  (4 species cannot be counted from NDVI and need the farmer's declaration).
- Contour (item 3.2.1-I): never observable; the range assumes it is confirmed (upper end) and says so.
- Consecutive soybean (item 3.2.1-II): a fallow winter on at least half of the farm's pixels triggers the literal
  reading (NM1) at the lower end only, as analysis/zarcnm-precheck keeps both readings.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "zarcnm-precheck"))
import zarcnm_rules as zr  # noqa: E402

RULER_RMSE = 8.3  # points, the fit of analysis/residue-landsat/embrapa.py to Embrapa Doc 454 Table 2
RULER_SATURATION = 80.0  # Embrapa Doc 454 p. 29
SIGNATURE_SHARE = 0.25  # share of the farm's clear cropland that is probable bare soil in one scene
SIGNATURE_SENSITIVITY = (0.10, 0.50)
MIN_OBSERVED_SHARE = 0.25  # of the farm's cropland pixels, for C to be read
CURRENT_YEAR = 2026
SOIL_BEST = 4


def c_range(cover_median: float | None) -> tuple[int, int] | None:
    if cover_median is None:
        return None
    lo = zr.level_straw_cover(max(0.0, cover_median - RULER_RMSE))
    hi = zr.level_straw_cover(min(100.0, cover_median + RULER_RMSE))
    if cover_median >= RULER_SATURATION:
        lo, hi = min(lo, 3), 4
    return lo, hi


def t_range(
    last_signature: int | None, first_observed: int | None, unobserved_after: list[int]
) -> tuple[int, int, int, int] | None:
    """(level_lo, level_hi, years_lo, years_hi). Years count complete years after the signature's spring."""
    if first_observed is None:
        return None
    start = last_signature if last_signature is not None else first_observed - 1
    years_hi = max(0, CURRENT_YEAR - start - 1)
    latest_doubt = max([start, *unobserved_after])
    years_lo = max(0, CURRENT_YEAR - latest_doubt - 1)
    return (
        zr.level_years_without_tillage(years_lo),
        zr.level_years_without_tillage(years_hi),
        years_lo,
        years_hi,
    )


def d_range(level_shares: dict | None, l4_possible_share: float | None) -> tuple[int, int] | None:
    if not level_shares:
        return None
    cum = 0.0
    med = 1
    for lv in (3, 2, 1):  # level reached by at least half of the pixels
        cum += level_shares.get(str(lv), 0.0)
        if cum >= 0.5:
            med = lv
            break
    hi = 4 if (med == 3 and (l4_possible_share or 0) >= 0.5) else med
    return med, hi


def nm_range(
    t: tuple[int, int] | None,
    c: tuple[int, int] | None,
    d: tuple[int, int] | None,
    slope_mean_pct: float | None,
    fallow_majority: bool,
    soil_level: int = SOIL_BEST,
) -> dict | None:
    """NM range from every combination of the observable levels, the three soil indicators at `soil_level`.

    Upper end: contour confirmed, the non-literal reading of "consecutive soybean". Lower end: contour still
    confirmed (otherwise every field on >= 3% would be NM1 and the range would say nothing), the literal reading
    when the farm's winters were mostly fallow.
    """
    if t is None or c is None or d is None:
        return None
    nms_hi, nms_lo, locks = [], [], set()
    for tl, cl, dl in itertools.product(range(t[0], t[1] + 1), range(c[0], c[1] + 1), range(d[0], d[1] + 1)):
        levels = {"V%": soil_level, "Ca": soil_level, "m%": soil_level, "T": tl, "C": cl, "D": dl}
        ok = zr.SiteFacts(slope_pct=slope_mean_pct, contour_share=1.0, useful_soil_depth_cm=None)
        hi = zr.classify(levels, ok)
        nms_hi.append(hi.nm)
        lo = zr.classify(levels, zr.SiteFacts(slope_pct=slope_mean_pct, contour_share=1.0, consecutive_soybean=True))
        nms_lo.append(lo.nm if fallow_majority else hi.nm)
        locks.update(lk.citation for lk in (lo.locks if fallow_majority else hi.locks))
    return {
        "nm_min": min(nms_lo),
        "nm_max": max(nms_hi),
        "locks": sorted(locks),
        "contour_to_confirm": slope_mean_pct is not None and slope_mean_pct >= 3,
    }


def band_label(r: dict | None) -> str:
    if r is None:
        return "not assessed"
    a, b = r["nm_min"], r["nm_max"]
    return f"NM{a}" if a == b else f"NM{a}-NM{b}"
