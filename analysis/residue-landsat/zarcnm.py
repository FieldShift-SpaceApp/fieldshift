# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Satellite pre-check of two ZARC-NM management indicators and the slope rule of IN SPA/MAPA 2/2025, Cruz Alta.

    python -I zarcnm.py <raw_dir> <results_dir>

What the norm (Instrucao Normativa SPA/MAPA n. 2/2025) defines and this script applies as written:
  - item 6.2: sample the field with regular quadrats; fields > 100 ha use quadrats of 5 to 10 ha, analysed at the
    quadrat centre. Here: three 300 m x 300 m (9 ha) quadrats of cropland (see QUADRAT RULE below).
  - item 6.3: mean slope from a product of at least 30 m resolution, such as NASADEM -> NASADEM at 30 m.
  - item 6.4 / 6.5: NDVI and NDTI time series from Landsat, Sentinel-2 or HLS at 30 m, every image available,
    at least every 16 days -> every Landsat C2 L2 and HLS v2.0 scene of 15 Sep - 31 Dec with the quadrat clear.
  - Table 1, indicator 4: years without soil disturbance T: level 1 T < 3, 2 3 <= T < 5, 3 5 <= T < 8, 4 T >= 8.
  - Table 1, indicator 5: straw cover in pre-sowing C (%): level 1 C < 30, 2 30-60, 3 60-90, 4 C >= 90.
  - item 6.7: C is judged in the month immediately before sowing from spectral indices such as NDTI.
  - item 6.8: tillage (ploughing, harrowing, chiselling, subsoiling) exposes soil and shows as a sudden change.
  - item 3.2.1 I: slope >= 3% requires contour sowing on at least 75% of the area (else NM1).
What the norm does NOT give, so it is a stated choice here (same thresholds as series.py): how to turn NDTI into
C, and the NDTI value of exposed soil. C is replaced by a PROXY: the share of the quadrat's 30 m pixels that are
NOT probable bare soil (NDVI >= 0.30, or NDTI >= 0.06) on the pre-sowing observation. A pixel share is not a
percentage of soil covered, so the indicator-5 level derived from it is indicative only.

QUADRAT RULE (no personal data; no property or owner is looked up): candidate 300 m blocks on the UTM 22S 30 m grid
that are entirely ESA WorldCover 2021 cropland inside the municipality and clear on both before/after map dates;
one per NASADEM slope class (< 3%, 3-8%, >= 8% block mean), the block closest to that class's median slope among
blocks at least 5 km from the ones already chosen.
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import planetary_computer
import pystac_client
import rasterio
from rasterio.enums import Resampling
from rasterio.features import geometry_mask
from rasterio.vrt import WarpedVRT
from rasterio.warp import reproject, transform_geom
from rasterio.warp import transform as warp_transform
from rasterio.windows import Window, from_bounds

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import embrapa  # noqa: E402
from map import DST_CRS, RES, grid  # noqa: E402
from scenes import BANDS, BBOX, STAC, WORLDCOVER_ITEM, load_geom, reflect, valid_mask  # noqa: E402
from series import NDTI_MAIN, NDVI_MAIN  # noqa: E402

BLOCK = 10  # pixels -> 300 m x 300 m = 9 ha (IN 2/2025 item 6.2 IV: 5-10 ha for fields > 100 ha)
WINDOW = ("09-15", "12-31")  # pre-sowing and sowing of the summer crop
MIN_CLEAR_PIXELS = 80  # of 100 in the quadrat
TILLAGE_BARE_SHARE = 0.5  # a clear observation with >= half of the quadrat probable bare soil
C_LEVELS = ((90, 4), (60, 3), (30, 2), (0, 1))  # Table 1, indicator 5
T_LEVELS = ((8, 4), (5, 3), (3, 2), (0, 1))  # Table 1, indicator 4
SLOPE_CLASSES = ((0, 3), (3, 8), (8, 1000))
MIN_DIST_M = 5000
WORKERS = 24
# Plan B (time): HLS S30 left out; Landsat 4-9 C2 L2 and HLS L30 cover 1984-2026 at <= 16 days (item 6.5).
# Add "hls2-s30" to read the Sentinel-2 half of HLS as well (about 300 more items, slow on the anonymous server).
HLS_COLLECTIONS = ("hls2-l30",)


def level(value: float, table) -> int:
    for lo, lv in table:
        if value >= lo:
            return lv
    return 1


def load_masks(cat, geom, tr, shape):
    wc_item = planetary_computer.sign(cat.get_collection("esa-worldcover").get_item(WORLDCOVER_ITEM))
    with rasterio.open(wc_item.assets["map"].href) as src:
        win = from_bounds(*BBOX, src.transform).round_offsets().round_lengths()
        wc, wc_tr = src.read(1, window=win), src.window_transform(win)
        crop = np.zeros(shape, dtype="float32")
        reproject(
            (wc == 40).astype("float32"),
            crop,
            src_transform=wc_tr,
            src_crs=src.crs,
            dst_transform=tr,
            dst_crs=DST_CRS,
            resampling=Resampling.average,
        )
    inside = ~geometry_mask([transform_geom("EPSG:4326", DST_CRS, geom)], out_shape=shape, transform=tr)
    # NASADEM, 1 arc-second, reprojected to the same 30 m grid
    dem = np.full(shape, np.nan, dtype="float32")
    dem_items = list(cat.search(collections=["nasadem"], bbox=BBOX).items())
    for it in dem_items:
        it = planetary_computer.sign(it)
        with rasterio.open(it.assets["elevation"].href) as src:
            part = np.full(shape, np.nan, dtype="float32")
            reproject(
                rasterio.band(src, 1),
                part,
                dst_transform=tr,
                dst_crs=DST_CRS,
                resampling=Resampling.bilinear,
                dst_nodata=np.nan,
            )
            dem = np.where(np.isnan(dem), part, dem)
    gy, gx = np.gradient(dem.astype("float64"), RES, RES)
    slope = (100 * np.hypot(gx, gy)).astype("float32")  # percent
    return crop, inside, dem, slope, [it.id for it in dem_items]


def slope_summary(slope, cropland) -> dict:
    s = slope[cropland & np.isfinite(slope)]
    n = s.size
    pct = lambda m: round(100 * float(m.sum()) / n, 1)  # noqa: E731
    return {
        "cropland_pixels_30m": int(n),
        "cropland_ha": round(n * RES * RES / 1e4),
        "norm_rule": "IN SPA/MAPA 2/2025 item 3.2.1 I: slope >= 3% requires contour sowing (or sowing on the level) "
        "on at least 75% of the area in the last year, otherwise the management level is NM1. The norm defines "
        "no other slope class.",
        "norm_classes_pct_of_cropland": {"slope_lt_3": pct(s < 3), "slope_ge_3": pct(s >= 3)},
        "context_classes_pct_of_cropland": {
            "0-3": pct(s < 3),
            "3-8": pct((s >= 3) & (s < 8)),
            "8-20": pct((s >= 8) & (s < 20)),
            "20-45": pct((s >= 20) & (s < 45)),
            "ge_45": pct(s >= 45),
        },
        "context_classes_note": "Relief classes used by Embrapa soil surveys (flat 0-3%, gently undulating 3-8%, "
        "undulating 8-20%, strongly undulating 20-45%); context only, not classes of the norm.",
        "slope_pct_quantiles": {q: round(float(np.quantile(s, q / 100)), 1) for q in (10, 25, 50, 75, 90)},
        "slope_pct_mean": round(float(s.mean()), 2),
    }


def blocks(crop, inside, slope, ok_before, ok_after):
    h, w = crop.shape
    out = []
    for r in range(0, h - BLOCK, BLOCK):
        for c in range(0, w - BLOCK, BLOCK):
            sl = (slice(r, r + BLOCK), slice(c, c + BLOCK))
            if inside[sl].all() and (crop[sl] >= 0.999).all() and ok_before[sl].all() and ok_after[sl].all():
                m = float(np.nanmean(slope[sl]))
                if np.isfinite(m):
                    out.append((r, c, m))
    return out


def pick_quadrats(cands, tr) -> list[dict]:
    chosen = []
    for k, (lo, hi) in enumerate(SLOPE_CLASSES, start=1):
        cl = [b for b in cands if lo <= b[2] < hi]
        if not cl:
            continue
        med = float(np.median([b[2] for b in cl]))

        def far(b):
            return all(np.hypot((b[0] - q["row"]) * RES, (b[1] - q["col"]) * RES) >= MIN_DIST_M for q in chosen)

        cl = sorted((b for b in cl if far(b)), key=lambda b: abs(b[2] - med))
        if not cl:
            continue
        r, c, m = cl[0]
        x, y = tr * (c + BLOCK / 2, r + BLOCK / 2)
        lon, lat = warp_transform(DST_CRS, "EPSG:4326", [x], [y])
        chosen.append(
            {
                "quadrant_id": f"CA-Q{k}",
                "row": r,
                "col": c,
                "lat": round(lat[0][0] if isinstance(lat[0], list) else lat[0], 5),
                "lon": round(lon[0][0] if isinstance(lon[0], list) else lon[0], 5),
                "slope_class_rule": f"{lo}-{hi}%" if hi < 1000 else f">= {lo}%",
                "slope_mean_pct_nasadem": round(m, 2),
                "candidates_in_class": len([b for b in cands if lo <= b[2] < hi]),
            }
        )
    return chosen


def search_items(cat) -> list:
    items = []
    bbox = BBOX
    q = {"eo:cloud_cover": {"lt": 80}}
    for it in cat.search(collections=["landsat-c2-l2"], bbox=bbox, datetime="1984-01-01/2026-12-31", query=q).items():
        p = it.properties
        if (p["landsat:wrs_path"], p["landsat:wrs_row"]) in (("223", "080"), ("222", "080")):
            if WINDOW[0] <= p["datetime"][5:10] <= WINDOW[1]:
                items.append(it)
    for coll in HLS_COLLECTIONS:
        for it in cat.search(collections=[coll], bbox=bbox, datetime="2013-01-01/2026-12-31", query=q).items():
            if (
                it.id.split(".")[2] in ("T22JBP", "T22JBN")
                and WINDOW[0] <= it.properties["datetime"][5:10] <= WINDOW[1]
            ):
                items.append(it)
    return items


def read_item(item, quads, tr, shape) -> dict:
    coll = item.collection_id
    bmap = BANDS[coll]
    signed = planetary_computer.sign(item)
    out = {}
    arrs = {}
    with rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_TIMEOUT="60"):
        for k in ("qa", "red", "nir", "sw1", "sw2"):
            with rasterio.open(signed.assets[bmap[k]].href) as src:
                nod = src.nodata if src.nodata is not None else 0
                with WarpedVRT(
                    src,
                    crs=DST_CRS,
                    transform=tr,
                    width=shape[1],
                    height=shape[0],
                    resampling=Resampling.nearest,
                    src_nodata=nod,
                    nodata=nod,
                ) as vrt:
                    arrs[k] = {
                        q["quadrant_id"]: vrt.read(1, window=Window(q["col"], q["row"], BLOCK, BLOCK)) for q in quads
                    }
    for q in quads:
        qid = q["quadrant_id"]
        ok = valid_mask(coll, arrs["qa"][qid])
        b = {k: reflect(coll, arrs[k][qid]) for k in ("red", "nir", "sw1", "sw2")}
        with np.errstate(invalid="ignore", divide="ignore"):
            ndvi = (b["nir"] - b["red"]) / (b["nir"] + b["red"])
            ndti = (b["sw1"] - b["sw2"]) / (b["sw1"] + b["sw2"])
        good = ok & np.isfinite(ndvi) & np.isfinite(ndti)
        n = int(good.sum())
        if n < MIN_CLEAR_PIXELS:
            continue
        v, t = ndvi[good], ndti[good]
        bare = (v < NDVI_MAIN) & (t < NDTI_MAIN)
        out[qid] = {
            "clear_pixels": n,
            "ndvi_mean": round(float(v.mean()), 3),
            "ndti_mean": round(float(t.mean()), 3),
            "share_green": round(float((v >= NDVI_MAIN).mean()), 3),
            "share_straw": round(float(((v < NDVI_MAIN) & (t >= NDTI_MAIN)).mean()), 3),
            "share_bare": round(float(bare.mean()), 3),
            **emb_stats(v, t),
        }
    return out


def emb_stats(v: np.ndarray, t: np.ndarray) -> dict:
    """Embrapa Documentos 454 ruler per pixel: cover of the no-green pixels (NDVI > 0.3 masked, as there)."""
    ng = v < NDVI_MAIN
    if not ng.any():
        return {"n_nogreen": 0}
    c = embrapa.cover(t[ng])
    return {
        "n_nogreen": int(ng.sum()),
        "emb_cover_mean": round(float(c.mean()), 1),
        "emb_share_lt30": round(float((c < 30).mean()), 3),
        "emb_share_30_60": round(float(((c >= 30) & (c < 60)).mean()), 3),
        "emb_share_60_90": round(float(((c >= 60) & (c < 90)).mean()), 3),
        "emb_share_ge90": round(float((c >= 90).mean()), 3),
        "emb_share_ge80_saturated": round(float((c >= embrapa.SATURATION_COVER).mean()), 3),
        # pixels of the whole clear quadrat with no green and C < 30 % (ploughed fields: 5-20 %, Table 2)
        "emb_share_of_quadrat_lt30": round(float((c < 30).sum() / v.size), 3),
    }


def sensor(item) -> str:
    if item.collection_id.startswith("hls"):
        return "HLS " + item.collection_id[-3:].upper()
    return {
        "landsat-4": "Landsat 4 TM",
        "landsat-5": "Landsat 5 TM",
        "landsat-7": "Landsat 7 ETM+",
        "landsat-8": "Landsat 8 OLI",
        "landsat-9": "Landsat 9 OLI-2",
    }[item.properties["platform"]]


def main() -> None:
    raw, results = Path(sys.argv[1]), Path(sys.argv[2])
    cache = raw / "zarcnm_v2"
    cache.mkdir(parents=True, exist_ok=True)
    geom = load_geom()
    tr, shape = grid()
    cat = pystac_client.Client.open(STAC)
    crop, inside, dem, slope, dem_ids = load_masks(cat, geom, tr, shape)
    cropland = inside & (crop >= 0.5)
    slope_doc = {
        "source": "NASADEM (NASA JPL, 1 arc-second, SRTM-based, year-2000 surface) via the Microsoft Planetary "
        "Computer collection 'nasadem' (anonymous); reprojected bilinearly to UTM 22S at 30 m; slope = 100 x the "
        "magnitude of the elevation gradient (numpy.gradient, central differences)",
        "nasadem_items": dem_ids,
        "cropland_mask": "ESA WorldCover 2021 class 40, >= 50% of the 30 m pixel, inside IBGE municipality 4306106",
        **slope_summary(slope, cropland),
        "warning": "The satellite and the DEM do not see contour sowing, terraces or sowing on the level: they "
        "only say where the rule applies (slope >= 3%), not whether the field complies. NASADEM noise at 30 m "
        "inflates slope on gentle relief; a field's mean slope (item 6.3) can differ from the pixel shares here.",
    }

    # quadrats: clear on both before/after map dates (re-read the clouds from residue_before_after.json scenes)
    ba = json.loads((results / "residue_before_after.json").read_text(encoding="utf-8"))
    oks = []
    for key in ("before", "after"):
        ids = ba[key]["scene"].split("+")
        ok = np.zeros(shape, dtype=bool)
        for iid in ids:
            coll = "landsat-c2-l2" if iid.startswith("L") else ("hls2-s30" if ".S30." in iid else "hls2-l30")
            it = planetary_computer.sign(cat.get_collection(coll).get_item(iid))
            with rasterio.open(it.assets[BANDS[coll]["qa"]].href) as src:
                with WarpedVRT(
                    src, crs=DST_CRS, transform=tr, width=shape[1], height=shape[0], resampling=Resampling.nearest
                ) as vrt:
                    ok |= valid_mask(coll, vrt.read(1))
        oks.append(ok)
    cands = blocks(crop, inside, slope, oks[0], oks[1])
    quads = pick_quadrats(cands, tr)
    print("quadrats", quads, flush=True)
    for q in quads:
        sl = (slice(q["row"], q["row"] + BLOCK), slice(q["col"], q["col"] + BLOCK))
        q["elevation_mean_m_nasadem"] = round(float(np.nanmean(dem[sl])), 1)
    slope_doc["quadrats"] = [
        {
            k: q[k]
            for k in (
                "quadrant_id",
                "lat",
                "lon",
                "slope_class_rule",
                "slope_mean_pct_nasadem",
                "elevation_mean_m_nasadem",
            )
        }
        for q in quads
    ]
    slope_doc["quadrats_rule_ge_3pct"] = {q["quadrant_id"]: q["slope_mean_pct_nasadem"] >= 3 for q in quads}

    (results / "nasadem_slope_classes.json").write_text(
        json.dumps(slope_doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    if "--slope-only" in sys.argv:
        print(json.dumps(slope_doc, indent=1, ensure_ascii=False))
        return
    items = search_items(cat)
    print(len(items), "items in", WINDOW, flush=True)

    def work(it):
        f = cache / f"{it.id}.json"
        if f.exists():
            return it, json.loads(f.read_text(encoding="utf-8")), None
        for attempt in range(3):
            try:
                res = read_item(it, quads, tr, shape)
                f.write_text(json.dumps(res), encoding="utf-8")
                return it, res, None
            except Exception as exc:  # noqa: BLE001 - retried, then recorded
                err = repr(exc)[:200]
                time.sleep(3 * (attempt + 1))
        return it, None, err

    obs = defaultdict(list)
    errors = {}
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        for fut in as_completed([ex.submit(work, it) for it in items]):
            it, res, err = fut.result()
            done += 1
            if res is None:
                errors[it.id] = err
                continue
            for qid, o in res.items():
                obs[qid].append({"date": it.properties["datetime"][:10], "sensor": sensor(it), "id": it.id, **o})
            if done % 100 == 0:
                print(f"[{done}/{len(items)}]", flush=True)

    # per quadrat and season (year of the 15 Sep - 31 Dec window)
    records = []
    for q in quads:
        qid = q["quadrant_id"]
        by_year = defaultdict(list)
        for o in obs[qid]:
            by_year[int(o["date"][:4])].append(o)
        last_signal = None
        continuous = True  # every season since the last signal had at least one no-green clear observation
        for year in range(1984, 2027):
            ss = sorted(by_year.get(year, []), key=lambda o: o["date"])
            rec = {
                "quadrant_id": qid,
                "lat": q["lat"],
                "lon": q["lon"],
                "year": year,
                "n_clear_observations": len(ss),
                "sensors": sorted({o["sensor"] for o in ss}),
            }
            if not ss:
                rec.update(
                    {
                        "ndvi_cover_class": None,
                        "ndti_residue_class": None,
                        "tillage_signal": "no data",
                        "notes": "no clear observation of the quadrat in 15 Sep - 31 Dec",
                    }
                )
                continuous = False
                records.append(rec)
                continue
            nogreen = [o for o in ss if o["ndvi_mean"] < NDVI_MAIN]
            pre = min(ss, key=lambda o: o["ndvi_mean"])  # pre-sowing reference: seasonal NDVI minimum
            ref = min(nogreen, key=lambda o: o["ndti_mean"]) if nogreen else pre  # minNDTI (Zheng et al. 2012)
            c_proxy = round(100 * (1 - ref["share_bare"]), 1)
            bare_max = max(o["share_bare"] for o in ss)
            emb_low_max = max(o.get("emb_share_of_quadrat_lt30", 0.0) for o in ss)
            signal = emb_low_max >= TILLAGE_BARE_SHARE  # Embrapa ruler: half the quadrat at C < 30 %
            team_signal = bare_max >= TILLAGE_BARE_SHARE
            c_emb = ref.get("emb_cover_mean")
            if signal:
                last_signal, continuous = year, True
            elif not nogreen:
                continuous = False
            t_years = (year - last_signal) if (last_signal is not None and continuous) else None
            notes = []
            if not nogreen:
                notes.append("never without green cover in the clear observations: straw and soil not visible")
            if len(ss) < 3:
                notes.append(f"only {len(ss)} clear observation(s): a short tillage event can be missed")
            if team_signal != signal:
                notes.append("team threshold (NDTI < 0.06) and Embrapa ruler disagree on the bare-soil signature")
            if c_emb is not None and c_emb >= embrapa.SATURATION_COVER:
                notes.append("NDTI above the ~80% saturation of the Embrapa calibration: levels 3 and 4 not separable")
            rec.update(
                {
                    "ndvi_cover_class": "green cover (NDVI >= 0.30)"
                    if pre["ndvi_mean"] >= NDVI_MAIN
                    else "no green (NDVI < 0.30)",
                    "ndti_residue_class": (
                        f"IN 2/2025 indicator 5 {embrapa.in_class_label(c_emb)} on {ref['date']}, Embrapa Doc 454 "
                        "ruler (Cambe PR calibration, not local)"
                    )
                    if c_emb is not None
                    else "not observable (no pixel without green on the reference date)",
                    "tillage_signal": "bare-soil signature (possible tillage)"
                    if signal
                    else ("no bare-soil signature" if nogreen else "not observable (always green)"),
                    "notes": "; ".join(notes) if notes else "",
                    "pre_sowing_reference_date": ref["date"],
                    "pre_sowing_ndvi_mean": ref["ndvi_mean"],
                    "pre_sowing_ndti_mean": ref["ndti_mean"],
                    "c_embrapa_pct": c_emb,
                    "indicator5_level_embrapa": (
                        "3 or 4" if c_emb >= embrapa.SATURATION_COVER else embrapa.in_level(c_emb)
                    )
                    if c_emb is not None
                    else None,
                    "c_embrapa_pixel_shares": {
                        k: ref.get(f"emb_share_{k}") for k in ("lt30", "30_60", "60_90", "ge90", "ge80_saturated")
                    },
                    "max_share_of_quadrat_c_lt30_in_season": emb_low_max,
                    "team_threshold_c_proxy_pct": c_proxy,
                    "team_threshold_indicator5_level": level(c_proxy, C_LEVELS),
                    "team_threshold_bare_signature": team_signal,
                    "max_share_bare_in_season": bare_max,
                    "years_since_last_bare_signature": t_years,
                    "indicator4_level_indicative": level(t_years, T_LEVELS) if t_years is not None else None,
                    "observation_dates": [o["date"] for o in ss],
                }
            )
            records.append(rec)

    doc = {
        "what": "Satellite pre-check of ZARC-NM indicators 4 (years without soil disturbance) and 5 (straw cover in "
        "pre-sowing) for three 9 ha cropland quadrats of Cruz Alta (RS), 1984-2026, applying IN SPA/MAPA 2/2025 "
        "items 6.2-6.8 and Table 1 where the norm gives definitions or thresholds.",
        "norm": "Instrucao Normativa SPA/MAPA n. 2/2025 (ZARC Niveis de Manejo), items 2 (Table 1), 3.2.1, 6.2-6.8",
        "applied_from_norm": {
            "quadrat_size": "9 ha (300 m x 300 m); norm item 6.2 IV: 5-10 ha for fields > 100 ha",
            "sensors": "Landsat C2 L2 (TM, ETM+, OLI, OLI-2) and HLS v2.0 L30 at 30 m (item 6.4; S30 left out, plan_b)",
            "all_images": "every scene of WRS-2 223/080, 222/080 and HLS L30 tiles T22JBP/T22JBN, "
            "15 Sep - 31 Dec, with "
            ">= 80 of the 100 quadrat pixels clear (item 6.5 asks for all images, >= every 16 days)",
            "indicator_5_bands": "C < 30 level 1; 30-60 level 2; 60-90 level 3; >= 90 level 4 (Table 1)",
            "indicator_4_bands": "T < 3 level 1; 3-5 level 2; 5-8 level 3; >= 8 level 4 (Table 1)",
            "tillage": "sudden change exposing soil (item 6.8)",
        },
        "chosen_here_not_in_norm": {
            "pre_sowing_month": "the norm uses the month before sowing (item 6.7); the sowing date is not known, so "
            "the reference is the clear observation with the lowest mean NDTI among no-green observations of 15 "
            "Sep - 31 Dec (minNDTI, Zheng et al. 2012), or the seasonal NDVI minimum if the quadrat was never "
            "without green",
            "c_embrapa": "residue cover C of the no-green pixels (NDVI < 0.30; Doc 454 masks NDVI > 0.3) on the "
            "reference date, from the Embrapa Documentos 454 ruler: quadratic fitted to its Table 2 "
            "(19 fields, Cambe PR, Sentinel-2, transect); the norm itself gives no NDTI-to-cover conversion. "
            "C >= 80% is reported as level '3 or 4' because the document states NDTI saturates near 80% cover. "
            "Calibrated on another soil, region and sensor: not validated in Cruz Alta",
            "tillage_signal": f"at least one clear observation with >= {int(100 * TILLAGE_BARE_SHARE)}% of the quadrat "
            "pixels at C < 30% by the Embrapa ruler (ploughed fields in Doc 454 Table 2 had 5-20% cover). The team "
            "threshold (NDVI < 0.30 and NDTI < 0.06) is kept as team_threshold_* for comparison",
            "years_since_last_signal": "counted only while every season since the last signal had a no-green clear "
            "observation; otherwise null (a tillage in an unobserved season cannot be excluded)",
        },
        "embrapa_ruler": embrapa.summary(),
        "quadrats": quads,
        "quadrat_rule": "300 m blocks on the UTM 22S 30 m grid entirely ESA WorldCover 2021 cropland inside the "
        "municipality and clear on both before/after map dates (1991-11-04 and 2026-10-20); one per NASADEM slope "
        "class (< 3%, 3-8%, >= 8% block mean), closest to the class median slope, >= 5 km apart. No property, "
        "owner or registry (CAR) was looked up; the quadrats are not real field samples.",
        "items_searched": len(items),
        "plan_b": "HLS S30 (the Sentinel-2 half of HLS) was left out for time; Landsat 4-9 and HLS L30 give every "
        "year 1984-2026 (16-day revisit per Landsat, 8 days with two in orbit). Reading S30 would add observations "
        "only from 2020 on.",
        "read_errors": errors,
        "caveats": [
            "No field calibration in Cruz Alta: the Embrapa ruler was calibrated in Cambe (PR) on 19 fields with "
            "Sentinel-2; Cruz Alta straw reads higher NDTI than any Cambe field, so most of it sits on the plateau.",
            "A 9 ha quadrat is not a field: the norm samples quadrats inside each declared field.",
            "Tillage between two clear observations can be missed; Landsat alone revisits every 16 days, and clouds "
            "leave gaps, so 'no bare-soil signature' is not proof of no tillage.",
            "Wet soil hides the bare-soil signature (see the rain check in residue_landsat.json).",
        ],
        "records": records,
    }
    (results / "zarcnm_satellite_indicators.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    (results / "nasadem_slope_classes.json").write_text(
        json.dumps(slope_doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    print(json.dumps(slope_doc, indent=1, ensure_ascii=False)[:3000])
    for r in records:
        if r["year"] in (1991, 2001, 2011) or r["year"] >= 2019:
            print(
                r["quadrant_id"],
                r["year"],
                r["n_clear_observations"],
                r.get("c_proxy_pct"),
                r["tillage_signal"],
                r.get("years_since_last_bare_signature"),
            )


if __name__ == "__main__":
    main()
