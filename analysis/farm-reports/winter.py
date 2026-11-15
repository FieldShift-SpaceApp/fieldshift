# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Winter path of every farm-cropland pixel, 2020-2026, and the farm's crop-diversity inputs (IN 2/2025 indicator 6).

    python -I winter.py [--ibge 4306106] [--raw DIR]

Reads the per-granule NDVI written by `scenes.py winter` (HLS L30/S30, tile T22JBP, 1 Apr - 30 Nov, 60 m) and
applies the phenological rules of analysis/rotation-fingerprint/classify.py (merged in PR #59 while this was written;
its MAIN constants are VENDORED below, checked identical to the merged file, so this folder runs on its own):
half-month median NDVI, linear gap filling, then per pixel-year one class: T wheat-like winter cereal, C winter
cover crop, P fallow (no green winter), O other / ambiguous, - not enough clear half-months.
Writes winter_pixels.npz (per-pixel classes and cover durations, raw folder) and winter_farms.json.
"""

from __future__ import annotations

import argparse
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DEFAULT_IBGE, FarmIndex, raw_dir, read_json, write_json  # noqa: E402

YEARS = list(range(2020, 2027))
NB = 16  # half-months from 1 April (bin 0) to 16-30 November (bin 15)
APR1, JUN1, JUN2, JUL1, AUG1, AUG2, SEP2, OCT1, OCT2, NOV2 = 0, 4, 5, 6, 8, 9, 11, 12, 13, 15
MIN_BINS = 10
NODATA = -32768
NONE, WHEAT, COVER, FALLOW, OTHER = 0, 1, 2, 3, 4
CODE = {NONE: "-", WHEAT: "T", COVER: "C", FALLOW: "P", OTHER: "O"}
# VENDORED from analysis/rotation-fingerprint/classify.py, MAIN (each constant's source is cited there):
# green 0.50 (between winter lows and peaks of the team's Sentinel-2 calendar), low 0.40 (canopy gone),
# fallow 0.50 (winter never green), split Jul-1 (autumn-sown cover vs June-July-sown wheat; ZARC wheat window,
# MAPA Portaria 385/2022), cover canopy gone by Nov-1, wheat canopy lasting to Oct-1 or later with a peak from Aug-2.
MAIN = {"green": 0.50, "low": 0.40, "fallow": 0.50, "split": JUL1, "cover_end": OCT2 + 1, "wheat_end": OCT1}
MAIN["wheat_peak"] = AUG2
COVER_45D_BINS = 3  # 3 half-months = 45.7 days -> "more than 45 days"
COVER_4M_BINS = 8  # 8 half-months = 121.8 days -> "more than 4 months"
DIVERSITY_YEARS = (2023, 2024, 2025)  # last three complete winters before the 2026/27 soybean


def bin_of(d: str) -> int | None:
    m, day = int(d[5:7]), int(d[8:10])
    if not 4 <= m <= 11:
        return None
    return (m - 4) * 2 + (0 if day <= 15 else 1)


def composites(src: Path, index: list[dict], n: int) -> dict:
    by = defaultdict(list)
    for g in index:
        if g.get("used"):
            b = bin_of(g["date"])
            if b is not None:
                by[(int(g["date"][:4]), b)].append(g["id"])
    out = {}
    for y in YEARS:
        md = np.full((NB, n), NODATA, dtype=np.int16)
        for b in range(NB):
            ids = by.get((y, b), [])
            if not ids:
                continue
            stack = np.stack([np.load(src / f"{i}.npz")["ndvi"] for i in ids]).astype("float32")
            stack[stack == NODATA] = np.nan
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                m = np.nanmedian(stack, axis=0)
            md[b] = np.where(np.isfinite(m), np.round(m), NODATA).astype(np.int16)
        out[y] = md
        print(y, "granules per half-month", [len(by.get((y, b), [])) for b in range(NB)], flush=True)
    return out


def fill(comp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Linear interpolation over missing half-months (as rotation-fingerprint); returns (filled, eligible)."""
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


def classify(v: np.ndarray, eligible: np.ndarray, prm: dict = MAIN) -> dict:
    """The rules of rotation-fingerprint classify(), on a filled (16, n) NDVI array."""
    g, lo, fal = prm["green"], prm["low"], prm["fallow"]
    idx = np.arange(NB)[:, None]
    n = v.shape[1]
    fallow = v[JUN1 : SEP2 + 1].max(0) < fal
    p = JUN1 + v[JUN1 : OCT1 + 1].argmax(0)
    gap = (idx < p) & (v < lo)
    last_gap = np.where(gap, idx, -1).max(0)
    a = np.where(last_gap >= 0, last_gap, np.where(idx <= p, v, np.inf).argmin(0))
    up = (idx >= a) & (idx <= p) & (v >= g)
    has_green = up.any(0)
    u = np.where(has_green, up.argmax(0), p)
    dn = (idx > p) & (v < lo)
    s = np.where(dn.any(0), dn.argmax(0), NB)
    last = v[NB - 1]
    wheat = (
        ~fallow
        & has_green
        & (u >= prm["split"])
        & (u <= AUG2)
        & (p >= prm["wheat_peak"])
        & (s >= prm["wheat_end"])
        & ((s < NB) | (last < g))
    )
    cover = ~fallow & has_green & (u < prm["split"]) & (s >= AUG1) & (s <= prm["cover_end"])
    cls = np.full(n, OTHER, dtype=np.uint8)
    cls[cover] = COVER
    cls[wheat] = WHEAT
    cls[fallow] = FALLOW
    cls[~eligible] = NONE
    return {"cls": cls, "dur": (s.astype(np.int16) - u.astype(np.int16))}


def pixel_diversity(cls: np.ndarray, dur: np.ndarray) -> dict:
    """IN 2/2025 Table 1 indicator 6 per pixel over DIVERSITY_YEARS (rows of cls/dur), as rotation-fingerprint."""
    complete = (cls != NONE).all(0)
    winter_crops = np.isin(cls, (WHEAT, COVER, OTHER)).sum(0)
    crops = 3 + winter_crops  # one summer crop per agricultural year, assumed soybean (not classified)
    families2 = winter_crops >= 1  # soybean (Fabaceae) + a winter grass (Poaceae)
    cov = cls == COVER
    cov45 = (cov & (dur >= COVER_45D_BINS)).sum(0)
    cov4m = (cov & (dur >= COVER_4M_BINS)).sum(0)
    level = np.ones(cls.shape[1], dtype=np.uint8)
    level[(crops >= 4) & families2] = 2
    l3 = (crops >= 6) & families2 & ((cov4m >= 1) | (cov45 >= 3))
    level[l3] = 3
    l4_possible = l3 & (cov4m >= 1) & (cov45 >= 2)
    level[~complete] = 0
    fallow_any = (cls == FALLOW).any(0) & complete
    return {"level": level, "l4_possible": l4_possible & complete, "fallow_any": fallow_any}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ibge", default=DEFAULT_IBGE)
    ap.add_argument("--raw", default=None)
    a = ap.parse_args()
    raw = raw_dir(a.ibge, a.raw)
    fi = FarmIndex(raw / "farm_idx60.npz")
    index = read_json(raw / "winter" / "index.json")
    comp = composites(raw / "winter", index, fi.idx.size)
    cls_y, dur_y = {}, {}
    for y in YEARS:
        v, el = fill(comp[y])
        r = classify(v, el)
        cls_y[y], dur_y[y] = r["cls"], r["dur"]
    div = pixel_diversity(np.stack([cls_y[y] for y in DIVERSITY_YEARS]), np.stack([dur_y[y] for y in DIVERSITY_YEARS]))
    np.savez_compressed(
        raw / "winter_pixels.npz",
        **{f"cls_{y}": cls_y[y] for y in YEARS},
        **{f"dur_{y}": dur_y[y] for y in YEARS},
        level=div["level"],
        l4_possible=div["l4_possible"],
        fallow_any=div["fallow_any"],
    )
    farms = []
    lab = fi.lab
    for_y = {}
    for y in YEARS:
        counts = np.stack(
            [np.bincount(lab, weights=(cls_y[y] == c).astype(float), minlength=fi.n) for c in range(5)], 1
        )
        for_y[y] = counts
    lev = np.stack([np.bincount(lab, weights=(div["level"] == k).astype(float), minlength=fi.n) for k in range(4)], 1)
    l4p = np.bincount(lab, weights=div["l4_possible"].astype(float), minlength=fi.n)
    fal = np.bincount(lab, weights=div["fallow_any"].astype(float), minlength=fi.n)
    for k in range(fi.n):
        seq = ""
        shares = {}
        for y in YEARS:
            c = for_y[y][k]
            ok = c[1:].sum()
            if ok == 0:
                seq += "-"
                shares[str(y)] = None
                continue
            seq += CODE[int(1 + np.argmax(c[1:]))]
            shares[str(y)] = {CODE[i]: round(float(c[i] / ok), 3) for i in range(1, 5)}
        n_lev = lev[k, 1:].sum()
        farms.append(
            {
                "farm": k,
                "fingerprint_2020_2026": seq,
                "winter_shares": shares,
                "diversity_pixels_classified": int(n_lev),
                "diversity_level_shares": (
                    {str(i): round(float(lev[k, i] / n_lev), 3) for i in (1, 2, 3)} if n_lev else None
                ),
                "level4_possible_share": round(float(l4p[k] / n_lev), 3) if n_lev else None,
                "fallow_winter_share": round(float(fal[k] / n_lev), 3) if n_lev else None,
            }
        )
    write_json(raw / "winter_farms.json", farms)
    print(f"winter: {sum(1 for f in farms if f['diversity_pixels_classified'])} farms with diversity input")


if __name__ == "__main__":
    main()
