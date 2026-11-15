# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Inputs for the Prithvi experiment: a 448 x 448 px (4 chips of 224 x 224, 13.4 km x 13.4 km) window of Cruz Alta
cropland in NASA HLS v2.0, winter YEAR.

    python -I fetch_chips.py <raw_dir> [--year 2024]

1. Window: the 448 x 448 block of the rotation-fingerprint grid (tile T22JBP, 30 m, EPSG:32622) with the largest
   share of ESA WorldCover 2021 cropland inside the IBGE polygon (same mask as analysis/rotation-fingerprint).
2. Rule-based winter class of every window pixel for YEAR: red, NIR and Fmask of every HLS granule (L30 + S30,
   1 April - 30 November, tile cloud < 90%), then the half-month median composite, gap filling and the MAIN rules
   of analysis/rotation-fingerprint/classify.py (imported, not copied), so the classes are those of that analysis.
3. Prithvi input: the six HLS bands the model was fine-tuned on (Blue, Green, Red, Narrow NIR, SWIR 1, SWIR 2) for
   the clearest granule (Fmask, cropland pixels) in each of three winter periods: Jul, Sep, 15 Oct - 30 Nov.

Writes to <raw_dir> (never committed): window.npz (classes, cropland mask, transform), hls6.npz (3 x 6 x 448 x 448
int16 reflectance x 10000, clear masks, dates), granules.json (search log with the clear share of each granule).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
from rasterio.transform import Affine

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rotation-fingerprint"))
import classify as fp  # noqa: E402  (analysis/rotation-fingerprint/classify.py)
import scenes as sc  # noqa: E402  (analysis/rotation-fingerprint/scenes.py)

N = 448  # 2 x 2 chips of 224 px
SIX = {  # HLS v2.0 band names: Blue, Green, Red, Narrow NIR, SWIR 1, SWIR 2 (order of the Prithvi crop model)
    "hls2-s30": ["B02", "B03", "B04", "B8A", "B11", "B12"],
    "hls2-l30": ["B02", "B03", "B04", "B05", "B06", "B07"],
}
PERIODS = {"Jul": ("07-01", "07-31"), "Sep": ("09-01", "09-30"), "Oct-Nov": ("10-15", "11-30")}


def pick_window(idx: np.ndarray, shape) -> tuple[int, int]:
    crop = np.zeros(shape[0] * shape[1], dtype=np.float32)
    crop[idx] = 1
    crop = crop.reshape(shape)
    ii = np.pad(crop.cumsum(0).cumsum(1), ((1, 0), (1, 0)))
    s = ii[N:, N:] - ii[:-N, N:] - ii[N:, :-N] + ii[:-N, :-N]
    s = s[::8, ::8]  # coarse step is enough
    r, c = np.unravel_index(int(s.argmax()), s.shape)
    return int(r) * 8, int(c) * 8


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw")
    ap.add_argument("--year", type=int, default=2024)
    a = ap.parse_args()
    raw = Path(a.raw)
    raw.mkdir(parents=True, exist_ok=True)
    cat = pystac_client.Client.open(sc.STAC)
    tr, shape = sc.grid()
    idx, _ = sc.cropland_index(cat, tr, shape)
    r0, c0 = pick_window(idx, shape)
    wtr = tr * Affine.translation(c0, r0)
    crop = np.zeros(shape[0] * shape[1], dtype=bool)
    crop[idx] = True
    crop = crop.reshape(shape)[r0 : r0 + N, c0 : c0 + N]
    print(f"window row {r0} col {c0}, cropland {crop.mean():.1%}", flush=True)

    searched_at = datetime.now(UTC).isoformat(timespec="seconds")
    items = []
    for coll in sc.BANDS:
        dt = f"{a.year}-{sc.SEASON[0]}/{a.year}-{sc.SEASON[1]}"
        for it in cat.search(
            collections=[coll], bbox=sc.BBOX, datetime=dt, query={"eo:cloud_cover": {"lt": 90}}
        ).items():
            if it.id.split(".")[2] == sc.TILE:
                items.append(it)
    items.sort(key=lambda i: i.properties["datetime"])
    print(f"{len(items)} granules", flush=True)

    def red_nir(item):
        s = planetary_computer.sign(item)
        b = sc.BANDS[item.collection_id]
        for attempt in range(3):
            try:
                ok = sc.clear(sc.read(s.assets[b["qa"]].href, wtr, (N, N)))
                row = {"id": item.id, "date": item.properties["datetime"][:10], "clear_share": float(ok[crop].mean())}
                if row["clear_share"] < sc.MIN_CLEAR:
                    return row, None
                red = sc.read(s.assets[b["red"]].href, wtr, (N, N)).astype("float32")
                nir = sc.read(s.assets[b["nir"]].href, wtr, (N, N)).astype("float32")
                good = ok & (red > 0) & (nir > 0)
                with np.errstate(invalid="ignore", divide="ignore"):
                    ndvi = (nir - red) / (nir + red)
                good &= np.isfinite(ndvi)
                v = np.full((N, N), fp.NODATA, dtype=np.int16)
                v[good] = np.round(np.clip(ndvi[good], -1, 1) * 10000).astype(np.int16)
                return row, v
            except Exception as e:  # network: retry, then log
                if attempt == 2:
                    return {"id": item.id, "date": item.properties["datetime"][:10], "error": str(e)[:200]}, None
                time.sleep(5 * (attempt + 1))

    t0 = time.time()
    with ThreadPoolExecutor(16) as ex:
        res = list(ex.map(red_nir, items))
    print(f"read in {time.time() - t0:.0f} s", flush=True)
    rows = [r for r, _ in res]

    # half-month median composite, fill and rules (same functions as analysis/rotation-fingerprint)
    n = N * N
    comp = np.full((fp.NB, n), fp.NODATA, dtype=np.int16)
    for b in range(fp.NB):
        st = [v.ravel() for r, v in res if v is not None and fp.bin_of(r["date"]) == b]
        if st:
            f = np.where(np.stack(st) == fp.NODATA, np.nan, np.stack(st).astype("float32"))
            with np.errstate(all="ignore"), __import__("warnings").catch_warnings():
                __import__("warnings").simplefilter("ignore", RuntimeWarning)
                m = np.nanmedian(f, axis=0)
            comp[b] = np.where(np.isfinite(m), np.round(m), fp.NODATA).astype(np.int16)
    v, eligible = fp.fill(comp)
    out = fp.classify(v, eligible, dict(fp.MAIN))
    cls = out["cls"].reshape(N, N)
    cls[~crop] = fp.NONE
    np.savez_compressed(
        raw / "window.npz",
        cls=cls,
        crop=crop,
        ndvi_filled=v.reshape(fp.NB, N, N).astype("float16"),
        transform=np.array(wtr)[:6],
        r0=r0,
        c0=c0,
        year=a.year,
    )
    u, k = np.unique(cls[crop], return_counts=True)
    print("rule classes in window:", {fp.CODE[int(x)]: int(y) for x, y in zip(u, k, strict=True)}, flush=True)

    # three clearest granules, one per winter period
    chosen = []
    for name, (d0, d1) in PERIODS.items():
        cand = [
            (r["clear_share"], it)
            for (r, vv), it in zip(res, items, strict=True)
            if vv is not None and f"{a.year}-{d0}" <= r["date"] <= f"{a.year}-{d1}"
        ]
        cand.sort(key=lambda t: -t[0])
        chosen.append((name, cand[0][1], cand[0][0]))
        print(name, cand[0][1].id, f"clear {cand[0][0]:.1%}", flush=True)
    stack = np.zeros((3, 6, N, N), dtype=np.int16)
    clear = np.zeros((3, N, N), dtype=bool)
    for t, (_, it, _) in enumerate(chosen):
        s = planetary_computer.sign(it)
        for k, band in enumerate(SIX[it.collection_id]):
            stack[t, k] = sc.read(s.assets[band].href, wtr, (N, N))
        clear[t] = sc.clear(sc.read(s.assets["Fmask"].href, wtr, (N, N)))
    np.savez_compressed(
        raw / "hls6.npz",
        x=stack,
        clear=clear,
        ids=np.array([it.id for _, it, _ in chosen]),
        periods=np.array([p for p, _, _ in chosen]),
    )
    (raw / "granules.json").write_text(
        json.dumps(
            {
                "searched_at_utc": searched_at,
                "stac": sc.STAC,
                "tile": sc.TILE,
                "year": a.year,
                "window": {"row0": r0, "col0": c0, "size_px": N, "transform": list(np.array(wtr)[:6]), "crs": sc.CRS},
                "cropland_share": float(crop.mean()),
                "prithvi_input": [
                    {
                        "period": p,
                        "id": it.id,
                        "date": it.properties["datetime"][:10],
                        "clear_share_cropland": round(cs, 4),
                        "stac_item": f"{sc.STAC}/collections/{it.collection_id}/items/{it.id}",
                    }
                    for p, it, cs in chosen
                ],
                "granules": rows,
            },
            indent=1,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
