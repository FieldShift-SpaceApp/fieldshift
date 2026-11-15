# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Farms, grids, cropland mask and slope for one municipality.

    python -I grids.py [--ibge 4306106] [--raw DIR]

- Farms: the CAR outlines of fetch_car.py, active records only (status AT, PE or SU; cancelled CA dropped).
  Each farm gets a sequential number after sorting by a SHA-256 of its CAR code; the code is not kept.
  Size class by fiscal modules (Lei 8.629/1993, art. 4, as amended by Lei 13.465/2017): small <= 4, medium
  > 4 to 15, large > 15.
- Grids: UTM 22S 30 m and 60 m over the farms' bounding box.
- Cropland: ESA WorldCover 2021 v200 class 40 covering >= 50% of the pixel (as in analysis/residue-landsat).
- Slope: NASADEM 1 arc-second, bilinear to the 30 m grid, percent slope from the central-difference gradient
  (as in analysis/residue-landsat/zarcnm.py); IN SPA/MAPA 2/2025 item 6.3 asks for a product of >= 30 m, such as
  NASADEM.
- Farm pixel indices: pixel centres inside each outline (overlapping outlines each keep their pixels).
Writes farms.json, grid.json, static30.npz, farm_idx30.npz and farm_idx60.npz to the raw folder.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject, transform_geom
from rasterio.windows import Window, from_bounds

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    CROPLAND_CLASS,
    CROPLAND_MIN_FRACTION,
    DEFAULT_IBGE,
    DST_CRS,
    STAC,
    WORLDCOVER_COLLECTION,
    gdal_env,
    grid,
    raw_dir,
    write_json,
)

ACTIVE = {"AT", "PE", "SU"}  # ativo, pendente, suspenso; CA = cancelado
PAD_DEG = 0.01


def size_class(m_fiscal: float) -> str:
    if m_fiscal <= 4:
        return "small"
    if m_fiscal <= 15:
        return "medium"
    return "large"


def farm_list(raw):
    data = json.loads((raw / "car.geojson").read_text(encoding="utf-8"))
    rows = []
    for f in data["features"]:
        p = f["properties"]
        if p.get("status_imovel") not in ACTIVE:
            continue
        key = hashlib.sha256(str(p["cod_imovel"]).encode()).hexdigest()
        rows.append((key, f["geometry"], p))
    rows.sort(key=lambda r: r[0])
    farms, geoms = [], []
    for n, (_key, g, p) in enumerate(rows):
        farms.append(
            {
                "farm": n,
                "area_declared_ha": round(float(p["area"]), 2),
                "fiscal_modules": round(float(p["m_fiscal"]), 3),
                "size_class": size_class(float(p["m_fiscal"])),
                "type": p.get("tipo_imovel"),
            }
        )
        geoms.append(g)
    return farms, geoms


def bounds_of(geoms) -> tuple[float, float, float, float]:
    xs, ys = [], []

    def walk(c):
        if isinstance(c[0], (int, float)):
            xs.append(c[0])
            ys.append(c[1])
        else:
            for k in c:
                walk(k)

    for g in geoms:
        walk(g["coordinates"])
    return (min(xs) - PAD_DEG, min(ys) - PAD_DEG, max(xs) + PAD_DEG, max(ys) + PAD_DEG)


def mosaic(cat, collection, bbox, asset, tr, shape, prep, resampling, query=None):
    out = np.full(shape, np.nan, dtype="float32")
    ids = []
    for it in cat.search(collections=[collection], bbox=bbox, query=query).items():
        it = planetary_computer.sign(it)
        ids.append(it.id)
        with gdal_env(), rasterio.open(it.assets[asset].href) as src:
            from rasterio.warp import transform_bounds

            b = transform_bounds("EPSG:4326", src.crs, *bbox)
            win = from_bounds(*b, src.transform).round_offsets().round_lengths()
            win = win.intersection(Window(0, 0, src.width, src.height))
            a = src.read(1, window=win)
            part = np.full(shape, np.nan, dtype="float32")
            reproject(
                prep(a, src.nodata),
                part,
                src_transform=src.window_transform(win),
                src_crs=src.crs,
                dst_transform=tr,
                dst_crs=DST_CRS,
                resampling=resampling,
                src_nodata=np.nan,
                dst_nodata=np.nan,
            )
            out = np.where(np.isnan(out), part, out)
    return out, ids


def farm_indices(geoms, tr, shape, keep: np.ndarray):
    """Flat indices of pixel centres inside each outline, restricted to `keep` (cropland)."""
    idx, lab, total = [], [], []
    h, w = shape
    for n, g in enumerate(geoms):
        gu = transform_geom("EPSG:4326", DST_CRS, g)
        xs, ys = [], []

        def walk(c, xs=xs, ys=ys):
            if isinstance(c[0], (int, float)):
                xs.append(c[0])
                ys.append(c[1])
            else:
                for k in c:
                    walk(k)

        walk(gu["coordinates"])
        win = from_bounds(min(xs), min(ys), max(xs), max(ys), tr).round_offsets(op="floor").round_lengths(op="ceil")
        win = Window(win.col_off, win.row_off, win.width + 1, win.height + 1).intersection(Window(0, 0, w, h))
        r0, c0, hh, ww = int(win.row_off), int(win.col_off), int(win.height), int(win.width)
        inside = ~geometry_mask([gu], out_shape=(hh, ww), transform=rasterio.windows.transform(win, tr))
        rr, cc = np.nonzero(inside)
        flat = (rr + r0) * w + (cc + c0)
        total.append(int(flat.size))
        flat = flat[keep.ravel()[flat]]
        idx.append(flat.astype(np.int64))
        lab.append(np.full(flat.size, n, dtype=np.int32))
    return np.concatenate(idx), np.concatenate(lab), np.array(total)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ibge", default=DEFAULT_IBGE)
    ap.add_argument("--raw", default=None)
    a = ap.parse_args()
    raw = raw_dir(a.ibge, a.raw)
    t0 = time.time()
    farms, geoms = farm_list(raw)
    bbox = bounds_of(geoms)
    tr30, sh30 = grid(bbox, 30.0)
    tr60, sh60 = grid(bbox, 60.0)
    cat = pystac_client.Client.open(STAC)

    crop30, wc_ids = mosaic(
        cat,
        WORLDCOVER_COLLECTION,
        bbox,
        "map",
        tr30,
        sh30,
        lambda arr, nod: (arr == CROPLAND_CLASS).astype("float32"),
        Resampling.average,
        query={"esa_worldcover:product_version": {"eq": "2.0.0"}},
    )
    crop30 = np.nan_to_num(crop30, nan=0.0)
    crop60 = crop30.reshape(sh60[0], 2, sh60[1], 2).mean(axis=(1, 3))

    dem, dem_ids = mosaic(
        cat,
        "nasadem",
        bbox,
        "elevation",
        tr30,
        sh30,
        lambda arr, nod: (
            np.where(arr == nod, np.nan, arr).astype("float32") if nod is not None else arr.astype("float32")
        ),
        Resampling.bilinear,
    )
    gy, gx = np.gradient(dem.astype("float64"), 30.0, 30.0)
    slope30 = (100 * np.hypot(gx, gy)).astype("float32")

    keep30 = crop30 >= CROPLAND_MIN_FRACTION
    keep60 = crop60 >= CROPLAND_MIN_FRACTION
    i30, l30, tot30 = farm_indices(geoms, tr30, sh30, keep30)
    i60, l60, tot60 = farm_indices(geoms, tr60, sh60, keep60)
    for f, t, c30, c60 in zip(
        farms, tot30, np.bincount(l30, minlength=len(farms)), np.bincount(l60, minlength=len(farms)), strict=True
    ):
        f["pixels_30m"] = int(t)
        f["cropland_pixels_30m"] = int(c30)
        f["cropland_pixels_60m"] = int(c60)
        f["cropland_ha"] = round(int(c30) * 0.09, 2)

    np.savez_compressed(raw / "farm_idx30.npz", idx=i30, lab=l30, n=len(farms), shape=np.array(sh30))
    np.savez_compressed(raw / "farm_idx60.npz", idx=i60, lab=l60, n=len(farms), shape=np.array(sh60))
    np.savez_compressed(raw / "static30.npz", crop30=crop30, slope30=slope30, dem30=dem)
    (raw / "farm_geoms.json").write_text(json.dumps(geoms), encoding="utf-8")
    write_json(raw / "farms.json", farms)
    write_json(
        raw / "grid.json",
        {
            "ibge": a.ibge,
            "bbox": bbox,
            "crs": DST_CRS,
            "tr30": list(tr30)[:6],
            "shape30": list(sh30),
            "tr60": list(tr60)[:6],
            "shape60": list(sh60),
            "worldcover_items": wc_ids,
            "nasadem_items": dem_ids,
            "seconds": round(time.time() - t0, 1),
        },
    )
    n_crop = sum(1 for f in farms if f["cropland_pixels_30m"] > 0)
    print(f"{len(farms)} active farms, {n_crop} with cropland; grid30 {sh30}; {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
