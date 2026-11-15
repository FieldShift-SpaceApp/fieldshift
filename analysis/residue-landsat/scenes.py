# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Per-scene NDVI x NDTI histograms of Cruz Alta cropland, Landsat Collection 2 Level-2 and HLS v2.0.

For every clear-enough scene in the two windows (20 Oct - 20 Nov and 1 Apr - 31 May), reads red, NIR,
SWIR1, SWIR2 and the QA band through the Microsoft Planetary Computer (anonymous SAS token, no account),
masks clouds, shadows, water and fill, keeps ESA WorldCover 2021 cropland (class 40, >= 50% of the
pixel) inside the IBGE polygon of municipality 4306106, and stores a 2-D histogram of (NDVI, NDTI).
Every threshold is applied later (series.py), so the sensitivity runs never re-read the imagery.

    python -I scenes.py <raw_dir>

Writes one small JSON per scene to <raw_dir>/scenes/ (resumable; never committed) and
<raw_dir>/scene_index.json (search log). Nothing raw is kept: windows are read at about 60 m.
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.warp import reproject, transform_bounds, transform_geom
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[2]
GEOM_PATH = ROOT / "data" / "dev" / "dev-cruz-alta" / "ibge" / "malha_municipio_4306106_2022.geojson"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
BBOX = (-53.80, -28.96, -53.24, -28.48)  # covers the municipality polygon
WORLDCOVER_ITEM = "ESA_WorldCover_10m_2021_v200_S30W054"
DECIM = 2  # 30 m -> about 60 m
MAX_TILE_CLOUD = 70  # search filter on scene/tile cloud cover; the real filter is the clear cropland share
WORKERS = 24  # parallel scene reads (network-bound)
WINDOWS = {"spring": ("10-20", "11-20"), "autumn": ("04-01", "05-31")}

# 2-D histogram grid; every threshold used later falls on an edge
NDVI_EDGES = np.round(np.arange(-0.20, 1.0001, 0.01), 3)
NDTI_EDGES = np.round(np.arange(-0.20, 0.4001, 0.005), 3)

BANDS = {
    "hls2-s30": {"red": "B04", "nir": "B8A", "sw1": "B11", "sw2": "B12", "qa": "Fmask"},
    "hls2-l30": {"red": "B04", "nir": "B05", "sw1": "B06", "sw2": "B07", "qa": "Fmask"},
    "landsat-c2-l2": {"red": "red", "nir": "nir08", "sw1": "swir16", "sw2": "swir22", "qa": "qa_pixel"},
}

# Roy et al. (2016), Table 2 OLS, ETM+ -> OLI surface reflectance (red, NIR, SWIR1, SWIR2), as published
# in the Google Earth Engine community tutorial "landsat-etm-to-oli-harmonization". Applied to TM and ETM+
# only as a sensitivity run (the coefficients were fitted on ETM+/OLI pairs, not TM).
ROY2016_ETM_TO_OLI = {
    "red": (0.0061, 0.9047),
    "nir": (0.0412, 0.8462),
    "sw1": (0.0254, 0.8937),
    "sw2": (0.0172, 0.9071),
}


def season_of(dt: str) -> str | None:
    md = dt[5:10]
    for name, (a, b) in WINDOWS.items():
        if a <= md <= b:
            return name
    return None


def load_geom() -> dict:
    g = json.loads(GEOM_PATH.read_text(encoding="utf-8"))
    return g["features"][0]["geometry"] if "features" in g else g


def read_window(href: str, out_shape=None, resampling=Resampling.average):
    with rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        GDAL_HTTP_MAX_RETRY="4",
        GDAL_HTTP_RETRY_DELAY="2",
        GDAL_HTTP_TIMEOUT="60",
    ):
        with rasterio.open(href) as src:
            b = transform_bounds("EPSG:4326", src.crs, *BBOX)
            win = from_bounds(*b, src.transform).round_offsets().round_lengths()
            if out_shape is None:
                out_shape = (max(1, int(win.height // DECIM)), max(1, int(win.width // DECIM)))
            fill = src.nodata if src.nodata is not None else 0
            arr = src.read(1, window=win, out_shape=out_shape, resampling=resampling, boundless=True, fill_value=fill)
            tr = src.window_transform(win) * rasterio.Affine.scale(win.width / out_shape[1], win.height / out_shape[0])
            return arr, tr, src.crs, out_shape


def valid_mask(coll: str, qa: np.ndarray) -> np.ndarray:
    qa = qa.astype(np.int64)
    if coll.startswith("hls"):
        # Fmask bits: 1 cloud, 2 adjacent to cloud/shadow, 3 cloud shadow, 4 snow/ice, 5 water; 255 = fill
        return (((qa >> 1) & 0b11111) == 0) & (qa != 255)
    # Landsat C2 QA_PIXEL: bit 0 fill, 1 dilated cloud, 3 cloud, 4 cloud shadow, 5 snow, 6 clear, 7 water
    bad = (qa & 1) | ((qa >> 1) & 1) | ((qa >> 3) & 1) | ((qa >> 4) & 1) | ((qa >> 5) & 1) | ((qa >> 7) & 1)
    return (bad == 0) & (((qa >> 6) & 1) == 1)


def reflect(coll: str, arr: np.ndarray) -> np.ndarray:
    a = arr.astype("float32")
    if coll.startswith("hls"):
        a[arr == -9999] = np.nan
        return a * 1e-4
    a[arr == 0] = np.nan
    return a * 2.75e-5 - 0.2


def hist2d(ndvi: np.ndarray, ndti: np.ndarray) -> dict:
    h, _, _ = np.histogram2d(ndvi, ndti, bins=[NDVI_EDGES, NDTI_EDGES])
    # values outside the grid are clipped into the edge bins so no pixel is lost
    h = h.astype(np.int64)
    out_lo_v = int((ndvi < NDVI_EDGES[0]).sum())
    out_hi_v = int((ndvi >= NDVI_EDGES[-1]).sum())
    i, j = np.nonzero(h)
    return {
        "sparse": [[int(a), int(b), int(h[a, b])] for a, b in zip(i, j, strict=True)],
        "ndvi_below_grid": out_lo_v,
        "ndvi_above_grid": out_hi_v,
        "ndti_below_grid": int((ndti < NDTI_EDGES[0]).sum()),
        "ndti_above_grid": int((ndti >= NDTI_EDGES[-1]).sum()),
    }


def clip_to_grid(ndvi: np.ndarray, ndti: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    eps = 1e-6
    return (
        np.clip(ndvi, NDVI_EDGES[0], NDVI_EDGES[-1] - eps),
        np.clip(ndti, NDTI_EDGES[0], NDTI_EDGES[-1] - eps),
    )


def scene_stats(item, geom: dict, wc) -> dict:
    coll = item.collection_id
    bmap = BANDS[coll]
    signed = planetary_computer.sign(item)
    qa, tr, crs, shape = read_window(signed.assets[bmap["qa"]].href, resampling=Resampling.nearest)
    raw = {}
    for k in ("red", "nir", "sw1", "sw2"):
        a, _, _, _ = read_window(signed.assets[bmap[k]].href, out_shape=shape)
        raw[k] = reflect(coll, a)
    ok = valid_mask(coll, qa)
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

    def indices(b: dict) -> tuple[np.ndarray, np.ndarray]:
        with np.errstate(invalid="ignore", divide="ignore"):
            return (b["nir"] - b["red"]) / (b["nir"] + b["red"]), (b["sw1"] - b["sw2"]) / (b["sw1"] + b["sw2"])

    ndvi, ndti = indices(raw)
    good = cropland & ok & np.isfinite(ndvi) & np.isfinite(ndti)
    p = item.properties
    out = {
        "id": item.id,
        "collection": coll,
        "platform": p.get("platform"),
        "datetime": p["datetime"],
        "date": p["datetime"][:10],
        "season": season_of(p["datetime"]),
        "tile_cloud_cover": p.get("eo:cloud_cover"),
        "wrs_path_row": f"{p['landsat:wrs_path']}/{p['landsat:wrs_row']}" if "landsat:wrs_path" in p else None,
        "mgrs_tile": item.id.split(".")[2] if coll.startswith("hls") else None,
        "stac_item": f"{STAC}/collections/{coll}/items/{item.id}",
        "pixel_m": 30 * DECIM,
        "cropland_pixels_municipality": int(cropland.sum()),
        "valid_cropland_pixels": int(good.sum()),
    }
    v, t = clip_to_grid(ndvi[good], ndti[good])
    out["hist"] = hist2d(v, t)
    if coll == "landsat-c2-l2" and p.get("platform") in ("landsat-4", "landsat-5", "landsat-7"):
        harm = {k: ROY2016_ETM_TO_OLI[k][0] + ROY2016_ETM_TO_OLI[k][1] * raw[k] for k in raw}
        hv, ht = indices(harm)
        hv, ht = clip_to_grid(hv[good], ht[good])
        out["hist_roy2016"] = hist2d(hv, ht)
    return out


def search(cat) -> list:
    items = []
    q = {"eo:cloud_cover": {"lt": MAX_TILE_CLOUD}}
    for it in cat.search(collections=["landsat-c2-l2"], bbox=BBOX, datetime="1984-01-01/2026-12-31", query=q).items():
        p = it.properties
        if (p["landsat:wrs_path"], p["landsat:wrs_row"]) in (("223", "080"), ("222", "080")) and season_of(
            p["datetime"]
        ):
            items.append(it)
    for coll in ("hls2-l30", "hls2-s30"):
        for it in cat.search(collections=[coll], bbox=BBOX, datetime="2013-01-01/2026-12-31", query=q).items():
            if season_of(it.properties["datetime"]) and it.id.split(".")[2] in ("T22JBP", "T22JBN"):
                items.append(it)
    return items


def main(raw: Path) -> None:
    out_dir = raw / "scenes"
    out_dir.mkdir(parents=True, exist_ok=True)
    geom = load_geom()
    cat = pystac_client.Client.open(STAC)
    wc_item = planetary_computer.sign(cat.get_collection("esa-worldcover").get_item(WORLDCOVER_ITEM))
    with rasterio.open(wc_item.assets["map"].href) as src:
        win = from_bounds(*BBOX, src.transform).round_offsets().round_lengths()
        wc = (src.read(1, window=win), src.window_transform(win), src.crs)
    searched_at = datetime.now(UTC).isoformat(timespec="seconds")
    items = search(cat)
    print(f"{len(items)} candidate scenes", flush=True)
    index = {
        "searched_utc": searched_at,
        "stac": STAC,
        "bbox": BBOX,
        "windows": WINDOWS,
        "max_tile_cloud_cover": MAX_TILE_CLOUD,
        "landsat_wrs": ["223/080", "222/080"],
        "hls_tiles": ["T22JBP", "T22JBN"],
        "worldcover_item": WORLDCOVER_ITEM,
        "ndvi_edges": NDVI_EDGES.tolist(),
        "ndti_edges": NDTI_EDGES.tolist(),
        "items": [it.id for it in items],
        "errors": {},
    }
    (raw / "scene_index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")
    todo = [it for it in items if not (out_dir / f"{it.id}.json").exists()]
    print(f"{len(todo)} to read ({len(items) - len(todo)} cached)", flush=True)

    def work(it):
        for attempt in range(3):
            try:
                return it.id, scene_stats(it, geom, wc), None
            except Exception as exc:  # noqa: BLE001 - logged and retried, then recorded
                err = repr(exc)[:300]
                time.sleep(3 * (attempt + 1))
        return it.id, None, err

    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for fut in as_completed([ex.submit(work, it) for it in todo]):
            iid, st, err = fut.result()
            done += 1
            if st is None:
                index["errors"][iid] = err
                print(f"[{done}/{len(todo)}] {iid} ERROR {err}", flush=True)
                continue
            (out_dir / f"{iid}.json").write_text(json.dumps(st), encoding="utf-8")
            if done % 20 == 0 or done == len(todo):
                print(f"[{done}/{len(todo)}] {iid} valid={st['valid_cropland_pixels']}", flush=True)
    (raw / "scene_index.json").write_text(json.dumps(index, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
