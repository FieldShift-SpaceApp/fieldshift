# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Before / after map: the same Cruz Alta cropland in early November of the oldest clear year and in the most
recent clear 2026 scene, each 30 m pixel classed green / straw / probable bare soil (NDVI + NDTI, same thresholds
as series.py). No NASA or agency logo.

    python -I map.py <results_dir>

Picks the two scenes from results/scenes.csv (accepted spring scenes): the earliest year, preferring a date from
1 to 15 November and then the clearest; and the latest 2026 scene with the clearest cropland. Re-reads only those
two scenes from the Planetary Computer (anonymous token), on one common UTM 22S 30 m grid. Writes
results/residue-before-after.png and results/residue_before_after.json.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.transform import from_origin
from rasterio.vrt import WarpedVRT
from rasterio.warp import reproject, transform_bounds, transform_geom
from rasterio.windows import from_bounds

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from scenes import BANDS, BBOX, STAC, WORLDCOVER_ITEM, load_geom, reflect, valid_mask  # noqa: E402
from series import NDTI_MAIN, NDVI_MAIN  # noqa: E402

BEFORE_YEAR = 1991  # asked for by the team (early November 1991); it is also the series maximum, said on the figure
DST_CRS = "EPSG:32722"
RES = 30.0
# class codes: 0 outside cropland/municipality, 1 green, 2 straw, 3 probable bare soil, 4 cloud/no data
GREEN, STRAW, BARE = "#3f8f3a", "#e3b23c", "#a3462b"
OUTSIDE, NODATA, INK, INK2, MUTED, SURFACE = "#ecebe7", "#ffffff", "#0b0b0b", "#52514e", "#8a8984", "#fcfcfb"


def grid() -> tuple:
    b = transform_bounds("EPSG:4326", DST_CRS, *BBOX)
    w, h = int((b[2] - b[0]) // RES), int((b[3] - b[1]) // RES)
    return from_origin(b[0], b[3], RES, RES), (h, w)


def read(href: str, tr, shape, resampling) -> np.ndarray:
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4"):
        with rasterio.open(href) as src:
            nod = src.nodata if src.nodata is not None else 0
            with WarpedVRT(
                src,
                crs=DST_CRS,
                transform=tr,
                width=shape[1],
                height=shape[0],
                resampling=resampling,
                src_nodata=nod,
                nodata=nod,
            ) as vrt:
                return vrt.read(1)


def fmt_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{int(d)} {'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()[int(m) - 1]} {y}"


def pick(rows: list[dict]) -> tuple[dict, dict]:
    spring = [r for r in rows if r["season"] == "spring" and r["accepted"] == "True"]
    # requested anchor: early November 1991 (Collection 2 Tier 1 only); fallback: the earliest such year
    early_t1 = [r for r in spring if "11-01" <= r["date"][5:] <= "11-15" and "_T1" in r["scene"]]
    old = [r for r in early_t1 if r["year"] == str(BEFORE_YEAR)] or [
        r for r in early_t1 if int(r["year"]) == min(int(x["year"]) for x in early_t1)
    ]
    before = max(old, key=lambda r: float(r["cropland_clear_fraction"]))
    new = [r for r in spring if r["year"] == "2026"]
    after = max(new, key=lambda r: (float(r["cropland_clear_fraction"]), r["date"]))
    return before, after


def classify(row: dict, cat, geom, crop_frac, tr, shape) -> tuple[np.ndarray, dict]:
    first_id = row["scene"].split("+")[0]
    coll = row["collection"]
    bmap = BANDS[coll]
    ids = row["scene"].split("+")
    cls = np.full(shape, 4, dtype=np.uint8)
    inside = ~geometry_mask([transform_geom("EPSG:4326", DST_CRS, geom)], out_shape=shape, transform=tr)
    cropland = inside & (crop_frac >= 0.5)
    for iid in ids:  # HLS: up to two MGRS tiles of the same day
        item = planetary_computer.sign(cat.get_collection(coll).get_item(iid))
        qa = read(item.assets[bmap["qa"]].href, tr, shape, Resampling.nearest)
        b = {
            k: reflect(coll, read(item.assets[bmap[k]].href, tr, shape, Resampling.bilinear))
            for k in BANDS[coll]
            if k != "qa"
        }
        with np.errstate(invalid="ignore", divide="ignore"):
            ndvi = (b["nir"] - b["red"]) / (b["nir"] + b["red"])
            ndti = (b["sw1"] - b["sw2"]) / (b["sw1"] + b["sw2"])
        ok = valid_mask(coll, qa) & np.isfinite(ndvi) & np.isfinite(ndti) & (cls == 4)
        c = np.where(ndvi >= NDVI_MAIN, 1, np.where(ndti >= NDTI_MAIN, 2, 3)).astype(np.uint8)
        cls[ok] = c[ok]
    cls[~cropland] = 0
    n = int(cropland.sum())
    valid = int(((cls >= 1) & (cls <= 3)).sum())
    pct = {
        name: round(100 * float((cls == k).sum()) / valid, 1) for k, name in ((1, "green"), (2, "straw"), (3, "bare"))
    }
    info = {
        "scene": row["scene"],
        "first_item": first_id,
        "date": row["date"],
        "sensor": row["sensor"],
        "cropland_pixels_30m": n,
        "clear_cropland_pixels_30m": valid,
        "clear_fraction": round(valid / n, 3) if n else None,
        "pct_of_clear_cropland": pct,
    }
    return cls, info


def main() -> None:
    results = Path(sys.argv[1])
    rows = list(csv.DictReader((results / "scenes.csv").open(encoding="utf-8")))
    before, after = pick(rows)
    geom = load_geom()
    tr, shape = grid()
    cat = pystac_client.Client.open(STAC)
    wc_item = planetary_computer.sign(cat.get_collection("esa-worldcover").get_item(WORLDCOVER_ITEM))
    with rasterio.open(wc_item.assets["map"].href) as src:
        win = from_bounds(*BBOX, src.transform).round_offsets().round_lengths()
        wc, wc_tr = src.read(1, window=win), src.window_transform(win)
        crop_frac = np.zeros(shape, dtype="float32")
        reproject(
            (wc == 40).astype("float32"),
            crop_frac,
            src_transform=wc_tr,
            src_crs=src.crs,
            dst_transform=tr,
            dst_crs=DST_CRS,
            resampling=Resampling.average,
        )
    panels = [classify(r, cat, geom, crop_frac, tr, shape) for r in (before, after)]

    cmap = ListedColormap([OUTSIDE, GREEN, STRAW, BARE, NODATA])
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    fig = plt.figure(figsize=(9, 5.6), dpi=130, facecolor=SURFACE)
    gproj = transform_geom("EPSG:4326", DST_CRS, geom)
    ring = np.array(gproj["coordinates"][0])
    col = (ring[:, 0] - tr.c) / RES
    rowp = (tr.f - ring[:, 1]) / RES
    for k, (cls, info) in enumerate(panels):
        ax = fig.add_axes((0.02 + k * 0.49, 0.15, 0.47, 0.62))
        ax.imshow(cls, cmap=cmap, vmin=0, vmax=4, interpolation="nearest")
        ax.plot(col, rowp, color=INK2, lw=0.7)
        ax.set_axis_off()
        p = info["pct_of_clear_cropland"]
        ax.set_title(
            f"{info['date']} · {info['sensor']}\n"
            f"green {p['green']:.1f}% · straw {p['straw']:.1f}% · probable bare soil {p['bare']:.1f}%",
            fontsize=8.5,
            color=INK,
            loc="left",
        )
        if k == 0:  # 10 km scale bar
            x0, y0 = shape[1] * 0.06, shape[0] * 0.95
            ax.plot([x0, x0 + 10000 / RES], [y0, y0], color=INK, lw=2.5, solid_capstyle="butt")
            ax.text(x0 + 5000 / RES, y0 - shape[0] * 0.02, "10 km", ha="center", va="bottom", fontsize=8, color=INK)
    ep = json.loads((results / "residue_landsat.json").read_text(encoding="utf-8"))["epochs_landsat"]
    d0, d1 = (fmt_date(p[1]["date"]) for p in panels)
    fig.text(0.02, 0.945, f"Same Cruz Alta cropland: {d0} vs {d1}", fontsize=12.5, weight="bold", color=INK)
    fig.text(
        0.02,
        0.875,
        "Fair comparison, median year (20 Oct – 20 Nov, Landsat): probable bare soil "
        f"{ep['spring 1984-1994']['pct_bare_median']}% in 1984–1994 vs "
        f"{ep['spring 2015-2026']['pct_bare_median']}% in 2015–2026. "
        f"{d0[-4:]} is the highest year of the series, not a typical one.\n"
        f"Each 30 m cropland pixel: green NDVI ≥ {NDVI_MAIN:.2f}; otherwise straw if NDTI ≥ {NDTI_MAIN:.2f}, "
        "probable bare soil if lower. Shares are of the clear cropland.",
        fontsize=8,
        color=INK2,
        linespacing=1.4,
    )
    handles = [
        Patch(color=GREEN, label="green"),
        Patch(color=STRAW, label="straw (residue)"),
        Patch(color=BARE, label="probable bare soil"),
        Patch(facecolor=NODATA, edgecolor=MUTED, label="cloud / no data"),
        Patch(color=OUTSIDE, label="not cropland (ESA WorldCover 2021)"),
    ]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.02, 0.065), ncol=5, frameon=False, fontsize=7.8)
    fig.text(
        0.02,
        0.045,
        "1991 is the highest year of the 1984–2026 series (median of 1984–1994: about 6%). Spectral inference without "
        "field calibration; municipality outline: IBGE 2022.",
        fontsize=7,
        color=MUTED,
    )
    fig.text(0.02, 0.015, "NASA/USGS Landsat; NASA HLS", fontsize=7.5, color=INK2)
    fig.savefig(results / "residue-before-after.png", facecolor=SURFACE)
    out = {
        "grid": {"crs": DST_CRS, "pixel_m": RES, "bbox_wgs84": BBOX},
        "thresholds": {"ndvi_green_min": NDVI_MAIN, "ndti_bare_below": NDTI_MAIN},
        "selection_rule": "before: the clearest accepted Tier 1 scene of 1-15 November 1991 (asked for by the team; "
        "1991 "
        "is also the highest year of the series, see series.csv); after: the accepted 2026 spring scene with the "
        "clearest cropland",
        "before": panels[0][1],
        "after": panels[1][1],
        "attribution": "NASA/USGS Landsat; NASA HLS; ESA WorldCover 2021 (contains modified Copernicus Sentinel data "
        "2021); IBGE municipal mesh 2022",
    }
    (results / "residue_before_after.json").write_text(json.dumps(out, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
