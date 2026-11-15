# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Read every scene a step needs and keep only the values of the farms' cropland pixels (resumable).

    python -I scenes.py {series,now,winter} [--ibge 4306106] [--raw DIR]

series  Landsat C2 L2 (TM, ETM+, OLI, OLI-2) and HLS L30/S30, 20 Oct - 20 Nov of 1984-2026, 60 m grid.
        Per scene, per farm: clear cropland pixels, green, straw, probable bare soil (NDTI < 0.06; also 0.04 and
        0.10), and pixels with Embrapa cover C < 30%. A scene is used when >= 50% of all farms' cropland is clear
        (the rule of analysis/residue-landsat).
now     HLS L30/S30 and Landsat 8/9, 1 Oct - 15 Nov 2026 and 1 Oct - 30 Nov 2025 (fallback), 30 m grid.
        Per scene: NDVI and NDTI of every farm cropland pixel (NaN when not clear), for per-pixel medians.
winter  HLS L30/S30, the municipality's winter tile (Cruz Alta T22JBP), 1 Apr - 30 Nov of 2020-2026, 60 m grid.
        Per granule: NDVI of every farm cropland pixel (int16 x 10,000; -32768 when not clear), for the winter
        fingerprint (winter.py).
Search filters: scene/tile cloud cover < 70% (series, now) or < 90% (winter, as analysis/rotation-fingerprint).
"""

from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
from rasterio.enums import Resampling

sys.path.insert(0, str(Path(__file__).resolve().parent))
import embrapa_ruler  # noqa: E402
from common import (  # noqa: E402
    BANDS,
    DEFAULT_IBGE,
    NDTI_BARE,
    NDVI_GREEN,
    STAC,
    FarmIndex,
    area,
    item_keep,
    nd,
    raw_dir,
    read_json,
    read_to_grid,
    reflect,
    retry,
    valid_mask,
    workers,
    write_json,
)

MODES = {
    "series": {
        "grid": 60,
        "spans": [("landsat-c2-l2", f"{y}-10-20", f"{y}-11-20") for y in range(1984, 2027)]
        + [(c, f"{y}-10-20", f"{y}-11-20") for c in ("hls2-l30", "hls2-s30") for y in range(2013, 2027)],
        "cloud": 70,
    },
    "now": {
        "grid": 30,
        "spans": [(c, "2026-10-01", "2026-11-15") for c in ("hls2-l30", "hls2-s30", "landsat-c2-l2")]
        + [(c, "2025-10-01", "2025-11-30") for c in ("hls2-l30", "hls2-s30", "landsat-c2-l2")],
        "cloud": 70,
    },
    "winter": {
        "grid": 60,
        "spans": [(c, f"{y}-04-01", f"{y}-11-30") for c in ("hls2-l30", "hls2-s30") for y in range(2020, 2027)],
        "cloud": 90,
    },
}
MIN_CLEAR_SERIES = 0.5
MIN_CLEAR_OTHER = 0.02
NODATA_I16 = -32768


def search(cat, mode: str, bbox, ibge: str = DEFAULT_IBGE) -> list:
    cfg = MODES[mode]
    items = {}
    for coll, a, b in cfg["spans"]:
        q = {"eo:cloud_cover": {"lt": cfg["cloud"]}}
        for it in cat.search(collections=[coll], bbox=bbox, datetime=f"{a}/{b}", query=q).items():
            if not item_keep(it, ibge):
                continue
            if mode == "winter" and coll.startswith("hls") and it.id.split(".")[2] != area(ibge)["winter_tile"]:
                continue
            if coll == "landsat-c2-l2" and it.properties.get("platform") == "landsat-7" and mode == "now":
                continue
            items[it.id] = it
    return sorted(items.values(), key=lambda i: (i.properties["datetime"], i.id))


def read_scene(item, mode: str, bbox, tr, shape, fi: FarmIndex):
    coll = item.collection_id
    bm = BANDS[coll]
    decim = 2 if MODES[mode]["grid"] == 60 else 1
    signed = planetary_computer.sign(item)
    qa = read_to_grid(signed.assets[bm["qa"]].href, bbox, tr, shape, decim, Resampling.nearest)
    ok = valid_mask(coll, qa).ravel()[fi.idx]
    clear_share = float(ok.mean()) if ok.size else 0.0
    need = MIN_CLEAR_SERIES if mode == "series" else MIN_CLEAR_OTHER
    meta = {"id": item.id, "collection": coll, "date": item.properties["datetime"][:10], "clear_share": clear_share}
    if clear_share < need:
        return meta, None
    names = ("red", "nir") if mode == "winter" else ("red", "nir", "sw1", "sw2")
    v = {}
    for k in names:
        a = read_to_grid(signed.assets[bm[k]].href, bbox, tr, shape, decim, Resampling.average)
        v[k] = reflect(coll, a).ravel()[fi.idx]
    ndvi = nd(v["nir"], v["red"])
    good = ok & np.isfinite(ndvi)
    if mode == "winter":
        out = np.where(good, np.round(np.clip(ndvi, -1, 1) * 10000), NODATA_I16).astype(np.int16)
        return meta, {"ndvi": out}
    ndti = nd(v["sw1"], v["sw2"])
    good &= np.isfinite(ndti)
    if mode == "now":
        return meta, {
            "ndvi": np.where(good, ndvi, np.nan).astype(np.float16),
            "ndti": np.where(good, ndti, np.nan).astype(np.float16),
        }
    nogreen = good & (ndvi < NDVI_GREEN)
    cov = np.where(nogreen, embrapa_ruler.cover(np.where(nogreen, ndti, 0)), np.nan)

    def per_farm(mask):
        return np.bincount(fi.lab, weights=mask.astype("float64"), minlength=fi.n).astype(np.int32)

    return meta, {
        "clear": per_farm(good),
        "green": per_farm(good & (ndvi >= NDVI_GREEN)),
        "straw": per_farm(nogreen & (ndti >= NDTI_BARE)),
        "bare": per_farm(nogreen & (ndti < NDTI_BARE)),
        "bare_004": per_farm(nogreen & (ndti < 0.04)),
        "bare_010": per_farm(nogreen & (ndti < 0.10)),
        "c_lt30": per_farm(nogreen & (cov < 30)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=sorted(MODES))
    ap.add_argument("--ibge", default=DEFAULT_IBGE)
    ap.add_argument("--raw", default=None)
    a = ap.parse_args()
    raw = raw_dir(a.ibge, a.raw)
    g = read_json(raw / "grid.json")
    res = MODES[a.mode]["grid"]
    import rasterio

    tr = rasterio.Affine(*g[f"tr{res}"])
    shape = tuple(g[f"shape{res}"])
    fi = FarmIndex(raw / f"farm_idx{res}.npz")
    bbox = tuple(g["bbox"])
    out_dir = raw / a.mode
    out_dir.mkdir(exist_ok=True)
    t0 = time.time()
    cat = pystac_client.Client.open(STAC)
    items = search(cat, a.mode, bbox, a.ibge)
    t_search = time.time() - t0
    print(f"{a.mode}: {len(items)} items ({t_search:.0f} s search)", flush=True)
    index_path = out_dir / "index.json"
    index = {m["id"]: m for m in read_json(index_path)} if index_path.exists() else {}
    todo = [it for it in items if it.id not in index]
    failed = []

    def job(it):
        meta, data = retry(lambda: read_scene(it, a.mode, bbox, tr, shape, fi))
        if data is not None:
            np.savez_compressed(out_dir / f"{it.id}.npz", **data)
        meta["used"] = data is not None
        return meta

    done = 0
    with ThreadPoolExecutor(workers()) as ex:
        futs = {ex.submit(job, it): it for it in todo}
        for f in as_completed(futs):
            try:
                m = f.result()
                index[m["id"]] = m
            except Exception as exc:  # noqa: BLE001 - logged; a re-run retries it
                failed.append({"id": futs[f].id, "error": repr(exc)[:300]})
            done += 1
            if done % 25 == 0:
                write_json(index_path, sorted(index.values(), key=lambda m: (m["date"], m["id"])))
                print(f"  {done}/{len(todo)} ({time.time() - t0:.0f} s)", flush=True)
    write_json(index_path, sorted(index.values(), key=lambda m: (m["date"], m["id"])))
    write_json(
        out_dir / "run.json",
        {
            "items_found": len(items),
            "items_read_this_run": len(todo),
            "failed": failed,
            "seconds": round(time.time() - t0, 1),
            "search_seconds": round(t_search, 1),
        },
    )
    used = sum(1 for m in index.values() if m.get("used"))
    print(f"{a.mode}: {used} used of {len(index)}; {len(failed)} failed; {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
