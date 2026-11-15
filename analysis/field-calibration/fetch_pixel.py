# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Look up the satellite NDTI and NDVI of the 30 m pixel under each field measurement (NASA HLS, then Landsat).

    python -I fetch_pixel.py PRIVATE.csv --out measurements/cruz_alta.csv [--max-days 10]

PRIVATE.csv (kept out of git; see measurements/README.md) has one row per rope transect with at least
``id, lat, lon, date, pct_straw`` (or the three point counts). For each row the script searches the Microsoft
Planetary Computer STAC anonymously (no account) for HLS v2.0 S30 and L30 granules, and Landsat Collection 2
Level-2 scenes, within ``--max-days`` of the measurement date, and takes the scene closest in time whose pixel is
clear (HLS Fmask / Landsat QA_PIXEL: no cloud, adjacent cloud, shadow, snow or water). It reads the 3 x 3 pixels
around the point (90 m) and reports the centre value and the 3 x 3 spread.

The output is the PUBLIC measurement file: coordinates are dropped (a field's location can identify its owner
through the rural land registry), only the date, the counts, the cover and the satellite values remain.
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.warp import transform
from rasterio.windows import Window

STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
BANDS = {
    "hls2-s30": {"red": "B04", "nir": "B8A", "sw1": "B11", "sw2": "B12", "qa": "Fmask"},
    "hls2-l30": {"red": "B04", "nir": "B05", "sw1": "B06", "sw2": "B07", "qa": "Fmask"},
    "landsat-c2-l2": {"red": "red", "nir": "nir08", "sw1": "swir16", "sw2": "swir22", "qa": "qa_pixel"},
}
PUBLIC_COLS = [
    "id",
    "date",
    "method",
    "points_total",
    "points_straw",
    "points_bare",
    "points_green",
    "pct_straw",
    "winter_crop",
    "ndti",
    "ndvi",
    "scene",
    "days_from_scene",
]


def clear(coll: str, qa: np.ndarray) -> np.ndarray:
    qa = qa.astype(np.int64)
    if coll.startswith("hls"):
        return (((qa >> 1) & 0b11111) == 0) & (qa != 255)
    bad = (qa & 1) | ((qa >> 1) & 1) | ((qa >> 3) & 1) | ((qa >> 4) & 1) | ((qa >> 5) & 1) | ((qa >> 7) & 1)
    return (bad == 0) & (((qa >> 6) & 1) == 1)


def reflect(coll: str, a: np.ndarray) -> np.ndarray:
    a = a.astype("float64")
    if coll.startswith("hls"):
        a[a == -9999] = np.nan
        return a * 1e-4
    a[a == 0] = np.nan
    return a * 2.75e-5 - 0.2


def read3x3(href: str, lon: float, lat: float) -> np.ndarray | None:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2"):
        with rasterio.open(href) as src:
            xs, ys = transform("EPSG:4326", src.crs, [lon], [lat])
            r, c = src.index(xs[0], ys[0])
            if not (1 <= r < src.height - 1 and 1 <= c < src.width - 1):
                return None
            return src.read(1, window=Window(c - 1, r - 1, 3, 3))


def pixel(item, lon: float, lat: float) -> dict | None:
    coll = item.collection_id
    b = BANDS[coll]
    signed = planetary_computer.sign(item)
    qa = read3x3(signed.assets[b["qa"]].href, lon, lat)
    if qa is None or not clear(coll, qa)[1, 1]:
        return None
    v = {k: reflect(coll, read3x3(signed.assets[b[k]].href, lon, lat)) for k in ("red", "nir", "sw1", "sw2")}
    with np.errstate(invalid="ignore", divide="ignore"):
        ndvi = (v["nir"] - v["red"]) / (v["nir"] + v["red"])
        ndti = (v["sw1"] - v["sw2"]) / (v["sw1"] + v["sw2"])
    ok = clear(coll, qa) & np.isfinite(ndti)
    if not np.isfinite(ndti[1, 1]):
        return None
    return {
        "ndti": float(ndti[1, 1]),
        "ndvi": float(ndvi[1, 1]),
        "ndti_3x3_sd": float(np.nanstd(ndti[ok])) if ok.sum() > 1 else float("nan"),
        "scene": item.id,
    }


def lookup(cat, lon: float, lat: float, day: date, max_days: int) -> dict | None:
    dt = f"{day - timedelta(days=max_days)}/{day + timedelta(days=max_days)}"
    pt = {"type": "Point", "coordinates": [lon, lat]}
    items = []
    for coll in ("hls2-s30", "hls2-l30", "landsat-c2-l2"):
        items += list(cat.search(collections=[coll], intersects=pt, datetime=dt).items())
    seen = set()
    ranked = []
    for it in items:
        if it.id in seen:
            continue
        seen.add(it.id)
        d = date.fromisoformat(it.properties["datetime"][:10])
        # HLS first at equal distance in time (harmonized), then Landsat C2 L2
        ranked.append((abs((d - day).days), 0 if it.collection_id.startswith("hls") else 1, (d - day).days, it))
    for _, _, offset, it in sorted(ranked, key=lambda t: (t[0], t[1])):
        try:
            px = pixel(it, lon, lat)
        except Exception as exc:  # noqa: BLE001 - a broken asset should not stop the lookup
            print(f"  {it.id}: {exc!r}"[:200])
            continue
        if px:
            px["days_from_scene"] = offset
            return px
    return None


def pct_from_counts(r: dict) -> float | None:
    if r.get("pct_straw"):
        return float(r["pct_straw"])
    try:
        s, b, g = (int(r[k]) for k in ("points_straw", "points_bare", "points_green"))
    except (KeyError, ValueError):
        return None
    n = s + b + g
    return 100.0 * s / n if n else None


def main(src: Path, out: Path, max_days: int) -> None:
    cat = pystac_client.Client.open(STAC)
    with src.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    public = []
    for r in rows:
        pct = pct_from_counts(r)
        day = date.fromisoformat(r["date"])
        px = lookup(cat, float(r["lon"]), float(r["lat"]), day, max_days)
        print(f"{r.get('id')}: {day} cover={pct} -> {px}")
        pts = [r.get(k, "") for k in ("points_straw", "points_bare", "points_green")]
        total = sum(int(p) for p in pts) if all(p.strip().isdigit() for p in pts) else ""
        public.append(
            {
                "id": r.get("id", ""),
                "date": r["date"],
                "method": r.get("method", "rope"),
                "points_total": total,
                "points_straw": pts[0],
                "points_bare": pts[1],
                "points_green": pts[2],
                "pct_straw": "" if pct is None else round(pct, 1),
                "winter_crop": r.get("winter_crop", ""),
                "ndti": "" if not px else round(px["ndti"], 4),
                "ndvi": "" if not px else round(px["ndvi"], 4),
                "scene": "" if not px else px["scene"],
                "days_from_scene": "" if not px else px["days_from_scene"],
            }
        )
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=PUBLIC_COLS)
        w.writeheader()
        w.writerows(public)
    print(f"wrote {out} ({len(public)} rows, no coordinates)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("private_csv", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--max-days", type=int, default=10)
    a = ap.parse_args()
    main(a.private_csv, a.out, a.max_days)
