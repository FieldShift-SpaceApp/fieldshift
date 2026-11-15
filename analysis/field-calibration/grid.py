# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""A small NDTI / NDVI lookup grid of Cruz Alta cropland for the app's /calibrate screen (NASA HLS, spring 2026).

The app cannot call the Planetary Computer from the farmer's phone without sending the point somewhere, so it
looks the point up in this file instead: every clear HLS S30 / L30 scene of 1 September - 15 November 2026 over
the municipality, read at about 60 m (the same reader as ../residue-landsat/scenes.py), masked to clear
WorldCover 2021 cropland inside the IBGE polygon, then summarised per grid cell of 0.005 degrees (about 490 m x
550 m) as the median NDTI of its no-green pixels (NDVI < 0.30, where straw can be read), the median NDVI and the
no-green share of its clear cropland pixels.

    python -I grid.py [--out results/cruz_alta_ndti_grid_2026.json]

What the app gets is a cell median, not the pixel under the farmer's rope: the 15 m rope samples one spot of a
field, the cell mixes several fields. ``fetch_pixel.py`` reads the 30 m pixel itself for the analysis.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject, transform, transform_geom
from rasterio.windows import from_bounds

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "residue-landsat"))
import scenes as rl  # noqa: E402  (reader shared with ../residue-landsat, on main)

DATES = "2026-09-01/2026-11-15"
CELL = 0.005  # degrees
MIN_PIX = 12  # clear cropland pixels (about 60 m) needed for a cell value (of about 75 per cell)
MIN_SCENE_CLEAR = 0.30  # share of the municipality's cropland that must be clear for a scene to be kept
MAX_TILE_CLOUD = 60
NDVI_GREEN = 0.30  # Documentos 454 masks NDVI > 0.3 before reading straw; same as ../residue-landsat
MIN_NOGREEN = 6  # no-green pixels needed for a straw NDTI in a cell


def scene_cells(item, geom: dict, wc) -> tuple[dict, dict]:
    coll = item.collection_id
    bmap = rl.BANDS[coll]
    signed = planetary_computer.sign(item)
    qa, tr, crs, shape = rl.read_window(signed.assets[bmap["qa"]].href, resampling=Resampling.nearest)
    raw = {}
    for k in ("red", "nir", "sw1", "sw2"):
        a, _, _, _ = rl.read_window(signed.assets[bmap[k]].href, out_shape=shape)
        raw[k] = rl.reflect(coll, a)
    ok = rl.valid_mask(coll, qa)
    inside = ~geometry_mask([transform_geom("EPSG:4326", crs, geom)], out_shape=shape, transform=tr)
    wc_arr, wc_tr, wc_crs = wc
    crop = np.zeros(shape, dtype="float32")
    reproject(
        (wc_arr == 40).astype("float32"),
        crop,
        src_transform=wc_tr,
        src_crs=wc_crs,
        dst_transform=tr,
        dst_crs=crs,
        resampling=Resampling.average,
    )
    cropland = inside & (crop >= 0.5)
    with np.errstate(invalid="ignore", divide="ignore"):
        ndvi = (raw["nir"] - raw["red"]) / (raw["nir"] + raw["red"])
        ndti = (raw["sw1"] - raw["sw2"]) / (raw["sw1"] + raw["sw2"])
    good = cropland & ok & np.isfinite(ndvi) & np.isfinite(ndti)
    rows, cols = np.nonzero(good)
    xs, ys = rasterio.transform.xy(tr, rows, cols)
    lon, lat = transform(crs, "EPSG:4326", list(np.atleast_1d(xs)), list(np.atleast_1d(ys)))
    lon = np.asarray(lon)
    lat = np.asarray(lat)
    ci = np.floor((lat - rl.BBOX[1]) / CELL).astype(int)
    cj = np.floor((lon - rl.BBOX[0]) / CELL).astype(int)
    vals = defaultdict(list)
    for a, b, t, v in zip(ci, cj, ndti[rows, cols], ndvi[rows, cols], strict=True):
        vals[(int(a), int(b))].append((float(t), float(v)))
    meta = {"cropland_pixels": int(cropland.sum()), "clear_cropland_pixels": int(good.sum())}
    return vals, meta


def main(out: Path) -> None:
    geom = rl.load_geom()
    cat = pystac_client.Client.open(rl.STAC)
    wc_item = planetary_computer.sign(cat.get_collection("esa-worldcover").get_item(rl.WORLDCOVER_ITEM))
    with rasterio.open(wc_item.assets["map"].href) as src:
        win = from_bounds(*rl.BBOX, src.transform).round_offsets().round_lengths()
        wc = (src.read(1, window=win), src.window_transform(win), src.crs)
    searched = datetime.now(UTC).isoformat(timespec="seconds")
    items = []
    for coll in ("hls2-s30", "hls2-l30"):
        q = {"eo:cloud_cover": {"lt": MAX_TILE_CLOUD}}
        for it in cat.search(collections=[coll], bbox=rl.BBOX, datetime=DATES, query=q).items():
            if it.id.split(".")[2] in ("T22JBP", "T22JBN"):
                items.append(it)
    print(f"{len(items)} candidate tiles", flush=True)
    by_day = defaultdict(list)
    for it in items:
        by_day[(it.properties["datetime"][:10], it.collection_id)].append(it)

    scenes_out = []
    cell_vals: dict[tuple[int, int], dict[int, tuple[float, float]]] = defaultdict(dict)
    for (day, coll), its in sorted(by_day.items()):
        merged = defaultdict(list)
        crop_px = 0
        clear_px = 0
        for it in its:
            try:
                vals, meta = scene_cells(it, geom, wc)
            except Exception as exc:  # noqa: BLE001 - one bad tile does not stop the grid
                print(f"{it.id} ERROR {exc!r}"[:300], flush=True)
                continue
            crop_px = max(crop_px, meta["cropland_pixels"])
            clear_px = max(clear_px, meta["clear_cropland_pixels"])
            for k, v in vals.items():
                merged[k].extend(v)
        clear_share = clear_px / crop_px if crop_px else 0.0
        print(f"{day} {coll} tiles={len(its)} clear_share~{clear_share:.2f} cells={len(merged)}", flush=True)
        if clear_share < MIN_SCENE_CLEAR:
            continue
        idx = len(scenes_out)
        scenes_out.append(
            {
                "date": day,
                "sensor": "HLS S30" if coll == "hls2-s30" else "HLS L30",
                "items": sorted(it.id for it in its),
                "clear_cropland_share_approx": round(clear_share, 3),
            }
        )
        for k, v in merged.items():
            if len(v) >= MIN_PIX:
                arr = np.array(v)
                nogreen = arr[:, 1] < NDVI_GREEN
                t_ng = float(np.median(arr[nogreen, 0])) if nogreen.sum() >= MIN_NOGREEN else None
                cell_vals[k][idx] = (t_ng, float(np.median(arr[:, 1])), float(nogreen.mean()))

    cells = {}
    for (i, j), d in sorted(cell_vals.items()):
        cells[f"{i}_{j}"] = [
            None
            if s not in d
            else [None if d[s][0] is None else round(d[s][0] * 1000), round(d[s][1] * 1000), round(d[s][2] * 100)]
            for s in range(len(scenes_out))
        ]
    doc = {
        "what": "NDTI of no-green pixels, NDVI and no-green share of clear WorldCover-2021 cropland pixels "
        "(about 60 m) per 0.005-degree cell, "
        "Cruz Alta (IBGE 4306106), every HLS v2.0 scene of the window with >= 30% of the cropland clear",
        "window": DATES,
        "searched_utc": searched,
        "stac": rl.STAC,
        "collections": ["hls2-s30", "hls2-l30"],
        "tiles": ["T22JBP", "T22JBN"],
        "cell_deg": CELL,
        "origin_lon_lat": [rl.BBOX[0], rl.BBOX[1]],
        "cell_key": "i_j with i = floor((lat - origin_lat) / cell_deg), j = floor((lon - origin_lon) / cell_deg)",
        "min_clear_pixels_per_cell": MIN_PIX,
        "value": "per scene: [1000 * median NDTI of the no-green pixels (NDVI < 0.30; null if fewer than "
        f"{MIN_NOGREEN}), 1000 * median NDVI of all clear cropland pixels, % of clear cropland pixels that are "
        "no-green]; null where the cell was cloudy or had too few clear cropland pixels",
        "scenes": scenes_out,
        "cells": cells,
        "attribution": "NASA HLS v2.0 (LP DAAC; doi:10.5067/HLS/HLSS30.002, 10.5067/HLS/HLSL30.002) via Microsoft "
        "Planetary Computer; ESA WorldCover 2021 v200 (CC BY 4.0); IBGE municipal mesh 2022",
        "caveat": "a cell median mixes fields; it is not the pixel under a 15 m rope",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {out} scenes={len(scenes_out)} cells={len(cells)} bytes={out.stat().st_size}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=HERE / "results" / "cruz_alta_ndti_grid_2026.json")
    main(ap.parse_args().out)
