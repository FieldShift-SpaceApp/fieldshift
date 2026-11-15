# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Per-granule 30 m NDVI of every Cruz Alta cropland pixel, NASA HLS v2.0 (L30 + S30), April - November 2020-2026.

    python -I scenes.py <raw_dir>

Reads, for every HLS granule of MGRS tile T22JBP (the tile alone covers the whole municipality) acquired from
1 April to 30 November, the red band, the NIR band and the Fmask quality layer through the Microsoft Planetary
Computer STAC (anonymous SAS token, no account), on the native 30 m UTM zone 22 grid of the tile (no resampling).
Keeps only ESA WorldCover 2021 cropland (class 40 covering >= 50% of the 30 m pixel) inside the IBGE polygon of
municipality 4306106. A granule is skipped without reading the bands when fewer than MIN_CLEAR of those cropland
pixels are clear in Fmask.

Writes to <raw_dir> (never committed): grid.npz (grid, cropland pixel index), ndvi/<granule>.npz (NDVI x 10000
as int16 for each cropland pixel, -32768 = cloud/shadow/water/no data), scene_index.json (search log, one row per
granule with its clear share). Resumable: granules already on disk are not read again.
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
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds, transform_geom
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[2]
GEOM_PATH = ROOT / "data" / "dev" / "dev-cruz-alta" / "ibge" / "malha_municipio_4306106_2022.geojson"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
BBOX = (-53.80, -28.96, -53.24, -28.48)  # covers the municipality polygon (same box as analysis/residue-landsat)
TILE = "T22JBP"  # MGRS tile; T22JBN repeats the same acquisitions and adds nothing inside the box
CRS = "EPSG:32622"  # native CRS of the HLS tiles of UTM zone 22 (northing negative in the south)
RES = 30.0
YEARS = range(2020, 2027)  # Planetary Computer: no Apr-Nov 2019 granule of this tile, S30 starts 2020
SEASON = ("04-01", "11-30")
MAX_TILE_CLOUD = 90  # search filter only; the real filter is the clear share of the cropland pixels
MIN_CLEAR = 0.02  # granules with < 2% of cropland pixels clear are logged and skipped
WORLDCOVER_ITEM = "ESA_WorldCover_10m_2021_v200_S30W054"
NODATA = -32768
WORKERS = 24
BANDS = {
    "hls2-s30": {"red": "B04", "nir": "B8A", "qa": "Fmask"},  # B8A (narrow NIR) is the band HLS harmonises to OLI
    "hls2-l30": {"red": "B04", "nir": "B05", "qa": "Fmask"},
}


def load_geom() -> dict:
    g = json.loads(GEOM_PATH.read_text(encoding="utf-8"))
    return g["features"][0]["geometry"] if "features" in g else g


def grid() -> tuple:
    """30 m grid aligned with the HLS tile grid (tile origins are multiples of 30 m)."""
    b = transform_bounds("EPSG:4326", CRS, *BBOX)
    x0, y1 = np.floor(b[0] / RES) * RES, np.ceil(b[3] / RES) * RES
    w, h = int(np.ceil((b[2] - x0) / RES)), int(np.ceil((y1 - b[1]) / RES))
    return from_origin(x0, y1, RES, RES), (h, w)


def env():
    return rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        GDAL_HTTP_MAX_RETRY="5",
        GDAL_HTTP_RETRY_DELAY="3",
        GDAL_HTTP_TIMEOUT="120",
    )


def read(href: str, tr, shape) -> np.ndarray:
    with env(), rasterio.open(href) as src:
        if abs(src.transform.a - RES) > 1e-6 or (src.transform.c - tr.c) % RES or (src.transform.f - tr.f) % RES:
            raise ValueError(f"grid of {href} is not aligned with the analysis grid")
        win = from_bounds(tr.c, tr.f - shape[0] * RES, tr.c + shape[1] * RES, tr.f, src.transform)
        win = win.round_offsets().round_lengths()
        fill = src.nodata if src.nodata is not None else 255
        return src.read(1, window=win, boundless=True, fill_value=fill)


def cropland_index(cat, tr, shape) -> tuple[np.ndarray, np.ndarray]:
    item = planetary_computer.sign(cat.get_collection("esa-worldcover").get_item(WORLDCOVER_ITEM))
    frac = np.zeros(shape, dtype="float32")
    with env(), rasterio.open(item.assets["map"].href) as src:
        win = from_bounds(*BBOX, src.transform).round_offsets().round_lengths()
        wc, wc_tr = src.read(1, window=win), src.window_transform(win)
        reproject(
            (wc == 40).astype("float32"),
            frac,
            src_transform=wc_tr,
            src_crs=src.crs,
            dst_transform=tr,
            dst_crs=CRS,
            resampling=Resampling.average,
        )
    inside = ~geometry_mask([transform_geom("EPSG:4326", CRS, load_geom())], out_shape=shape, transform=tr)
    return np.flatnonzero((inside & (frac >= 0.5)).ravel()), inside


def clear(qa: np.ndarray) -> np.ndarray:
    # HLS v2.0 Fmask bits: 1 cloud, 2 adjacent to cloud/shadow, 3 cloud shadow, 4 snow/ice, 5 water; 255 = fill
    q = qa.astype(np.int64)
    return (((q >> 1) & 0b11111) == 0) & (q != 255)


def process(item, tr, shape, idx: np.ndarray, out: Path) -> dict:
    coll = item.collection_id
    b = BANDS[coll]
    p = item.properties
    row = {
        "id": item.id,
        "collection": coll,
        "date": p["datetime"][:10],
        "datetime": p["datetime"],
        "tile_cloud_cover": p.get("eo:cloud_cover"),
        "stac_item": f"{STAC}/collections/{coll}/items/{item.id}",
    }
    signed = planetary_computer.sign(item)
    for attempt in range(3):
        try:
            ok = clear(read(signed.assets[b["qa"]].href, tr, shape)).ravel()[idx]
            row["clear_share"] = round(float(ok.mean()), 4)
            if row["clear_share"] < MIN_CLEAR:
                row["status"] = "skipped_cloudy"
                return row
            red = read(signed.assets[b["red"]].href, tr, shape).ravel()[idx].astype("float32")
            nir = read(signed.assets[b["nir"]].href, tr, shape).ravel()[idx].astype("float32")
            break
        except Exception as e:  # network errors: retry, then log
            if attempt == 2:
                row["status"] = f"error: {type(e).__name__}: {e}"[:300]
                return row
            time.sleep(5 * (attempt + 1))
    good = ok & (red > 0) & (nir > 0) & (red != -9999) & (nir != -9999)
    with np.errstate(invalid="ignore", divide="ignore"):
        ndvi = (nir - red) / (nir + red)  # scale factor 1e-4 cancels in the ratio
    good &= np.isfinite(ndvi)
    v = np.full(idx.size, NODATA, dtype=np.int16)
    v[good] = np.round(np.clip(ndvi[good], -1, 1) * 10000).astype(np.int16)
    np.savez_compressed(out, ndvi=v)
    row["status"] = "ok"
    row["valid_share"] = round(float(good.mean()), 4)
    return row


def main() -> None:
    raw = Path(sys.argv[1])
    (raw / "ndvi").mkdir(parents=True, exist_ok=True)
    cat = pystac_client.Client.open(STAC)
    tr, shape = grid()
    if (raw / "grid.npz").exists():
        idx = np.load(raw / "grid.npz")["idx"]
    else:
        idx, inside = cropland_index(cat, tr, shape)
        np.savez_compressed(raw / "grid.npz", idx=idx, inside=inside, transform=np.array(tr)[:6], shape=np.array(shape))
    print(f"grid {shape}, cropland pixels {idx.size} ({idx.size * RES * RES / 1e4:,.0f} ha)", flush=True)

    searched_at = datetime.now(UTC).isoformat(timespec="seconds")
    items = []
    for coll in BANDS:
        for y in YEARS:
            dt = f"{y}-{SEASON[0]}/{y}-{SEASON[1]}"
            q = {"eo:cloud_cover": {"lt": MAX_TILE_CLOUD}}
            for it in cat.search(collections=[coll], bbox=BBOX, datetime=dt, query=q).items():
                if it.id.split(".")[2] == TILE:
                    items.append(it)
    items.sort(key=lambda i: i.properties["datetime"])
    print(f"{len(items)} granules of {TILE}", flush=True)

    index_path = raw / "scene_index.json"
    done = {}
    if index_path.exists():
        done = {r["id"]: r for r in json.loads(index_path.read_text(encoding="utf-8"))["granules"]}
    todo = [
        it
        for it in items
        if not ((raw / "ndvi" / f"{it.id}.npz").exists() or done.get(it.id, {}).get("status") == "skipped_cloudy")
    ]
    print(f"{len(todo)} to read", flush=True)
    t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(process, it, tr, shape, idx, raw / "ndvi" / f"{it.id}.npz"): it for it in todo}
        for k, f in enumerate(as_completed(futs), 1):
            r = f.result()
            done[r["id"]] = r
            if k % 20 == 0 or k == len(todo):
                el = time.time() - t0
                print(f"{k}/{len(todo)} {el / 60:.1f} min, last {r['id']} {r['status']}", flush=True)
                index_path.write_text(json.dumps({"granules": list(done.values())}, indent=1), encoding="utf-8")
    for it in items:  # granules read in an earlier run keep their row
        done.setdefault(it.id, {"id": it.id, "status": "ok", "date": it.properties["datetime"][:10]})
    doc = {
        "searched_at_utc": searched_at,
        "stac": STAC,
        "collections": list(BANDS),
        "tile": TILE,
        "bbox_wgs84": BBOX,
        "season": SEASON,
        "years": list(YEARS),
        "max_tile_cloud_search_filter": MAX_TILE_CLOUD,
        "min_clear_share_of_cropland": MIN_CLEAR,
        "grid": {"crs": CRS, "res_m": RES, "shape": list(shape), "transform": list(np.array(tr)[:6])},
        "cropland_pixels": int(idx.size),
        "granules": sorted(done.values(), key=lambda r: r.get("date", "")),
    }
    index_path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    st = [r["status"] for r in done.values()]
    print({s: st.count(s) for s in set(st)}, flush=True)


if __name__ == "__main__":
    main()
