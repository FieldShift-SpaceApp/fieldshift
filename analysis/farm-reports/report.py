# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Per-farm indicators, satellite-side NM range, municipal statistics, map and one example report.

    python -I report.py [--ibge 4306106] [--raw DIR] [--results DIR] [--name "Cruz Alta (RS)"]

Reads the raw folder written by fetch_car.py, grids.py, scenes.py and winter.py. Writes to results/ only
aggregates, the map and one anonymous example (no CAR code, no outline, no coordinates). The per-farm table
stays in the raw folder (farm_results.json), never committed.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import platform
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import PolyCollection  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from rasterio.warp import transform_geom  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import embrapa_ruler  # noqa: E402
import indicators as ind  # noqa: E402
from common import (  # noqa: E402
    DEFAULT_IBGE,
    DST_CRS,
    NDTI_BARE,
    NDVI_GREEN,
    ROOT,
    FarmIndex,
    area,
    raw_dir,
    read_json,
    write_json,
)

HERE = Path(__file__).resolve().parent
SUBSIDY = ind.zr.SUBSIDY_PCT_SOY
SERIES_MIN_FARM_PIXELS = 10  # 60 m pixels of the farm's cropland clear in a scene for it to count
SERIES_MIN_FARM_SHARE = 0.5  # and at least half of the farm's cropland clear
BANDS_ORDER = ["NM4", "NM3-NM4", "NM3", "NM2-NM4", "NM2-NM3", "NM2", "NM1-NM4", "NM1-NM3", "NM1-NM2", "NM1"]
CEIL_COLORS = {4: "#1f6f4a", 3: "#7fb36a", 2: "#e3b23c", 1: "#a3462b", 0: "#cfcdc6"}
INK, MUTED = "#0b0b0b", "#6b6a66"
ATTRIBUTION = (
    "Data: NASA/USGS Landsat Collection 2 (TM, ETM+, OLI, OLI-2); NASA HLS v2.0 (L30, S30); NASADEM (NASA JPL); "
    "property outlines: CAR/SICAR, Serviço Florestal Brasileiro; cropland: ESA WorldCover 2021 (CC BY 4.0). "
    "Read via Microsoft Planetary Computer."
)


# --------------------------------------------------------------------------------------------------------------
# measurements per farm
# --------------------------------------------------------------------------------------------------------------


def straw_now(raw: Path, fi: FarmIndex) -> dict:
    """Per farm: share of cropland observed with no green, median Embrapa cover, share probable bare soil.
    Most recent window first (1 Oct - 15 Nov 2026); farms not observed then fall back to 1 Oct - 30 Nov 2025."""
    index = read_json(raw / "now" / "index.json")
    out = {}
    windows = {}
    for year in (2026, 2025):
        ids = [m["id"] for m in index if m.get("used") and m["date"].startswith(str(year))]
        windows[year] = sorted({m["date"] for m in index if m.get("used") and m["date"].startswith(str(year))})
        if not ids:
            continue
        ndvi = np.stack([np.load(raw / "now" / f"{i}.npz")["ndvi"] for i in ids]).astype("float32")
        ndti = np.stack([np.load(raw / "now" / f"{i}.npz")["ndti"] for i in ids]).astype("float32")
        nog = ndvi < NDVI_GREEN  # NaN compares False
        ndti_nog = np.where(nog, ndti, np.nan)
        with np.errstate(all="ignore"), __import__("warnings").catch_warnings():
            __import__("warnings").simplefilter("ignore", RuntimeWarning)
            med_ndti = np.nanmedian(ndti_nog, axis=0)
        observed = np.isfinite(med_ndti)
        clear_any = np.isfinite(ndvi).any(0)
        cov = np.where(observed, embrapa_ruler.cover(np.where(observed, med_ndti, 0)), np.nan)
        lab, n = fi.lab, fi.n
        n_crop = np.bincount(lab, minlength=n)
        n_obs = np.bincount(lab, weights=observed.astype(float), minlength=n)
        n_clear = np.bincount(lab, weights=clear_any.astype(float), minlength=n)
        n_bare = np.bincount(lab, weights=(observed & (med_ndti < NDTI_BARE)).astype(float), minlength=n)
        n_lt30 = np.bincount(lab, weights=(observed & (cov < 30)).astype(float), minlength=n)
        n_sat = np.bincount(lab, weights=(observed & (cov >= ind.RULER_SATURATION)).astype(float), minlength=n)
        order = np.argsort(lab, kind="stable")
        bounds = np.searchsorted(lab[order], np.arange(n + 1))
        cov_sorted = cov[order]
        for k in range(n):
            if k in out or n_crop[k] == 0:
                continue
            share = n_obs[k] / n_crop[k]
            if share < ind.MIN_OBSERVED_SHARE:
                continue
            c = cov_sorted[bounds[k] : bounds[k + 1]]
            c = c[np.isfinite(c)]
            out[k] = {
                "year": year,
                "observed_share": round(float(share), 3),
                "clear_share": round(float(n_clear[k] / n_crop[k]), 3),
                "cover_median_pct": round(float(np.median(c)), 1),
                "bare_share": round(float(n_bare[k] / n_obs[k]), 3),
                "straw_share": round(float(1 - n_bare[k] / n_obs[k]), 3),
                "c_lt30_share": round(float(n_lt30[k] / n_obs[k]), 3),
                "c_saturated_share": round(float(n_sat[k] / n_obs[k]), 3),
            }
    return {"farms": out, "dates": windows}


def bare_series(raw: Path, fi: FarmIndex) -> dict:
    index = read_json(raw / "series" / "index.json")
    used = [m for m in index if m.get("used")]
    crop = fi.count()
    by_year = defaultdict(list)
    for m in used:
        z = np.load(raw / "series" / f"{m['id']}.npz")
        by_year[int(m["date"][:4])].append({k: z[k].astype(float) for k in z.files})
    years = sorted(by_year)
    n = fi.n
    share = {key: np.full((len(years), n), np.nan) for key in ("bare", "bare_004", "bare_010")}
    for yi, y in enumerate(years):
        for key in share:
            best = np.full(n, np.nan)
            for s in by_year[y]:
                ok = (s["clear"] >= SERIES_MIN_FARM_PIXELS) & (
                    s["clear"] >= SERIES_MIN_FARM_SHARE * np.maximum(crop, 1)
                )
                v = np.where(ok, s[key] / np.maximum(s["clear"], 1), np.nan)
                best = np.fmax(best, v)
            share[key][yi] = best
    return {"years": years, "share": share, "scenes_used": len(used), "scenes_found": len(index)}


def t_inputs(years: list[int], share_col: np.ndarray, thr: float):
    obs = np.isfinite(share_col)
    if not obs.any():
        return None, None, []
    yrs = np.array(years)
    observed_years = yrs[obs]
    sig = yrs[obs & (np.nan_to_num(share_col) >= thr)]
    last = int(sig.max()) if sig.size else None
    start = last if last is not None else int(observed_years.min()) - 1
    # The current spring is read by C (straw before sowing); only complete past years count as doubts for T.
    unobserved_after = [y for y in range(start + 1, ind.CURRENT_YEAR) if y not in set(observed_years.tolist())]
    return last, int(observed_years.min()), unobserved_after


def slope_per_farm(raw: Path, fi: FarmIndex) -> dict:
    z = np.load(raw / "static30.npz")
    s = z["slope30"]
    sl = s.ravel()[fi.idx]
    ok = np.isfinite(sl)
    cnt = np.bincount(fi.lab, weights=ok.astype(float), minlength=fi.n)
    tot = np.bincount(fi.lab, weights=np.where(ok, sl, 0), minlength=fi.n)
    ge3 = np.bincount(fi.lab, weights=(ok & (sl >= 3)).astype(float), minlength=fi.n)
    return {
        k: {"slope_mean_pct": round(float(tot[k] / cnt[k]), 2), "slope_ge3_share": round(float(ge3[k] / cnt[k]), 3)}
        for k in range(fi.n)
        if cnt[k] > 0
    }


# --------------------------------------------------------------------------------------------------------------
# assemble
# --------------------------------------------------------------------------------------------------------------


def assemble(raw: Path) -> tuple[list[dict], dict]:
    farms = read_json(raw / "farms.json")
    fi30 = FarmIndex(raw / "farm_idx30.npz")
    fi60 = FarmIndex(raw / "farm_idx60.npz")
    now = straw_now(raw, fi30)
    ser = bare_series(raw, fi60)
    slope = slope_per_farm(raw, fi30)
    win = {w["farm"]: w for w in read_json(raw / "winter_farms.json")}
    years = ser["years"]
    out = []
    for f in farms:
        k = f["farm"]
        r = dict(f)
        r["has_cropland"] = f["cropland_pixels_30m"] > 0
        sn = now["farms"].get(k)
        r["straw_now"] = sn
        r["slope"] = slope.get(k)
        col = ser["share"]["bare"][:, k]
        last, first, unobs = t_inputs(years, col, ind.SIGNATURE_SHARE)
        r["bare_series"] = {
            "years_observed": int(np.isfinite(col).sum()),
            "first_observed": first,
            "last_signature_year": last,
            "unobserved_years_after": unobs,
            "last_signature_year_thr010": t_inputs(years, col, 0.10)[0],
            "last_signature_year_thr050": t_inputs(years, col, 0.50)[0],
            "last_signature_year_ndti004": t_inputs(years, ser["share"]["bare_004"][:, k], ind.SIGNATURE_SHARE)[0],
            "last_signature_year_ndti010": t_inputs(years, ser["share"]["bare_010"][:, k], ind.SIGNATURE_SHARE)[0],
            "share_by_year": {
                str(y): (None if np.isnan(v) else round(float(v), 3)) for y, v in zip(years, col, strict=True)
            },
        }
        w = win.get(k, {})
        r["winter"] = {
            "fingerprint_2020_2026": w.get("fingerprint_2020_2026"),
            "diversity_level_shares": w.get("diversity_level_shares"),
            "level4_possible_share": w.get("level4_possible_share"),
            "fallow_winter_share": w.get("fallow_winter_share"),
        }
        fp = w.get("fingerprint_2020_2026") or ""
        r["winter"]["winter_crops_2020_2026"] = sum(1 for ch in fp if ch in "TCO")
        r["winter"]["winter_paths_2020_2026"] = sorted({ch for ch in fp if ch in "TCPO"})
        tr = ind.t_range(last, first, unobs) if r["has_cropland"] else None
        cr = ind.c_range(sn["cover_median_pct"]) if sn else None
        dr = ind.d_range(w.get("diversity_level_shares"), w.get("level4_possible_share"))
        fallow = (w.get("fallow_winter_share") or 0) >= 0.5
        sm = r["slope"]["slope_mean_pct"] if r["slope"] else None
        r["levels"] = {
            "T": None if tr is None else {"lo": tr[0], "hi": tr[1], "years_lo": tr[2], "years_hi": tr[3]},
            "C": None if cr is None else {"lo": cr[0], "hi": cr[1]},
            "D": None if dr is None else {"lo": dr[0], "hi": dr[1]},
        }
        rng = ind.nm_range(None if tr is None else tr[:2], cr, dr, sm, fallow) if r["has_cropland"] else None
        rng3 = ind.nm_range(None if tr is None else tr[:2], cr, dr, sm, fallow, soil_level=3) if rng else None
        r["nm_if_soil_level4"] = rng
        r["nm_if_soil_level3"] = rng3
        r["band"] = ind.band_label(rng) if r["has_cropland"] else "no cropland"
        missing = [x for x, v in (("T", tr), ("C", cr), ("D", dr)) if v is None]
        r["not_assessed_reason"] = (
            None if rng or not r["has_cropland"] else "missing satellite indicator(s): " + ", ".join(missing)
        )
        out.append(r)
    meta = {
        "now_dates": {str(k): v for k, v in now["dates"].items()},
        "series_years": years,
        "series_scenes_used": ser["scenes_used"],
        "series_scenes_found": ser["scenes_found"],
    }
    return out, meta


# --------------------------------------------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------------------------------------------


def stats(rows: list[dict]) -> dict:
    def agg(sel):
        return {
            "farms": len(sel),
            "declared_area_ha": round(sum(r["area_declared_ha"] for r in sel)),
            "cropland_ha": round(sum(r["cropland_ha"] for r in sel)),
        }

    crop = [r for r in rows if r["has_cropland"]]
    assessed = [r for r in crop if r["nm_if_soil_level4"]]
    by_band = {b: agg([r for r in rows if r["band"] == b]) for b in sorted({r["band"] for r in rows}, key=_band_key)}
    by_ceiling = {f"NM{c}": agg([r for r in assessed if r["nm_if_soil_level4"]["nm_max"] == c]) for c in (4, 3, 2, 1)}
    by_size = {}
    for sc in ("small", "medium", "large"):
        sel = [r for r in rows if r["size_class"] == sc]
        by_size[sc] = {
            "all": agg(sel),
            "assessed": agg([r for r in sel if r["nm_if_soil_level4"]]),
            "by_ceiling": {
                f"NM{c}": agg([r for r in sel if r["nm_if_soil_level4"] and r["nm_if_soil_level4"]["nm_max"] == c])
                for c in (4, 3, 2, 1)
            },
            "ready_nm3_plus_strict": agg(
                [r for r in sel if r["nm_if_soil_level4"] and r["nm_if_soil_level4"]["nm_min"] >= 3]
            ),
        }
    ready_strict = [r for r in assessed if r["nm_if_soil_level4"]["nm_min"] >= 3]
    ready_loose = [r for r in assessed if r["nm_if_soil_level4"]["nm_max"] >= 3]
    ready_soil3 = [r for r in assessed if r["nm_if_soil_level3"] and r["nm_if_soil_level3"]["nm_min"] >= 3]

    def dist(key):
        c = Counter()
        for r in assessed:
            lv = r["levels"][key]
            c[f"{lv['lo']}" if lv["lo"] == lv["hi"] else f"{lv['lo']}-{lv['hi']}"] += 1
        return dict(sorted(c.items()))

    last_sig = Counter()
    for r in crop:
        y = r["bare_series"]["last_signature_year"]
        if r["bare_series"]["first_observed"] is None:
            last_sig["no observation"] += 1
        elif y is None:
            last_sig["never (in the observed years)"] += 1
        else:
            last_sig[f"{(y // 5) * 5}-{(y // 5) * 5 + 4}"] += 1
    contour = [r for r in assessed if r["nm_if_soil_level4"]["contour_to_confirm"]]
    fp = Counter(r["winter"]["fingerprint_2020_2026"] for r in assessed)
    return {
        "farms_active": len(rows),
        "farms_with_cropland": len(crop),
        "farms_assessed": len(assessed),
        "farms_not_assessed": Counter(r["not_assessed_reason"] for r in crop if not r["nm_if_soil_level4"]),
        "by_band_if_soil_level4": by_band,
        "by_ceiling_if_soil_level4": by_ceiling,
        "satellite_ready_nm3_plus": {
            "strict_whole_range_nm3_plus_if_soil_level4": agg(ready_strict),
            "loose_upper_end_nm3_plus_if_soil_level4": agg(ready_loose),
            "strict_if_soil_level3": agg(ready_soil3),
            "note": "if the three soil tests (V%, Ca, m%) come back at the stated level and contour sowing is "
            "confirmed where the mean slope is >= 3%; never a final NM",
        },
        "by_size_class": by_size,
        "indicator_level_distribution_assessed": {"T": dist("T"), "C": dist("C"), "D": dist("D")},
        "last_bare_signature_period_cropland_farms": dict(sorted(last_sig.items())),
        "contour_to_confirm_farms": len(contour),
        "cropland_slope_ge3_share_median": round(
            float(np.median([r["slope"]["slope_ge3_share"] for r in assessed if r["slope"]])), 3
        )
        if assessed
        else None,
        "top_fingerprints_2020_2026": dict(fp.most_common(8)),
    }


def _band_key(b: str):
    return (BANDS_ORDER.index(b) if b in BANDS_ORDER else 99, b)


# --------------------------------------------------------------------------------------------------------------
# map
# --------------------------------------------------------------------------------------------------------------


def rings_utm(geom: dict) -> list[np.ndarray]:
    g = transform_geom("EPSG:4326", DST_CRS, geom)
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    return [np.asarray(p[0])[:, :2] / 1000.0 for p in polys]


def draw_map(rows, geoms, st, name, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 10.6), dpi=130)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    order = sorted(range(len(rows)), key=lambda k: -rows[k]["area_declared_ha"])  # small farms drawn on top
    polys, colors = [], []
    for k in order:
        r = rows[k]
        rng = r["nm_if_soil_level4"]
        if not r["has_cropland"]:
            col = "#ffffff"
        else:
            col = CEIL_COLORS[rng["nm_max"]] if rng else CEIL_COLORS[0]
        for ring in rings_utm(geoms[k]):
            polys.append(ring)
            colors.append(col)
    ax.add_collection(PolyCollection(polys, facecolors=colors, edgecolors="#ffffff", linewidths=0.25))
    mun = ROOT / "data" / "dev" / "dev-cruz-alta" / "ibge" / f"malha_municipio_{DEFAULT_IBGE}_2022.geojson"
    if mun.exists() and name.startswith("Cruz Alta"):
        g = json.loads(mun.read_text(encoding="utf-8"))
        g = g["features"][0]["geometry"] if "features" in g else g
        for ring in rings_utm(g):
            ax.plot(ring[:, 0], ring[:, 1], color=INK, lw=0.9)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    x0, x1 = ax.get_xlim()
    y0, _ = ax.get_ylim()
    ax.plot([x0 + 1, x0 + 11], [y0 + 1, y0 + 1], color=INK, lw=2)
    ax.text(x0 + 6, y0 + 1.6, "10 km", ha="center", fontsize=8, color=INK)
    bc = st["by_ceiling_if_soil_level4"]
    labels = {
        4: "up to NM4",
        3: "up to NM3",
        2: "up to NM2",
        1: "NM1 only",
    }
    handles = [
        Patch(
            color=CEIL_COLORS[c],
            label=f"{labels[c]}: {bc[f'NM{c}']['farms']} farms, {bc[f'NM{c}']['cropland_ha']:,} ha cropland",
        )
        for c in (4, 3, 2, 1)
    ]
    na = st["farms_with_cropland"] - st["farms_assessed"]
    handles.append(Patch(color=CEIL_COLORS[0], label=f"cropland, not enough satellite data: {na} farms"))
    handles.append(
        Patch(
            facecolor="#ffffff",
            edgecolor="#bbbbbb",
            label=f"no cropland in the mask: {st['farms_active'] - st['farms_with_cropland']} farms",
        )
    )
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(0, -0.01), ncol=2, fontsize=8.2, frameon=False)
    fig.suptitle(
        f"{name}: best satellite-side ZarcNM level of each rural property (CAR)",
        x=0.05,
        y=0.975,
        ha="left",
        fontsize=13.5,
        color=INK,
        weight="bold",
    )
    fig.text(
        0.05,
        0.945,
        "Highest management level (NM) the satellite indicators allow if the 3 soil tests are favourable and contour "
        "sowing is confirmed.\nPre-check, not a certificate: the official level comes only from Embrapa's SINM "
        "(IN SPA/MAPA 2/2025). No names or CAR codes.",
        fontsize=8.6,
        color=MUTED,
        va="top",
    )
    fig.text(0.05, 0.012, ATTRIBUTION, fontsize=6.4, color=MUTED, wrap=True)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.91, bottom=0.12)
    fig.savefig(path, facecolor=fig.get_facecolor())
    plt.close(fig)


# --------------------------------------------------------------------------------------------------------------
# example report (one anonymous farm)
# --------------------------------------------------------------------------------------------------------------


def pick_example(rows, st) -> dict | None:
    """Rule: medium farm, all three satellite indicators read, C read in 2026, upper end equal to the most common
    upper end among assessed farms; the one closest to the median cropland area of those candidates."""
    bc = st["by_ceiling_if_soil_level4"]
    modal = max(bc, key=lambda b: bc[b]["farms"])
    cand = [
        r
        for r in rows
        if r["size_class"] == "medium"
        and r["nm_if_soil_level4"]
        and f"NM{r['nm_if_soil_level4']['nm_max']}" == modal
        and r["straw_now"]
        and r["straw_now"]["year"] == 2026
    ]
    if not cand:
        cand = [r for r in rows if r["nm_if_soil_level4"]]
    if not cand:
        return None
    med = float(np.median([r["cropland_ha"] for r in cand]))
    return min(cand, key=lambda r: (abs(r["cropland_ha"] - med), r["farm"]))


def example_public(r: dict, name: str) -> dict:
    """What the example shows; rounded so it does not point to one CAR record."""
    lv = r["levels"]
    sn = r["straw_now"]
    bs = r["bare_series"]
    rng = r["nm_if_soil_level4"]

    def lvl(x):
        return f"level {x['lo']}" if x["lo"] == x["hi"] else f"level {x['lo']}-{x['hi']}"

    return {
        "municipality": name,
        "size_class": r["size_class"],
        "declared_area_ha_rounded": int(round(r["area_declared_ha"], -1)),
        "cropland_ha_rounded": int(round(r["cropland_ha"], -1)),
        "satellite_side_nm_range_if_soil_level4": ind.band_label(rng),
        "satellite_side_nm_range_if_soil_level3": ind.band_label(r["nm_if_soil_level3"]),
        "subsidy_pct_soy_2026_pilot": {f"NM{k}": v for k, v in SUBSIDY.items()},
        "contour_note": "and contour sowing confirmed"
        if rng["contour_to_confirm"]
        else "slope below 3%: no contour rule",
        "indicators": [
            {
                "code": "T",
                "name": "Years without tillage",
                "status": "satellite",
                "level": lvl(lv["T"]),
                "evidence": (
                    (
                        f"last spring with a bare-soil signature: {bs['last_signature_year']}"
                        if bs["last_signature_year"]
                        else "no spring with a bare-soil signature"
                    )
                    + f" in {bs['years_observed']} springs observed since {bs['first_observed']} (NASA/USGS Landsat, NASA HLS); "
                    f"{lv['T']['years_lo']}-{lv['T']['years_hi']} complete years without tillage (the lower figure counts "
                    "years with no clear scene as possible tillage)"
                ),
            },
            {
                "code": "C",
                "name": "Straw cover before sowing",
                "status": "satellite",
                "level": lvl(lv["C"]),
                "evidence": (
                    f"{sn['year']} Oct-Nov (NASA HLS / Landsat): median cover {sn['cover_median_pct']:.0f}% (Embrapa "
                    f"Doc 454 ruler); straw {100 * sn['straw_share']:.0f}%, probable bare soil "
                    f"{100 * sn['bare_share']:.0f}% of the field area seen without green canopy "
                    f"({100 * sn['observed_share']:.0f}% of the cropland)"
                ),
            },
            {
                "code": "D",
                "name": "Crop diversity (last 3 years)",
                "status": "satellite + farmer's declaration",
                "level": lvl(lv["D"]),
                "evidence": (
                    f"winter fingerprint 2020-2026: {r['winter']['fingerprint_2020_2026']} (T wheat-like, C cover crop, "
                    f"P fallow, O other); summer crop assumed soybean; level 4 also needs 4 species declared"
                ),
            },
            {
                "code": "slope",
                "name": "Slope (contour rule)",
                "status": "satellite + field check",
                "level": "contour sowing to confirm" if rng["contour_to_confirm"] else "below 3%: rule does not apply",
                "evidence": (
                    f"NASADEM: mean slope {r['slope']['slope_mean_pct']:.1f}%, "
                    f"{100 * r['slope']['slope_ge3_share']:.0f}% of the cropland at 3% or more"
                ),
            },
            {
                "code": "V%",
                "name": "Base saturation 0-20 cm",
                "status": "needs soil test",
                "level": "-",
                "evidence": "-",
            },
            {"code": "Ca", "name": "Calcium 20-40 cm", "status": "needs soil test", "level": "-", "evidence": "-"},
            {
                "code": "m%",
                "name": "Aluminium saturation 20-40 cm",
                "status": "needs soil test",
                "level": "-",
                "evidence": "-",
            },
        ],
        "still_needed": [
            "Soil analysis of the 0-20 cm and 20-40 cm layers by an accredited laboratory (V%, Ca, m%; valid 24 "
            "months; IN 2/2025 items 4.1-III and 7)",
            "Confirmation of contour sowing (or sowing on the level) on at least 75% of the area where the slope is "
            "3% or more (item 3.2.1-I)",
            "The farmer's declaration of crops and species of the last three agricultural years (item 4.1-I and II); "
            "it can raise diversity to level 4 and corrects what the satellite misreads",
            "Registration of the field by an accredited agent so that Embrapa's SINM issues the official level "
            "(IN 2/2025 items 3, 4.2-4.3); useful soil depth (Portaria SPA/MAPA 209/2026 item 2.4)",
        ],
    }


def example_html(ex: dict, path: Path) -> None:
    e = html.escape
    rows = "".join(
        f"<tr class='{'need' if i['status'] == 'needs soil test' else ''}'><td><b>{e(i['code'])}</b></td>"
        f"<td>{e(i['name'])}</td><td>{e(i['status'])}</td><td>{e(i['level'])}</td><td class='ev'>{e(i['evidence'])}</td></tr>"
        for i in ex["indicators"]
    )
    needed = "".join(f"<li>{e(s)}</li>" for s in ex["still_needed"])
    sub = " · ".join(f"{k} {v}%" for k, v in ex["subsidy_pct_soy_2026_pilot"].items())
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Farm soil pre-check</title>
<style>
:root{{--ink:#0b0b0b;--muted:#5d5c58;--line:#e2e0da;--bg:#fcfcfb;--card:#ffffff;--accent:#1f6f4a;--warn:#8a5a00;--warnbg:#fff6e0}}
@media (prefers-color-scheme: dark){{:root{{--ink:#f2f1ed;--muted:#b3b1aa;--line:#3a3935;--bg:#151514;--card:#1d1d1b;--accent:#7fd3a4;--warn:#ffcf70;--warnbg:#3a2f12}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}}
main{{max-width:880px;margin:0 auto;padding:24px 16px 40px}}
h1{{font-size:1.45rem;margin:0 0 4px}}.sub{{color:var(--muted);margin:0 0 16px}}
.banner{{background:var(--warnbg);color:var(--warn);border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:0 0 18px;font-weight:600}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:18px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}}
.card .k{{color:var(--muted);font-size:.8rem;text-transform:uppercase;letter-spacing:.04em}}.card .v{{font-size:1.6rem;font-weight:700;color:var(--accent)}}
table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden;font-size:.88rem}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}th{{color:var(--muted);font-weight:600}}
tr.need td{{color:var(--muted)}}td.ev{{color:var(--muted)}}.wrap{{overflow-x:auto}}
h2{{font-size:1.05rem;margin:22px 0 8px}}ol{{padding-left:20px}}footer{{color:var(--muted);font-size:.78rem;margin-top:22px}}
</style></head><body><main>
<h1>Your farm's soil pre-check (ZarcNM, soybean)</h1>
<p class="sub">Example: an anonymous {e(ex["size_class"])} rural property in {e(ex["municipality"])} · about {ex["declared_area_ha_rounded"]} ha declared, {ex["cropland_ha_rounded"]} ha of cropland seen by satellite</p>
<div class="banner">Pre-check, not a certificate. 3 of the 6 indicators come from NASA data; 3 need a soil test. The official level comes only from Embrapa's SINM.</div>
<div class="grid">
<div class="card"><div class="k">If soil tests are at level 4</div><div class="v">{e(ex["satellite_side_nm_range_if_soil_level4"])}</div><div class="k">{e(ex["contour_note"])}</div></div>
<div class="card"><div class="k">If soil tests are at level 3</div><div class="v">{e(ex["satellite_side_nm_range_if_soil_level3"])}</div><div class="k">{e(ex["contour_note"])}</div></div>
<div class="card"><div class="k">Premium subsidy, soybean 2026 pilot</div><div style="font-weight:600;margin-top:6px">{e(sub)}</div></div>
</div>
<div class="wrap"><table><thead><tr><th></th><th>Indicator</th><th>Source</th><th>Pre-check</th><th>Evidence</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>What's still needed</h2><ol>{needed}</ol>
<footer>Rules: IN SPA/MAPA 2/2025 (Annex, soybean) and Portaria SPA/MAPA 209/2026; subsidy: Resolução CGSR 111/2026. {e(ATTRIBUTION)} Made by the FieldShift team (NASA Space Apps 2026).</footer>
</main></body></html>
"""
    path.write_text(doc, encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ibge", default=DEFAULT_IBGE)
    ap.add_argument("--raw", default=None)
    ap.add_argument("--results", default=str(HERE / "results"))
    ap.add_argument("--name", default="Cruz Alta (RS)")
    a = ap.parse_args()
    raw = raw_dir(a.ibge, a.raw)
    res = Path(a.results)
    res.mkdir(parents=True, exist_ok=True)
    rows, meta = assemble(raw)
    write_json(raw / "farm_results.json", rows)  # per farm: raw folder only
    st = stats(rows)
    st["farms_not_assessed"] = {str(k): v for k, v in st["farms_not_assessed"].items()}
    geoms = json.loads((raw / "farm_geoms.json").read_text(encoding="utf-8"))
    draw_map(rows, geoms, st, a.name, res / "farm-reports-map.png")
    ex_row = pick_example(rows, st)
    ex = example_public(ex_row, a.name) if ex_row else None
    if ex:
        example_html(ex, res / "example-report.html")
    # timing.json: step times of the last full run (reproduce.py writes it); else the last run of each scene step
    if (raw / "timing.json").exists():
        timing = {"step_seconds": read_json(raw / "timing.json")}
    else:
        timing = {}
        for step in ("now", "series", "winter"):
            p = raw / step / "run.json"
            if p.exists():
                timing[f"scenes_{step}_seconds_last_run"] = read_json(p)["seconds"]
    g = read_json(raw / "grid.json")
    car = read_json(raw / "car_access.json")
    ar = area(a.ibge)
    out = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "what": "Satellite-side pre-check of the ZarcNM soybean management level (IN SPA/MAPA 2/2025) for every "
        "rural property of the municipality in the CAR. Pre-check, not a certificate; never a final NM.",
        "municipality": {"name": a.name, "ibge": a.ibge},
        "privacy": "No owner name, CPF, CNPJ or CAR code is stored in this repository; the CAR layer has no personal "
        "fields and its code is replaced by a sequential number kept outside git. Only aggregates and one rounded "
        "anonymous example are published.",
        "car": {
            "source": car["source"],
            "accessed_utc": car["accessed_utc"],
            "records_returned": car["features_returned"],
            "active_records": st["farms_active"],
            "note": "CAR is self-declared; outlines overlap and are mostly not yet analysed by the state agency",
        },
        "sources": {
            "landsat": "NASA/USGS Landsat Collection 2 Level-2 (TM, ETM+, OLI, OLI-2), WRS-2 "
            + " and ".join(f"{p}/{r}" for p, r in sorted(ar["landsat_path_rows"], reverse=True)),
            "hls": "NASA HLS v2.0 L30 and S30 (LP DAAC), tiles " + "/".join(sorted(ar["hls_tiles"], reverse=True)),
            "nasadem": g["nasadem_items"],
            "worldcover": g["worldcover_items"],
            "access": "Microsoft Planetary Computer STAC, anonymous",
        },
        "method": {
            "pixel_classes": f"green NDVI >= {NDVI_GREEN}; straw NDVI < {NDVI_GREEN} and NDTI >= {NDTI_BARE}; "
            f"probable bare soil NDVI < {NDVI_GREEN} and NDTI < {NDTI_BARE} (analysis/residue-landsat)",
            "embrapa_ruler": embrapa_ruler.summary()["equation"],
            "straw_now_windows": meta["now_dates"],
            "bare_series": {
                "window": "20 Oct - 20 Nov, every year 1984-2026",
                "years_with_data": meta["series_years"],
                "scenes_used": meta["series_scenes_used"],
                "scenes_found": meta["series_scenes_found"],
                "signature_rule": f">= {int(ind.SIGNATURE_SHARE * 100)}% of the farm's clear cropland probable bare "
                f"soil in one scene (sensitivity {ind.SIGNATURE_SENSITIVITY})",
            },
            "winter": f"rules of analysis/rotation-fingerprint (HLS {ar['winter_tile']}, 1 Apr - 30 Nov, half-month "
            "medians, 2020-2026); diversity on the 2023-2025 winters",
            "slope": "NASADEM 30 m, percent slope; mean over the farm's cropland",
            "nm_range": "zarcnm_rules.classify over every combination of the observed level ranges, the three soil "
            "indicators at level 4 (or 3); contour assumed confirmed; literal 'consecutive soybean' reading at the "
            "lower end when most winters were fallow",
        },
        "results": st,
        "example_report": ex,
        "processing": {
            **timing,
            "grid_seconds": g["seconds"],
            "python": platform.python_version(),
        },
        "attribution": ATTRIBUTION,
    }
    write_json(res / "farm_reports.json", out)
    with (res / "summary_by_size.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["size_class", "upper_end_if_soil_level4", "farms", "cropland_ha", "declared_area_ha"])
        for sc, d in st["by_size_class"].items():
            for b, v in d["by_ceiling"].items():
                w.writerow([sc, b, v["farms"], v["cropland_ha"], v["declared_area_ha"]])
    print(json.dumps(st["by_ceiling_if_soil_level4"], indent=1))
    print(json.dumps(st["satellite_ready_nm3_plus"], indent=1))


if __name__ == "__main__":
    main()
