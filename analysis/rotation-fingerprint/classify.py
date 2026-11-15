# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Winter path of every 30 m cropland pixel of Cruz Alta, 2020-2026, from the NASA HLS NDVI time series.

    python -I classify.py <raw_dir> <results_dir> [--quadrats FILE]

1. Half-month median NDVI of the clear (Fmask) observations, 1 April - 30 November (16 bins), per pixel and year,
   from every granule written by scenes.py; gaps filled by linear interpolation in time when the pixel-year has
   enough clear half-months (MIN_BINS, and at least one in each of Jun-Jul, Aug-Sep and Oct-Nov).
2. Explicit phenological rules (constants below, each with its source) give one winter path per pixel-year:
   T wheat-like winter cereal, C winter cover crop, P fallow (no green winter canopy), O other / ambiguous.
3. Rotation fingerprint per pixel (the 2020-2026 sequence, e.g. "CTCTCTC") and the crop-diversity level of IN
   SPA/MAPA 2/2025 (Table 1, indicator 6) for the last three complete winters, as far as a satellite can see it.
4. Independent check against IBGE PAM planted areas (fetch_pam.py), aggregate "area confusion" bounds and a rule
   sensitivity grid.
Writes small JSON/CSV files to <results_dir> and the per-year class rasters to <raw_dir>/classes.npz (not committed).
"""

from __future__ import annotations

import argparse
import csv
import json
import warnings
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from rasterio.transform import Affine, xy
from rasterio.warp import transform as warp_transform

CRS = "EPSG:32622"
YEARS = list(range(2020, 2027))
NB = 16  # half-months from 1 April (bin 0) to 16-30 November (bin 15)
BIN_NAMES = [f"{m}-{h}" for m in ("Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov") for h in (1, 2)]
APR1, JUN1, JUN2, JUL1, AUG1, AUG2, SEP2, OCT1, OCT2, NOV2 = 0, 4, 5, 6, 8, 9, 11, 12, 13, 15
HALF_MONTH_DAYS = 365.25 / 24
MIN_BINS = 10  # of 16 clear half-months per pixel-year, before interpolation
NODATA = -32768
PIXEL_HA = 0.09

# Class codes in the rasters
NONE, WHEAT, COVER, FALLOW, OTHER = 0, 1, 2, 3, 4
CODE = {NONE: "-", WHEAT: "T", COVER: "C", FALLOW: "P", OTHER: "O"}
NAME = {
    WHEAT: "wheat-like winter cereal",
    COVER: "winter cover crop",
    FALLOW: "fallow (no green winter)",
    OTHER: "other",
}

MAIN = {
    # NDVI >= GREEN = a green crop canopy. 0.5 sits between the winter lows (0.33-0.39) and the peaks (0.81-0.84) of
    # the k-means centroids of the team's Sentinel-2 calendar (fieldshift-hq, 2019-2025); sensitivity 0.45 / 0.55.
    "green": 0.50,
    # NDVI < LOW after the peak = canopy gone (harvest, senescence or desiccation). Above the "no green" 0.25 of the
    # team's bare-soil calendar because a max composite of a dying canopy rarely reaches 0.25 within a half-month;
    # sensitivity 0.35 / 0.45.
    "low": 0.40,
    # Fallow: the winter (Jun-1 to Sep-2) never reaches FALLOW; sensitivity 0.40 / 0.60.
    "fallow": 0.50,
    # Green-up split between cover and wheat: a canopy green by Jun-2 was sown in autumn (cover; black oat is sown
    # after the soybean harvest, March-May); a canopy that first turns green from Jul-1 was sown in June-July
    # (wheat: ZARC rainfed wheat window at Cruz Alta 1 June - 20 July, 30% risk class from 21 May; MAPA Portaria
    # 385/2022). Sensitivity: split one half-month earlier / later.
    "split": JUL1,
    # Cover canopy must be gone by Nov-1 (desiccation before soybean sowing; team brief: September-October; the
    # Sentinel-2 cover centroid falls from September and stays at 0.23-0.28 from Oct-2). One half-month later than
    # the brief because the half-month in which the canopy is killed still holds its green dates (soybean sowing,
    # and so desiccation, runs into November). Sensitivity Oct-2 / Nov-2.
    "cover_end": OCT2 + 1,
    # Wheat canopy must last to Oct-1 or later (harvest October-November; Emater/RS harvest progress for the state,
    # refs in analysis/storms-bare-soil/straw_parameters.json) and peak from Aug-2 (heading about Sep).
    "wheat_end": OCT1,
    "wheat_peak": AUG2,
    # Composite: median of the clear observations in each half-month. The maximum-value composite (Holben 1986),
    # made for daily AVHRR without a cloud mask, moves every date towards the greenest observation (green-up
    # earlier, senescence later), and the rules are calendar dates; it is kept as a sensitivity run. This choice
    # was made after a first look at 2020 with both composites (2020: T 15.6% with max, 25.6% with median).
    "composite": "median",
}
SENSITIVITY = {
    "main": {},
    "green_0.45": {"green": 0.45},
    "green_0.55": {"green": 0.55},
    "low_0.35": {"low": 0.35},
    "low_0.45": {"low": 0.45},
    "fallow_0.40": {"fallow": 0.40},
    "fallow_0.60": {"fallow": 0.60},
    "split_jun2": {"split": JUN2},
    "split_jul2": {"split": JUL1 + 1},
    "cover_end_oct2": {"cover_end": OCT2},
    "cover_end_nov2": {"cover_end": NOV2},
    "composite_max": {"composite": "max"},
}
# Diversity (IN SPA/MAPA 2/2025, Table 1, indicator 6) - durations at half-month resolution
COVER_45D_BINS = 3  # 3 half-months = 45.7 days  -> "more than 45 days"
COVER_4M_BINS = 8  # 8 half-months = 121.8 days -> "more than 4 months" (within half a month)
WINDOWS = {"2023-2025": (2023, 2024, 2025), "2024-2026": (2024, 2025, 2026)}
BLOCK = 10  # 10 x 10 pixels = 300 m x 300 m = 9 ha, the quadrat size of item 6.2 IV (5-10 ha for fields > 100 ha)


def bin_of(d: str) -> int | None:
    m, day = int(d[5:7]), int(d[8:10])
    if not 4 <= m <= 11:
        return None
    return (m - 4) * 2 + (0 if day <= 15 else 1)


def composites(raw: Path, granules: list[dict], n: int) -> dict:
    """{year: {"max": (16, n) int16, "median": (16, n) int16, "nobs": (16, n) uint8}}"""
    by = defaultdict(list)
    for g in granules:
        if g.get("status") == "ok" and (raw / "ndvi" / f"{g['id']}.npz").exists():
            b = bin_of(g["date"])
            if b is not None:
                by[(int(g["date"][:4]), b)].append(g["id"])
    out = {}
    for y in YEARS:
        mx = np.full((NB, n), NODATA, dtype=np.int16)
        md = np.full((NB, n), NODATA, dtype=np.int16)
        nobs = np.zeros((NB, n), dtype=np.uint8)
        for b in range(NB):
            ids = by.get((y, b), [])
            if not ids:
                continue
            stack = np.stack([np.load(raw / "ndvi" / f"{i}.npz")["ndvi"] for i in ids])
            valid = stack != NODATA
            nobs[b] = valid.sum(0)
            mx[b] = np.where(valid, stack, NODATA).max(0)
            f = np.where(valid, stack.astype("float32"), np.nan)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                m = np.nanmedian(f, axis=0)
            md[b] = np.where(np.isfinite(m), np.round(m), NODATA).astype(np.int16)
        out[y] = {"max": mx, "median": md, "nobs": nobs, "granules": {b: len(by.get((y, b), [])) for b in range(NB)}}
        print(y, "granules per bin", [len(by.get((y, b), [])) for b in range(NB)], flush=True)
    return out


def fill(comp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Linear interpolation over missing half-months; returns (filled float32, eligible bool)."""
    v = np.where(comp == NODATA, np.nan, comp.astype("float32") / 10000)
    valid = np.isfinite(v)
    idx = np.arange(NB)[:, None]
    prev = np.maximum.accumulate(np.where(valid, idx, -1), axis=0)
    nxt = np.minimum.accumulate(np.where(valid, idx, NB)[::-1], axis=0)[::-1]
    vp = np.take_along_axis(v, np.clip(prev, 0, NB - 1), 0)
    vn = np.take_along_axis(v, np.clip(nxt, 0, NB - 1), 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        w = (idx - prev) / (nxt - prev)
        lin = vp + (vn - vp) * w
    out = np.where(valid, v, np.where((prev >= 0) & (nxt < NB), lin, np.where(prev >= 0, vp, vn)))
    eligible = (valid.sum(0) >= MIN_BINS) & valid[JUN1:AUG1].any(0) & valid[AUG1:OCT1].any(0) & valid[OCT1:].any(0)
    return out.astype("float32"), eligible


def classify(v: np.ndarray, eligible: np.ndarray, prm: dict) -> dict:
    """Rules on a filled (16, n) NDVI array. Returns class codes and the dates behind them (bins)."""
    g, lo, fal = prm["green"], prm["low"], prm["fallow"]
    idx = np.arange(NB)[:, None]
    n = v.shape[1]
    winter_max = v[JUN1 : SEP2 + 1].max(0)
    fallow = winter_max < fal
    p = JUN1 + v[JUN1 : OCT1 + 1].argmax(0)  # peak of the winter canopy, Jun-1 .. Oct-1
    # establishment gap of the winter canopy: the last half-month before the peak with no canopy (NDVI < LOW), e.g.
    # after the soybean harvest, or after weeds are desiccated for wheat sowing; if the pixel never drops below LOW
    # before the peak (a cover sown into standing soybean), the lowest half-month before the peak
    gap = (idx < p) & (v < lo)
    last_gap = np.where(gap, idx, -1).max(0)
    a = np.where(last_gap >= 0, last_gap, np.where(idx <= p, v, np.inf).argmin(0))
    up = (idx >= a) & (idx <= p) & (v >= g)
    has_green = up.any(0)
    u = np.where(has_green, up.argmax(0), p)  # green-up: first green half-month after the autumn minimum
    dn = (idx > p) & (v < lo)
    s = np.where(dn.any(0), dn.argmax(0), NB)  # end of canopy: first half-month after the peak below LOW
    last = v[NB - 1]
    wheat = (
        ~fallow
        & has_green
        & (u >= prm["split"])
        & (u <= AUG2)
        & (p >= prm["wheat_peak"])
        & (s >= prm["wheat_end"])
        # season not over (2026: imagery to mid-November): a wheat canopy still standing at the last image is kept
        & ((s < NB) | (last < g) | prm.get("incomplete", False))
    )
    cover = ~fallow & has_green & (u < prm["split"]) & (s >= AUG1) & (s <= prm["cover_end"])
    cls = np.full(n, OTHER, dtype=np.uint8)
    cls[cover] = COVER
    cls[wheat] = WHEAT
    cls[fallow] = FALLOW
    cls[~eligible] = NONE
    # reason codes for "other" (for the honesty table)
    other = cls == OTHER
    reason = np.full(n, "", dtype=object)
    reason[other & ~has_green] = "weak_canopy"
    reason[other & has_green & (s == NB) & (last >= g)] = "green_to_end_of_november"
    reason[other & has_green & (u < prm["split"]) & (s > prm["cover_end"]) & (reason == "")] = "long_cycle_autumn_sown"
    reason[other & has_green & (u < prm["split"]) & (s < AUG1) & (reason == "")] = "autumn_canopy_gone_before_aug"
    reason[other & has_green & (u > AUG2) & (reason == "")] = "green_up_after_august"
    reason[other & has_green & (u >= prm["split"]) & (reason == "")] = "short_or_early_ending_winter_cycle"
    reason[other & (reason == "")] = "unclassified"
    return {"cls": cls, "u": u.astype(np.uint8), "s": s.astype(np.uint8), "p": p.astype(np.uint8), "reason": reason}


def shares(cls: np.ndarray) -> dict:
    n_ok = int((cls != NONE).sum())
    d = {"classified_pixels": n_ok, "unclassified_pixels": int((cls == NONE).sum())}
    for c in (WHEAT, COVER, FALLOW, OTHER):
        d[CODE[c]] = round(100 * float((cls == c).sum()) / n_ok, 2) if n_ok else None
    return d


def pearson(a, b) -> float | None:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.size < 3 or np.std(a) == 0 or np.std(b) == 0:
        return None
    return round(float(np.corrcoef(a, b)[0, 1]), 3)


def area_bounds(sat_ha: float, pam_ha: float, total_ha: float) -> dict:
    """2 x 2 area table (satellite T / not T x PAM winter grain / not) under the best and worst pixel matching."""
    best_tt = min(sat_ha, pam_ha)
    worst_tt = max(0.0, sat_ha + pam_ha - total_ha)

    def table(tt):
        return {
            "sat_T_pam_grain": round(tt),
            "sat_T_pam_not_grain": round(sat_ha - tt),
            "sat_not_T_pam_grain": round(pam_ha - tt),
            "sat_not_T_pam_not_grain": round(total_ha - sat_ha - pam_ha + tt),
            "overall_agreement_pct": round(100 * (2 * tt + total_ha - sat_ha - pam_ha) / total_ha, 1),
        }

    return {"best_case": table(best_tt), "worst_case": table(worst_tt)}


def diversity(classes: dict, ends: dict, years: tuple) -> dict:
    """IN SPA/MAPA 2/2025 Table 1 indicator 6, as far as the satellite sees it, per pixel. Returns arrays."""
    cl = np.stack([classes[y] for y in years])
    dur = np.stack([ends[y]["s"].astype(int) - ends[y]["u"].astype(int) for y in years])
    complete = (cl != NONE).all(0)
    winter_crops = np.isin(cl, (WHEAT, COVER, OTHER)).sum(0)
    crops = 3 + winter_crops  # assumes one summer crop (soybean) per agricultural year; not classified here
    families2 = winter_crops >= 1  # soybean (Fabaceae) + winter grasses (Poaceae): wheat, oat, barley, rye
    cov = cl == COVER
    cov45 = (cov & (dur >= COVER_45D_BINS)).sum(0)
    cov4m = (cov & (dur >= COVER_4M_BINS)).sum(0)
    level = np.ones(cl.shape[1], dtype=np.uint8)
    level[(crops >= 4) & families2] = 2
    l3 = (crops >= 6) & families2 & ((cov4m >= 1) | (cov45 >= 3))
    level[l3] = 3
    l4_possible = l3 & (cov4m >= 1) & (cov45 >= 2)  # also needs >= 4 species, which a satellite cannot count
    level[~complete] = 0
    return {"level": level, "l4_possible": l4_possible & complete, "crops": crops, "cov45": cov45, "cov4m": cov4m}


def level_rule_text() -> dict:
    return {
        "source": "IN SPA/MAPA n. 2/2025, Annex, Table 1, indicator 6 (diversity of crops in the last three "
        "agricultural years) and item 2.4",
        "level_1": "requirements of the other levels not met",
        "level_2": "at least 4 crops, with at least 2 species and 2 botanical families",
        "level_3": "at least 6 crops, with at least 2 species and 2 botanical families, and 1 cover crop for more "
        "than 4 months OR 3 cover crops (single or mixed) for more than 45 days each",
        "level_4": "at least 6 crops, with at least 4 species and 2 botanical families, and 1 cover crop for more "
        "than 4 months AND 2 cover crops (single or mixed) for more than 45 days each",
        "applied_here": {
            "crops": "3 summer crops (one per agricultural year, assumed soybean, not classified) + every winter "
            "pixel-year with a green cycle (T, C or O)",
            "species_and_families": "any winter crop -> 2 species and 2 families (soybean, Fabaceae + a winter "
            "grass, Poaceae). 4 species cannot be counted from NDVI, so level 4 is never assigned: 'level 4 "
            "possible' flags pixels whose cover durations meet level 4, pending the species declared by the farmer",
            "cover_duration": f"green-up to end of canopy in half-months: >= {COVER_45D_BINS} (45.7 d) counts as "
            f"'more than 45 days', >= {COVER_4M_BINS} (121.8 d) as 'more than 4 months'; covers green on 1 April "
            "give a lower bound",
            "window": "last three complete winters before the 2026/27 soybean (2023-2025); 2024-2026 also shown "
            "(2026 imagery to 2 November, the last granule on the server at the run)",
        },
    }


def pick_quadrats(cls_by_year: dict, ends: dict, idx: np.ndarray, shape, tr: Affine, div: dict) -> list[dict]:
    """Rule: 300 m blocks of the analysis grid that are entirely cropland and classified in 2023-2025; for each
    diversity level 3, 2, 1 (2023-2025, block majority), the purest block (mean share of the yearly majority class,
    2020-2026), at least 5 km from the blocks already chosen; if a level has no block, the purest block with a new
    2020-2026 majority sequence. Chosen to show one example per level, not at random."""
    h, w = shape
    full = {y: np.zeros(h * w, dtype=np.uint8) for y in YEARS}
    for y in YEARS:
        full[y][idx] = cls_by_year[y]
    crop = np.zeros(h * w, dtype=bool)
    crop[idx] = True
    lev = np.zeros(h * w, dtype=np.uint8)
    lev[idx] = div["level"]
    hb, wb = h // BLOCK, w // BLOCK

    def blocks(a):
        return a[: hb * BLOCK, : wb * BLOCK].reshape(hb, BLOCK, wb, BLOCK).swapaxes(1, 2).reshape(hb, wb, -1)

    cb = blocks(crop.reshape(h, w)).all(-1)
    ok = cb.copy()
    for y in WINDOWS["2023-2025"]:
        ok &= (blocks(full[y].reshape(h, w)) != NONE).all(-1)
    purity = np.zeros((hb, wb))
    maj = {}
    for y in YEARS:
        b = blocks(full[y].reshape(h, w))
        counts = np.stack([(b == c).sum(-1) for c in (WHEAT, COVER, FALLOW, OTHER)], -1)
        maj[y] = np.array([WHEAT, COVER, FALLOW, OTHER])[counts.argmax(-1)]
        maj[y] = np.where(counts.sum(-1) > 0, maj[y], NONE)
        purity += counts.max(-1) / BLOCK**2
    purity /= len(YEARS)
    blev = np.median(blocks(lev.reshape(h, w)), -1)
    chosen = []
    for target in (3, 2, 1):
        cand = np.argwhere(ok & (blev == target))
        order = sorted(cand.tolist(), key=lambda rc: -purity[rc[0], rc[1]])
        for r, c in order:
            x, y = xy(tr, r * BLOCK + BLOCK / 2 - 0.5, c * BLOCK + BLOCK / 2 - 0.5)
            if all(np.hypot(x - q["_x"], y - q["_y"]) >= 5000 for q in chosen):
                chosen.append({"_x": x, "_y": y, "_r": r, "_c": c, "target_level": target})
                break
    # a level with no block: fill with the purest blocks whose 2020-2026 majority sequence is not chosen yet
    seqs = {(q["_r"], q["_c"]) for q in chosen}
    seq_of = lambda r, c: "".join(CODE[int(maj[y][r, c])] for y in YEARS)  # noqa: E731
    used = {seq_of(r, c) for r, c in seqs}
    for r, c in sorted(np.argwhere(ok).tolist(), key=lambda rc: -purity[rc[0], rc[1]]):
        if len(chosen) >= 3:
            break
        x, y = xy(tr, r * BLOCK + BLOCK / 2 - 0.5, c * BLOCK + BLOCK / 2 - 0.5)
        sq = seq_of(r, c)
        if sq not in used and all(np.hypot(x - q["_x"], y - q["_y"]) >= 5000 for q in chosen):
            chosen.append({"_x": x, "_y": y, "_r": r, "_c": c, "target_level": int(blev[r, c])})
            used.add(sq)
    return chosen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", type=Path)
    ap.add_argument("results", type=Path)
    ap.add_argument("--quadrats", type=Path, default=None, help="JSON with quadrats (lat/lon) to reuse, optional")
    args = ap.parse_args()
    raw, res = args.raw, args.results
    res.mkdir(parents=True, exist_ok=True)
    gz = np.load(raw / "grid.npz")
    idx, shape = gz["idx"], tuple(int(x) for x in gz["shape"])
    tr = Affine(*gz["transform"])
    sidx = json.loads((raw / "scene_index.json").read_text(encoding="utf-8"))
    comps = composites(raw, sidx["granules"], idx.size)

    # main classification and every sensitivity variant
    runs: dict[str, dict] = {}
    # a year whose last half-month (Nov-2) has no granule is a season not yet over at the run date
    incomplete = {y for y in YEARS if comps[y]["granules"][NB - 1] == 0}
    filled = {}
    for y in YEARS:
        filled[(y, "max")] = fill(comps[y]["max"])
        filled[(y, "median")] = fill(comps[y]["median"])
    for name, over in SENSITIVITY.items():
        prm = {**MAIN, **over}
        runs[name] = {
            y: classify(*filled[(y, prm["composite"])], {**prm, "incomplete": y in incomplete}) for y in YEARS
        }
        print(name, {y: shares(runs[name][y]["cls"]) for y in YEARS}, flush=True)
    main_run = runs["main"]
    cls = {y: main_run[y]["cls"] for y in YEARS}

    # PAM
    pam = {}
    with (res / "ibge_pam_1612_cruz_alta.csv").open(encoding="utf-8") as f:
        lines = [ln for ln in f if not ln.startswith("#")]
    for r in csv.DictReader(lines):
        pam[int(r["year"])] = {k: (float(v) if v else None) for k, v in r.items() if k != "year"}
    crop_ha = idx.size * PIXEL_HA

    rows = []
    for y in YEARS:
        s = shares(cls[y])
        p = pam.get(y)
        row = {
            "year": y,
            "classified_pct_of_cropland": round(100 * s["classified_pixels"] / idx.size, 1),
            "T_pct": s["T"],
            "C_pct": s["C"],
            "P_pct": s["P"],
            "O_pct": s["O"],
            "T_ha_scaled": round(s["T"] / 100 * crop_ha) if s["T"] is not None else None,
        }
        if p and s["T"] is not None:
            row.update(
                {
                    "pam_wheat_ha": p["wheat_ha"],
                    "pam_winter_grain_ha": p["winter_grain_ha"],
                    "pam_soybean_ha": p["soybean_ha"],
                    "pam_wheat_pct_of_soy": round(100 * p["wheat_ha"] / p["soybean_ha"], 1),
                    "pam_winter_grain_pct_of_soy": round(100 * p["winter_grain_ha"] / p["soybean_ha"], 1),
                }
            )
            row["T_minus_pam_winter_grain_pp"] = round(row["T_pct"] - row["pam_winter_grain_pct_of_soy"], 1)
        rows.append(row)
        print(row, flush=True)
    with (res / "winter_paths_by_year.csv").open("w", newline="", encoding="utf-8") as f:
        cols = list(dict.fromkeys(["year", *rows[0].keys(), *[k for r in rows for k in r]]))
        wcsv = csv.DictWriter(f, fieldnames=cols)
        wcsv.writeheader()
        for r in rows:
            wcsv.writerow(r)

    val_years = [r["year"] for r in rows if "pam_winter_grain_pct_of_soy" in r]
    vr = [r for r in rows if r["year"] in val_years]
    validation = {
        "years": val_years,
        "denominator_note": "satellite shares are % of classified WorldCover cropland pixels; PAM shares are % of "
        "the PAM soybean planted area of the same year (soybean fills about the whole summer cropland). Hectares: "
        f"satellite T share x {crop_ha:,.0f} ha of WorldCover 2021 cropland in the municipality.",
        "pearson_T_vs_pam_winter_grain_share": pearson(
            [r["T_pct"] for r in vr], [100 * r["pam_winter_grain_ha"] / r["pam_soybean_ha"] for r in vr]
        ),
        "pearson_T_vs_pam_wheat_share": pearson(
            [r["T_pct"] for r in vr], [100 * r["pam_wheat_ha"] / r["pam_soybean_ha"] for r in vr]
        ),
        "mean_T_pct": round(float(np.mean([r["T_pct"] for r in vr])), 1),
        "mean_pam_winter_grain_pct_of_soy": round(
            float(np.mean([100 * r["pam_winter_grain_ha"] / r["pam_soybean_ha"] for r in vr])), 1
        ),
        "mean_pam_wheat_pct_of_soy": round(
            float(np.mean([100 * r["pam_wheat_ha"] / r["pam_soybean_ha"] for r in vr])), 1
        ),
        "n_years_note": "n = 6 years: a correlation this small in sample has a wide uncertainty; read it as a "
        "check of level and direction, not as a validation.",
        "mean_abs_diff_T_vs_winter_grain_pp": round(
            float(np.mean([abs(r["T_minus_pam_winter_grain_pp"]) for r in vr])), 1
        ),
        "ratio_T_ha_to_pam_winter_grain_ha": {
            r["year"]: round(r["T_ha_scaled"] / r["pam_winter_grain_ha"], 2) for r in vr
        },
        "area_confusion_bounds": {
            r["year"]: area_bounds(r["T_ha_scaled"], r["pam_winter_grain_ha"], crop_ha) for r in vr
        },
        "area_confusion_note": "IBGE publishes municipal totals, not fields, so a pixel confusion matrix is "
        "impossible here. The 2 x 2 table is the satellite T area against the PAM winter-grain area in the same "
        "cropland, filled in the most favourable and the least favourable way the two totals allow; the true "
        "agreement lies between the two.",
    }
    sens = []
    for name, rr in runs.items():
        t = {y: shares(rr[y]["cls"]) for y in YEARS}
        row = {"variant": name}
        for y in YEARS:
            for k in ("T", "C", "P", "O"):
                row[f"{k}_{y}"] = t[y][k]
        row["pearson_T_vs_pam_winter_grain"] = pearson(
            [t[y]["T"] for y in val_years], [pam[y]["winter_grain_ha"] / pam[y]["soybean_ha"] * 100 for y in val_years]
        )
        row["mean_abs_diff_T_vs_pam_winter_grain_pp"] = round(
            float(
                np.mean([abs(t[y]["T"] - pam[y]["winter_grain_ha"] / pam[y]["soybean_ha"] * 100) for y in val_years])
            ),
            1,
        )
        sens.append(row)
    with (res / "sensitivity.csv").open("w", newline="", encoding="utf-8") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(sens[0]))
        wcsv.writeheader()
        wcsv.writerows(sens)
    # stability: share of pixel-years whose class changes under each variant
    stability = {}
    for name, rr in runs.items():
        if name == "main":
            continue
        same, tot = 0, 0
        for y in YEARS:
            m = (cls[y] != NONE) & (rr[y]["cls"] != NONE)
            same += int((cls[y][m] == rr[y]["cls"][m]).sum())
            tot += int(m.sum())
        stability[name] = round(100 * same / tot, 1)

    # reasons for "other"
    other_reasons = {y: dict(Counter(main_run[y]["reason"][cls[y] == OTHER].tolist()).most_common()) for y in YEARS}

    # fingerprints
    code = np.zeros(idx.size, dtype=np.int64)
    for y in YEARS:
        code = code * 5 + cls[y]
    uniq, cnt = np.unique(code, return_counts=True)

    def decode(c):
        s = []
        for _ in YEARS:
            s.append(CODE[int(c % 5)])
            c //= 5
        return "".join(reversed(s))

    order = np.argsort(-cnt)
    complete_fp = np.all(np.stack([cls[y] != NONE for y in YEARS]), 0)
    top = []
    for i in order[:25]:
        fp = decode(int(uniq[i]))
        top.append(
            {"fingerprint_2020_2026": fp, "pixels": int(cnt[i]), "pct_of_cropland": round(100 * cnt[i] / idx.size, 2)}
        )
    with (res / "fingerprints_top25.csv").open("w", newline="", encoding="utf-8") as f:
        wcsv = csv.DictWriter(f, fieldnames=list(top[0]))
        wcsv.writeheader()
        wcsv.writerows(top)
    stack = np.stack([cls[y] for y in YEARS])
    n_wheat_years = (stack == WHEAT).sum(0)
    n_cover_years = (stack == COVER).sum(0)
    n_paths = np.zeros(idx.size, dtype=np.uint8)
    for c in (WHEAT, COVER, FALLOW, OTHER):
        n_paths += (stack == c).any(0)
    fp_stats = {
        "pixels_with_all_7_winters_classified_pct": round(100 * float(complete_fp.mean()), 1),
        "among_complete": {
            "distinct_paths_per_pixel_pct": {
                str(k): round(100 * float((n_paths[complete_fp] == k).mean()), 1) for k in range(1, 5)
            },
            "wheat_years_pct": {
                str(k): round(100 * float((n_wheat_years[complete_fp] == k).mean()), 1) for k in range(8)
            },
            "cover_years_pct": {
                str(k): round(100 * float((n_cover_years[complete_fp] == k).mean()), 1) for k in range(8)
            },
            "same_path_every_year_pct": round(100 * float((n_paths[complete_fp] == 1).mean()), 1),
            "never_fallow_pct": round(100 * float(((stack == FALLOW).sum(0)[complete_fp] == 0).mean()), 1),
        },
    }

    # diversity
    ends = {y: main_run[y] for y in YEARS}
    div = {k: diversity(cls, ends, yrs) for k, yrs in WINDOWS.items()}
    div_stats = {}
    for k, d in div.items():
        comp = d["level"] > 0
        div_stats[k] = {
            "pixels_with_3_winters_classified_pct": round(100 * float(comp.mean()), 1),
            "level_pct_of_those": {str(lv): round(100 * float((d["level"][comp] == lv).mean()), 1) for lv in (1, 2, 3)},
            "level_4_possible_pct_of_those": round(100 * float(d["l4_possible"][comp].mean()), 1),
            "level_ha_scaled": {str(lv): round(float((d["level"][comp] == lv).mean()) * crop_ha) for lv in (1, 2, 3)},
        }

    # class rasters for the figures
    np.savez_compressed(
        raw / "classes.npz",
        **{f"cls_{y}": cls[y] for y in YEARS},
        **{f"u_{y}": main_run[y]["u"] for y in YEARS},
        **{f"s_{y}": main_run[y]["s"] for y in YEARS},
        **{f"level_{k}": d["level"] for k, d in div.items()},
        **{f"l4p_{k}": d["l4_possible"] for k, d in div.items()},
        n_wheat_years=n_wheat_years,
        n_cover_years=n_cover_years,
    )
    # median NDVI profile per class (for the figure): pooled pixel-years, 20 000 random per class
    rng = np.random.default_rng(20261115)
    profiles = {}
    for c in (WHEAT, COVER, FALLOW, OTHER):
        pool = []
        for y in YEARS:
            v, _ = filled[(y, MAIN["composite"])]
            sel = np.flatnonzero(cls[y] == c)
            if sel.size:
                pool.append(v[:, rng.choice(sel, min(4000, sel.size), replace=False)])
        if pool:
            a = np.concatenate(pool, 1)
            profiles[CODE[c]] = {
                "n": int(a.shape[1]),
                "p25": np.round(np.percentile(a, 25, 1), 3).tolist(),
                "median": np.round(np.median(a, 1), 3).tolist(),
                "p75": np.round(np.percentile(a, 75, 1), 3).tolist(),
            }

    # quadrats
    quad_source = "selected here (rule in pick_quadrats)"
    quads = []
    if args.quadrats and args.quadrats.exists():
        doc = json.loads(args.quadrats.read_text(encoding="utf-8"))
        found = []

        def walk(o):
            if isinstance(o, dict):
                if "lat" in o and "lon" in o and ("quadrant_id" in o or "quadrat_id" in o):
                    found.append(o)
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)

        walk(doc)
        seen = {}
        for q in found:
            seen.setdefault(q.get("quadrant_id") or q.get("quadrat_id"), q)
        for qid, q in seen.items():
            xs, ys = warp_transform("EPSG:4326", CRS, [q["lon"]], [q["lat"]])
            col, row = ~tr * (xs[0], ys[0])
            quads.append({"_r": int(row) - BLOCK // 2, "_c": int(col) - BLOCK // 2, "id": qid, "pixel_block": True})
        quad_source = f"reused from {args.quadrats.name} (same lat/lon centres; 300 m block re-centred on this grid)"
    if not quads:
        for k, q in enumerate(pick_quadrats(cls, ends, idx, shape, tr, div["2023-2025"]), 1):
            quads.append({"_r": q["_r"] * BLOCK, "_c": q["_c"] * BLOCK, "id": f"RF-Q{k}", "target": q["target_level"]})
    h, w = shape
    pos = np.full(h * w, -1, dtype=np.int64)
    pos[idx] = np.arange(idx.size)
    examples = []
    for q in quads:
        rr, cc = np.meshgrid(np.arange(q["_r"], q["_r"] + BLOCK), np.arange(q["_c"], q["_c"] + BLOCK), indexing="ij")
        flat = (rr * w + cc).ravel()
        flat = flat[(flat >= 0) & (flat < h * w)]
        pi = pos[flat]
        pi = pi[pi >= 0]
        xc, yc = xy(tr, q["_r"] + BLOCK / 2 - 0.5, q["_c"] + BLOCK / 2 - 0.5)
        lon, lat = warp_transform(CRS, "EPSG:4326", [xc], [yc])
        yrs = {}
        seq = ""
        for y in YEARS:
            c = cls[y][pi]
            counts = {CODE[k]: int((c == k).sum()) for k in (WHEAT, COVER, FALLOW, OTHER, NONE)}
            ok = c != NONE
            if ok.sum() == 0:
                maj = NONE
            else:
                maj = max((WHEAT, COVER, FALLOW, OTHER), key=lambda k: int((c == k).sum()))
            seq += CODE[maj]
            m = c == maj
            yrs[str(y)] = {
                "majority_path": CODE[maj],
                "majority_name": NAME.get(maj, "not classified"),
                "pixel_counts": counts,
                "green_up_half_month": BIN_NAMES[int(np.median(ends[y]["u"][pi][m]))]
                if m.any() and maj != FALLOW
                else None,
                "canopy_end_half_month": (
                    (
                        BIN_NAMES[int(np.median(ends[y]["s"][pi][m]))]
                        if np.median(ends[y]["s"][pi][m]) < NB
                        else "after Nov-2"
                    )
                    if m.any() and maj != FALLOW
                    else None
                ),
                "green_days_approx": round(
                    float(np.median(ends[y]["s"][pi][m].astype(int) - ends[y]["u"][pi][m])) * HALF_MONTH_DAYS
                )
                if m.any() and maj != FALLOW
                else None,
            }
        lv = {}
        for k, d in div.items():
            lvv = d["level"][pi]
            vals, cts = np.unique(lvv[lvv > 0], return_counts=True)
            lv[k] = {
                "level_majority_of_pixels": int(vals[cts.argmax()]) if vals.size else None,
                "pixel_level_counts": {str(int(a)): int(b) for a, b in zip(vals, cts, strict=True)},
                "level_4_possible_pixels": int(d["l4_possible"][pi].sum()),
            }
        examples.append(
            {
                "quadrat_id": q["id"],
                "lat": round(float(lat[0]), 5),
                "lon": round(float(lon[0]), 5),
                "size": "300 m x 300 m (9 ha), 100 HLS pixels",
                "cropland_pixels": int(pi.size),
                "sequence_2020_2026": seq,
                "years": yrs,
                "diversity_level_IN2_2025": lv,
                **({"selected_as_example_of_level": q["target"]} if "target" in q else {}),
            }
        )
    ex_doc = {
        "title": "Rotation fingerprint of three 9 ha cropland quadrats of Cruz Alta (RS) and the crop-diversity level "
        "of IN SPA/MAPA 2/2025 a satellite can support",
        "quadrats_source": quad_source,
        "selection_rule": pick_quadrats.__doc__.replace("\n    ", " ") if "selected here" in quad_source else None,
        "codes": {"T": NAME[WHEAT], "C": NAME[COVER], "P": NAME[FALLOW], "O": NAME[OTHER], "-": "not classified"},
        "diversity_rule": level_rule_text(),
        "quadrats": examples,
        "caveat": "Classes are phenological hypotheses from NDVI, not field labels; the level is a pre-check of one "
        "of six ZARC-NM indicators, never a classification (item 2.2: no level without every indicator).",
        "data": "NASA HLS v2.0 L30 + S30 (LP DAAC), via Microsoft Planetary Computer",
    }
    (res / "zarcnm_diversity_examples.json").write_text(
        json.dumps(ex_doc, indent=1, ensure_ascii=False), encoding="utf-8"
    )

    # coverage
    cov = {
        str(y): {
            "granules_ok": int(sum(comps[y]["granules"].values())),
            "granules_per_half_month": [comps[y]["granules"][b] for b in range(NB)],
            "median_clear_obs_per_pixel_per_half_month": [int(np.median(comps[y]["nobs"][b])) for b in range(NB)],
            "classified_pct_of_cropland": round(100 * float((cls[y] != NONE).mean()), 1),
            "season_complete": y not in incomplete,
        }
        for y in YEARS
    }
    st = Counter(g.get("status", "?").split(":")[0] for g in sidx["granules"])
    doc = {
        "title": "Every field's winter, from space: winter path of each 30 m cropland pixel of Cruz Alta (RS), "
        "2020-2026, NASA HLS",
        "generated": date.today().isoformat(),
        "data": {
            "imagery": "NASA HLS v2.0 HLSL30 + HLSS30 (LP DAAC; doi:10.5067/HLS/HLSL30.002, "
            "doi:10.5067/HLS/HLSS30.002), tile T22JBP, 1 Apr - 30 Nov, read via the Microsoft Planetary Computer STAC",
            "stac_searched_at_utc": sidx.get("searched_at_utc"),
            "granule_status": dict(st),
            "cropland_mask": "ESA WorldCover 2021 v200 class 40 >= 50% of the 30 m pixel, inside IBGE municipality "
            "4306106 (2022 mesh)",
            "cropland_pixels": int(idx.size),
            "cropland_ha": round(crop_ha),
            "check": "IBGE PAM SIDRA 1612 planted area (results/ibge_pam_1612_cruz_alta.csv)",
        },
        "method": {
            "composite": "half-month median NDVI of the clear observations (maximum-value composite, Holben "
            "1986, as a sensitivity run), 16 half-months 1 Apr - 30 Nov",
            "gap_fill": f"linear in time; pixel-year kept with >= {MIN_BINS} clear half-months and >= 1 in each of "
            "Jun-Jul, Aug-Sep, Oct-Nov",
            "parameters_main": {
                k: (BIN_NAMES[v] if k in ("split", "cover_end", "wheat_end", "wheat_peak") else v)
                for k, v in MAIN.items()
            },
            "rules": {
                "P fallow": "max NDVI Jun-1..Sep-2 < fallow",
                "T wheat-like": "green-up (first half-month >= green after the autumn minimum) from split to Aug-2, "
                "peak (max Jun-1..Oct-1) at or after wheat_peak, canopy end (first half-month after the peak < low) "
                "at or after wheat_end (or not yet ended with Nov-2 < green)",
                "C cover": "green-up before split (autumn-sown) and canopy end from Aug-1 to cover_end",
                "O other": "every other green winter (reasons counted in other_reasons)",
            },
            "sensitivity_variants": {k: v for k, v in SENSITIVITY.items()},
        },
        "coverage_by_year": cov,
        "shares_by_year": rows,
        "validation_vs_pam": validation,
        "sensitivity_pixel_years_unchanged_pct": stability,
        "other_reasons_by_year": other_reasons,
        "fingerprints": {"top": top[:12], "stats": fp_stats},
        "diversity_IN2_2025": {"rule": level_rule_text(), "by_window": div_stats},
        "ndvi_profiles_by_class": {"bins": BIN_NAMES, **profiles},
        "what_cannot_be_said": [
            "Which crop is in a pixel: T is any winter cereal sown in June-July and harvested in October-November "
            "(wheat, barley, triticale, rye, white oat for grain look alike in NDVI); C is any autumn-sown canopy "
            "gone by October (black oat, ryegrass, vetch mixes, grazed oat, volunteer or weeds).",
            "Whether a C canopy was sown as a cover crop, grazed, or cut for forage (item 2.4 III excludes silage "
            "and hay from the count).",
            "The summer crop: the diversity count assumes one soybean crop per summer; maize summers (PAM 8-10 "
            "thousand ha) or a second summer crop are not seen here.",
            "Species and families: a satellite cannot count 4 species, so level 4 is never assigned; canola "
            "(Brassicaceae, 4,200 ha in PAM 2025) would add a family but is not separated.",
            "Field boundaries: pixels are classified one by one; a field mixes classes at its edges.",
        ],
        "references": {
            "HLS": "Claverie et al. 2018, Remote Sens. Environ. 219:145-161, doi:10.1016/j.rse.2018.09.002",
            "NDVI": "Tucker 1979, Remote Sens. Environ. 8:127-150, doi:10.1016/0034-4257(79)90013-0",
            "max_value_composite": "Holben 1986, Int. J. Remote Sens. 7:1417-1434, doi:10.1080/01431168608948945",
            "wheat_sowing": "MAPA ZARC risk table 2022/2023 (Portaria 385 of 8 Dec 2022), rainfed wheat at Cruz "
            "Alta: 20% risk class 1 Jun - 20 Jul (data/sites/cruz-alta/input/replay-2023.yaml)",
            "wheat_harvest_and_cover_desiccation": "analysis/storms-bare-soil/straw_parameters.json (Emater/RS "
            "harvest progress; desiccation September-October is a team scenario, no Cruz Alta calendar found)",
            "winter_profiles": "team's Sentinel-2 k-means of winter NDVI profiles, Cruz Alta 2019-2025 "
            "(fieldshift-hq, private planning repository)",
            "norm": "IN SPA/MAPA n. 2/2025, Annex: Table 1 indicator 6, items 2.4, 6.2, 6.4-6.6",
        },
    }
    (res / "rotation_fingerprint.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(validation, indent=1))
    print(json.dumps(div_stats, indent=1))
    print(json.dumps(fp_stats, indent=1))
    print(json.dumps(stability, indent=1))


if __name__ == "__main__":
    main()
