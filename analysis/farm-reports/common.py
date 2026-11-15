# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Shared constants and helpers of the farm-report pipeline (one municipality at a time).

Grids: UTM 22S (EPSG:32722), 30 m (straw cover now, slope) and 60 m (the 1984-2026 bare-soil series and the
2020-2026 winter fingerprint, read from 2x decimated windows like analysis/residue-landsat/scenes.py).
Imagery is read anonymously through the Microsoft Planetary Computer STAC (no account).
Nothing raw is committed: every step writes to the raw folder (default ~/.cache/fieldshift/farm-reports/<ibge>).
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject, transform_bounds
from rasterio.windows import from_bounds

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1"
DST_CRS = "EPSG:32722"
WORLDCOVER_COLLECTION = "esa-worldcover"
CROPLAND_CLASS = 40  # ESA WorldCover 2021 "Cropland"
CROPLAND_MIN_FRACTION = 0.5  # same rule as analysis/residue-landsat and the team's bare-soil calendar

# Same pixel classes and thresholds as analysis/residue-landsat (PR #54): green NDVI >= 0.30; straw NDVI < 0.30
# and NDTI >= 0.06; probable bare soil NDVI < 0.30 and NDTI < 0.06.
NDVI_GREEN = 0.30
NDTI_BARE = 0.06

BANDS = {
    "hls2-s30": {"red": "B04", "nir": "B8A", "sw1": "B11", "sw2": "B12", "qa": "Fmask"},
    "hls2-l30": {"red": "B04", "nir": "B05", "sw1": "B06", "sw2": "B07", "qa": "Fmask"},
    "landsat-c2-l2": {"red": "red", "nir": "nir08", "sw1": "swir16", "sw2": "swir22", "qa": "qa_pixel"},
}
LANDSAT_PATH_ROWS = {("223", "080"), ("222", "080")}  # WRS-2 scenes over Cruz Alta (as in residue-landsat)
HLS_TILES = {"T22JBP", "T22JBN"}

DEFAULT_IBGE = "4306106"  # Cruz Alta (RS)


def raw_dir(ibge: str, override: str | None = None) -> Path:
    p = Path(override) if override else Path.home() / ".cache" / "fieldshift" / "farm-reports" / ibge
    p.mkdir(parents=True, exist_ok=True)
    return p


def write_json(path: Path, obj) -> None:
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=1, allow_nan=False) + "\n", encoding="utf-8", newline="\n"
    )


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def grid(bbox: tuple[float, float, float, float], res: float):
    """(transform, (rows, cols)) of a north-up grid in DST_CRS covering a lon/lat bbox; 30 m and 60 m align."""
    b = transform_bounds("EPSG:4326", DST_CRS, *bbox)
    x0 = np.floor(b[0] / 60.0) * 60.0
    y1 = np.ceil(b[3] / 60.0) * 60.0
    w = int(np.ceil((b[2] - x0) / 60.0)) * int(60 / res)
    h = int(np.ceil((y1 - b[1]) / 60.0)) * int(60 / res)
    return from_origin(x0, y1, res, res), (h, w)


def gdal_env():
    return rasterio.Env(
        GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
        GDAL_HTTP_MAX_RETRY="5",
        GDAL_HTTP_RETRY_DELAY="3",
        GDAL_HTTP_TIMEOUT="90",
        GDAL_HTTP_MULTIRANGE="YES",
        GDAL_HTTP_MERGE_CONSECUTIVE_RANGES="YES",
        VSI_CACHE="FALSE",
    )


def read_to_grid(href: str, bbox, dst_tr, dst_shape, decim: int, resampling: Resampling) -> np.ndarray:
    """Read the window of a COG that covers bbox (decimated `decim` times, using its overviews), then put it on
    the destination grid with nearest neighbour. Returns float32 with NaN where the source is nodata/outside."""
    with gdal_env(), rasterio.open(href) as src:
        b = transform_bounds("EPSG:4326", src.crs, *bbox)
        win = from_bounds(*b, src.transform).round_offsets().round_lengths()
        out_shape = (max(1, int(win.height // decim)), max(1, int(win.width // decim)))
        nod = src.nodata
        arr = src.read(1, window=win, out_shape=out_shape, resampling=resampling, boundless=True, fill_value=nod or 0)
        tr = src.window_transform(win) * rasterio.Affine.scale(win.width / out_shape[1], win.height / out_shape[0])
        a = arr.astype("float32")
        if nod is not None:
            a[arr == nod] = np.nan
        out = np.full(dst_shape, np.nan, dtype="float32")
        reproject(
            a,
            out,
            src_transform=tr,
            src_crs=src.crs,
            dst_transform=dst_tr,
            dst_crs=DST_CRS,
            resampling=Resampling.nearest,
            src_nodata=np.nan,
            dst_nodata=np.nan,
        )
        return out


def valid_mask(coll: str, qa: np.ndarray) -> np.ndarray:
    """Clear land pixels. Same bit rules as analysis/residue-landsat/scenes.py."""
    ok = np.isfinite(qa)
    q = np.where(ok, qa, 0).astype(np.int64)
    if coll.startswith("hls"):
        # Fmask bits: 1 cloud, 2 adjacent to cloud/shadow, 3 cloud shadow, 4 snow/ice, 5 water; 255 = fill
        return ok & (((q >> 1) & 0b11111) == 0) & (q != 255)
    # Landsat C2 QA_PIXEL: bit 0 fill, 1 dilated cloud, 3 cloud, 4 cloud shadow, 5 snow, 6 clear, 7 water
    bad = (q & 1) | ((q >> 1) & 1) | ((q >> 3) & 1) | ((q >> 4) & 1) | ((q >> 5) & 1) | ((q >> 7) & 1)
    return ok & (bad == 0) & (((q >> 6) & 1) == 1)


def reflect(coll: str, a: np.ndarray) -> np.ndarray:
    if coll.startswith("hls"):
        a = np.where(a == -9999, np.nan, a)
        return a * 1e-4
    a = np.where(a == 0, np.nan, a)
    return a * 2.75e-5 - 0.2


def nd(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return (a - b) / (a + b)


def item_keep(item) -> bool:
    """Landsat WRS-2 223/080 and 222/080, HLS MGRS tiles T22JBP/T22JBN."""
    if item.collection_id == "landsat-c2-l2":
        p = item.properties
        return (p["landsat:wrs_path"], p["landsat:wrs_row"]) in LANDSAT_PATH_ROWS
    return item.id.split(".")[2] in HLS_TILES


def retry(fn, tries: int = 4, wait: float = 5.0):
    last = None
    for k in range(tries):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - network reads; retried, then raised
            last = exc
            time.sleep(wait * (k + 1))
    raise last  # type: ignore[misc]


def workers(default: int = 16) -> int:
    return int(os.environ.get("FARM_REPORTS_WORKERS", default))


class FarmIndex:
    """Flat pixel indices of each farm's cropland on one grid, for fast zonal sums with np.bincount."""

    def __init__(self, path: Path):
        z = np.load(path)
        self.idx = z["idx"]  # flat pixel index
        self.lab = z["lab"]  # farm number 0..n-1
        self.n = int(z["n"])
        self.shape = tuple(int(v) for v in z["shape"])

    def sums(self, values: np.ndarray) -> np.ndarray:
        v = values.ravel()[self.idx].astype("float64")
        return np.bincount(self.lab, weights=v, minlength=self.n)

    def count(self) -> np.ndarray:
        return np.bincount(self.lab, minlength=self.n).astype("float64")
