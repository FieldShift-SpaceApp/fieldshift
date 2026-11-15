# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Green / straw / probable bare soil on Cruz Alta cropland, per scene and per year, with every check.

    python -I series.py <raw_dir> <results_dir>

Reads the per-scene histograms written by scenes.py and the context files written by fetch_context.py;
reads the NASA POWER and GPM IMERG daily rain already committed in data/cache/. Writes small results only:
scenes.csv, series.csv, residue_landsat.json.
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import numpy as np
from fieldshift.sources import power, power_imerg

ROOT = Path(__file__).resolve().parents[2]
IMERG_CACHE = ROOT / "data" / "cache" / "power-imerg" / "cruz-alta" / "daily_19980101_20251231.json"
POWER_CACHE = ROOT / "data" / "cache" / "power" / "cruz-alta" / "daily_19810101_20261031.json"
LAT, LON = -28.703, -53.563

# Thresholds. NDVI < 0.30: "many agricultural studies" mask green vegetation this way before reading residue
# (Hively et al. 2021, citing Beeson et al. 2020, Daughtry et al. 2006, Serbin et al. 2009); 0.25 is the
# team's bare-soil calendar threshold. NDTI: no transferable published threshold exists (residue-cover models
# are calibrated per site and soil; Zheng et al. 2014; Hively et al. 2021), so 0.06 is this analysis's choice
# and 0.04-0.10 is the sensitivity range; an Otsu valley on the pooled histograms is reported as a data check.
NDVI_MAIN, NDVI_ALT = 0.30, (0.25, 0.35)
NDTI_MAIN, NDTI_LOW, NDTI_HIGH = 0.06, 0.04, 0.10
NDTI_OTSU_NEAR = 0.12  # close to the Otsu valley of the 1984-1995 histograms; reported, not used
NDTI_GRID = (0.04, 0.05, 0.06, 0.07, 0.08, 0.10)
MIN_CLEAR = 0.5  # at least half of the municipal cropland pixels clear (same rule as the bare-soil calendar)
WET_MM_3D = 10.0  # rain in the 3 days before the scene that marks it "wet" (convention; 5 and 20 mm also shown)
PAIR_DAYS = 8


def load_hist(h: dict, n_v: int, n_t: int) -> np.ndarray:
    m = np.zeros((n_v, n_t), dtype=np.int64)
    for i, j, c in h["sparse"]:
        m[i, j] = c
    return m


def classes(m: np.ndarray, ndvi_edges: np.ndarray, ndti_edges: np.ndarray, ndvi_t: float, ndti_t: float) -> dict:
    iv = int(np.searchsorted(ndvi_edges, ndvi_t - 1e-9))  # first bin with lower edge >= threshold
    it = int(np.searchsorted(ndti_edges, ndti_t - 1e-9))
    total = m.sum()
    nogreen = m[:iv, :]
    bare = nogreen[:, :it].sum()
    ng = nogreen.sum()
    return {
        "green": 100 * (total - ng) / total,
        "straw": 100 * (ng - bare) / total,
        "bare": 100 * bare / total,
        "bare_of_nogreen": (100 * bare / ng) if ng else None,
    }


def ndti_median_nogreen(m: np.ndarray, ndvi_edges, ndti_edges, ndvi_t: float) -> float | None:
    iv = int(np.searchsorted(ndvi_edges, ndvi_t - 1e-9))
    col = m[:iv, :].sum(axis=0)
    if col.sum() == 0:
        return None
    cum = np.cumsum(col)
    k = int(np.searchsorted(cum, cum[-1] / 2))
    return float((ndti_edges[k] + ndti_edges[k + 1]) / 2)


def otsu(counts: np.ndarray, edges: np.ndarray) -> float:
    """Otsu (1979) threshold of a histogram; returns the upper edge of the last bin of the low class."""
    centers = (edges[:-1] + edges[1:]) / 2
    w = counts.astype(float)
    p = w / w.sum()
    omega = np.cumsum(p)
    mu = np.cumsum(p * centers)
    mu_t = mu[-1]
    with np.errstate(invalid="ignore", divide="ignore"):
        sb = (mu_t * omega - mu) ** 2 / (omega * (1 - omega))
    sb[~np.isfinite(sb)] = -1
    k = int(np.argmax(sb))
    return float(edges[k + 1])


def r1(x):
    return None if x is None else round(float(x), 1)


def r3(x):
    return None if x is None else round(float(x), 3)


def med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else None


def sensor_of(s: dict) -> str:
    if s["collection"] == "hls2-s30":
        return "HLS S30"
    if s["collection"] == "hls2-l30":
        return "HLS L30"
    return {"landsat-4": "Landsat 4 TM", "landsat-5": "Landsat 5 TM", "landsat-7": "Landsat 7 ETM+"}.get(
        s["platform"], {"landsat-8": "Landsat 8 OLI", "landsat-9": "Landsat 9 OLI-2"}.get(s["platform"], s["platform"])
    )


def rain_sum(daily: dict, d: date, days: int) -> float | None:
    vals = [daily.get(d - timedelta(days=k)) for k in range(1, days + 1)]
    return None if any(v is None for v in vals) else round(sum(vals), 1)


def main() -> None:
    raw, results = Path(sys.argv[1]), Path(sys.argv[2])
    results.mkdir(parents=True, exist_ok=True)
    index = json.loads((raw / "scene_index.json").read_text(encoding="utf-8"))
    ndvi_edges, ndti_edges = np.array(index["ndvi_edges"]), np.array(index["ndti_edges"])
    nv, nt = len(ndvi_edges) - 1, len(ndti_edges) - 1

    # rain: NASA POWER PRECTOTCORR (committed cache + tail fetched at run time) and GPM IMERG via POWER
    pw = power.parse(json.loads(POWER_CACHE.read_text(encoding="utf-8")), lat=LAT, lon=LON).daily["PRECTOTCORR"]
    pw = dict(pw)
    tail = json.loads((raw / "context" / "power_prectotcorr_tail.json").read_text(encoding="utf-8"))
    for k, v in tail["body"]["properties"]["parameter"]["PRECTOTCORR"].items():
        pw[date(int(k[:4]), int(k[4:6]), int(k[6:]))] = None if v is None or v < -900 else float(v)
    imerg = power_imerg.parse(json.loads(IMERG_CACHE.read_text(encoding="utf-8")), lat=LAT, lon=LON).daily

    # scenes; HLS items of the same day and sensor on the two MGRS tiles are merged
    groups: dict[tuple, list] = defaultdict(list)
    for iid in index["items"]:
        f = raw / "scenes" / f"{iid}.json"
        if not f.exists():
            continue
        s = json.loads(f.read_text(encoding="utf-8"))
        key = (s["collection"], s["date"]) if s["collection"].startswith("hls") else (s["collection"], s["id"])
        groups[key].append(s)

    scenes = []
    for (_coll, _), ss in sorted(groups.items(), key=lambda kv: kv[1][0]["date"]):
        s0 = ss[0]
        m = sum(load_hist(s["hist"], nv, nt) for s in ss)
        mh = sum(load_hist(s["hist_roy2016"], nv, nt) for s in ss) if "hist_roy2016" in s0 else None
        valid = sum(s["valid_cropland_pixels"] for s in ss)
        crop = max(s["cropland_pixels_municipality"] for s in ss)
        clear = min(1.0, valid / crop) if crop else 0.0
        d = date.fromisoformat(s0["date"])
        row = {
            "scene": "+".join(s["id"] for s in ss),
            "date": s0["date"],
            "year": d.year,
            "season": s0["season"],
            "sensor": sensor_of(s0),
            "collection": s0["collection"],
            "wrs_path_row": s0["wrs_path_row"],
            "mgrs_tiles": "+".join(s["mgrs_tile"] for s in ss) if s0["mgrs_tile"] else None,
            "tile_cloud_cover": s0["tile_cloud_cover"],
            "cropland_clear_fraction": round(clear, 3),
            "accepted": clear >= MIN_CLEAR and valid > 0,
            "rain_power_2d_mm": rain_sum(pw, d, 2),
            "rain_power_3d_mm": rain_sum(pw, d, 3),
            "rain_power_7d_mm": rain_sum(pw, d, 7),
            "rain_imerg_3d_mm": rain_sum(imerg, d, 3),
            "_m": m,
            "_mh": mh,
        }
        row["wet_3d"] = None if row["rain_power_3d_mm"] is None else row["rain_power_3d_mm"] >= WET_MM_3D
        if valid:
            c = classes(m, ndvi_edges, ndti_edges, NDVI_MAIN, NDTI_MAIN)
            row.update(
                {
                    "pct_green": r1(c["green"]),
                    "pct_straw": r1(c["straw"]),
                    "pct_bare": r1(c["bare"]),
                    "pct_bare_of_nogreen": r1(c["bare_of_nogreen"]),
                    "pct_bare_ndti_0_04": r1(classes(m, ndvi_edges, ndti_edges, NDVI_MAIN, NDTI_LOW)["bare"]),
                    "pct_bare_ndti_0_10": r1(classes(m, ndvi_edges, ndti_edges, NDVI_MAIN, NDTI_HIGH)["bare"]),
                    "pct_bare_ndti_0_12": r1(classes(m, ndvi_edges, ndti_edges, NDVI_MAIN, NDTI_OTSU_NEAR)["bare"]),
                    "pct_bare_ndvi_0_25": r1(classes(m, ndvi_edges, ndti_edges, 0.25, NDTI_MAIN)["bare"]),
                    "pct_bare_ndvi_0_35": r1(classes(m, ndvi_edges, ndti_edges, 0.35, NDTI_MAIN)["bare"]),
                    "pct_bare_roy2016": r1(classes(mh, ndvi_edges, ndti_edges, NDVI_MAIN, NDTI_MAIN)["bare"])
                    if mh is not None
                    else None,
                    "ndti_median_nogreen": r3(ndti_median_nogreen(m, ndvi_edges, ndti_edges, NDVI_MAIN)),
                }
            )
        scenes.append(row)

    acc = [s for s in scenes if s["accepted"]]
    landsat = [s for s in acc if s["collection"] == "landsat-c2-l2"]
    hls = [s for s in acc if s["collection"].startswith("hls")]

    def yearly(rows: list, family: str) -> list[dict]:
        by = defaultdict(list)
        for s in rows:
            by[(s["season"], s["year"])].append(s)
        out = []
        for (season, year), ss in sorted(by.items()):
            dry = [s for s in ss if s["wet_3d"] is False]
            out.append(
                {
                    "family": family,
                    "season": season,
                    "year": year,
                    "n_scenes": len(ss),
                    "n_dry_scenes": len(dry),
                    "sensors": "/".join(sorted({s["sensor"] for s in ss})),
                    "dates": " ".join(s["date"] for s in ss),
                    "pct_bare_median": r1(med([s["pct_bare"] for s in ss])),
                    "pct_bare_min": r1(min(s["pct_bare"] for s in ss)),
                    "pct_bare_max": r1(max(s["pct_bare"] for s in ss)),
                    "pct_bare_median_ndti_0_04": r1(med([s["pct_bare_ndti_0_04"] for s in ss])),
                    "pct_bare_median_ndti_0_10": r1(med([s["pct_bare_ndti_0_10"] for s in ss])),
                    "pct_bare_median_ndti_0_12": r1(med([s["pct_bare_ndti_0_12"] for s in ss])),
                    "pct_bare_median_ndvi_0_25": r1(med([s["pct_bare_ndvi_0_25"] for s in ss])),
                    "pct_bare_median_ndvi_0_35": r1(med([s["pct_bare_ndvi_0_35"] for s in ss])),
                    "pct_bare_median_dry_only": r1(med([s["pct_bare"] for s in dry])),
                    "pct_bare_median_roy2016": r1(med([s["pct_bare_roy2016"] for s in ss])),
                    "pct_green_median": r1(med([s["pct_green"] for s in ss])),
                    "pct_straw_median": r1(med([s["pct_straw"] for s in ss])),
                    "pct_bare_of_nogreen_median": r1(med([s["pct_bare_of_nogreen"] for s in ss])),
                }
            )
        return out

    series = yearly(landsat, "landsat") + yearly(hls, "hls")

    # epochs (median of annual medians, Landsat, each season)
    epochs = {}
    for season in ("spring", "autumn"):
        rows = [r for r in series if r["family"] == "landsat" and r["season"] == season]
        for a, b in ((1984, 1994), (1995, 2004), (2005, 2014), (2015, 2026)):
            sel = [r for r in rows if a <= r["year"] <= b]
            epochs[f"{season} {a}-{b}"] = {
                "years_with_data": len(sel),
                "pct_bare_median": r1(med([r["pct_bare_median"] for r in sel])),
                "pct_bare_median_ndti_0_04": r1(med([r["pct_bare_median_ndti_0_04"] for r in sel])),
                "pct_bare_median_ndti_0_10": r1(med([r["pct_bare_median_ndti_0_10"] for r in sel])),
                "pct_bare_median_ndti_0_12": r1(med([r["pct_bare_median_ndti_0_12"] for r in sel])),
                "pct_bare_median_roy2016": r1(med([r["pct_bare_median_roy2016"] for r in sel])),
                "pct_bare_median_dry_only": r1(med([r["pct_bare_median_dry_only"] for r in sel])),
            }

    # rain check: wet vs dry scenes, per era (Landsat spring)
    rain_check = {}
    for label, a, b in (("1984-1999", 1984, 1999), ("2000-2012", 2000, 2012), ("2013-2026", 2013, 2026)):
        sel = [s for s in landsat if s["season"] == "spring" and a <= s["year"] <= b and s["wet_3d"] is not None]
        for thr in (5.0, WET_MM_3D, 20.0):
            wet = [s for s in sel if s["rain_power_3d_mm"] >= thr]
            dry = [s for s in sel if s["rain_power_3d_mm"] < thr]
            rain_check[f"{label} wet>={thr:g}mm"] = {
                "n_wet": len(wet),
                "n_dry": len(dry),
                "pct_bare_median_wet": r1(med([s["pct_bare"] for s in wet])),
                "pct_bare_median_dry": r1(med([s["pct_bare"] for s in dry])),
                "ndti_nogreen_median_wet": r3(med([s["ndti_median_nogreen"] for s in wet])),
                "ndti_nogreen_median_dry": r3(med([s["ndti_median_nogreen"] for s in dry])),
            }

    # sensor checks: near-simultaneous pairs
    def pairs(a_rows, b_rows, max_days, same_ok=False):
        out = []
        for x in a_rows:
            for y in b_rows:
                if x is y or (not same_ok and x["sensor"] == y["sensor"]):
                    continue
                dd = abs((date.fromisoformat(x["date"]) - date.fromisoformat(y["date"])).days)
                if dd <= max_days and x["season"] == y["season"]:
                    out.append((x, y, dd))
        return out

    def summarize(ps, label):
        diffs = [y["pct_bare"] - x["pct_bare"] for x, y, _ in ps]
        nd = [
            y["ndti_median_nogreen"] - x["ndti_median_nogreen"]
            for x, y, _ in ps
            if x["ndti_median_nogreen"] is not None and y["ndti_median_nogreen"] is not None
        ]
        return {
            "pairs": len(ps),
            "definition": label,
            "median_diff_pct_bare_points": r1(med(diffs)),
            "median_abs_diff_pct_bare_points": r1(med([abs(v) for v in diffs])),
            "max_abs_diff_pct_bare_points": r1(max((abs(v) for v in diffs), default=None)),
            "median_diff_ndti_nogreen": r3(med(nd)),
            "examples": [
                {"a": x["scene"], "b": y["scene"], "days": dd, "a_pct_bare": x["pct_bare"], "b_pct_bare": y["pct_bare"]}
                for x, y, dd in ps[:6]
            ],
        }

    by_sensor = defaultdict(list)
    for s in acc:
        by_sensor[s["sensor"]].append(s)
    l5, l7, l8, l9 = (by_sensor[k] for k in ("Landsat 5 TM", "Landsat 7 ETM+", "Landsat 8 OLI", "Landsat 9 OLI-2"))
    sensor_checks = {
        "L7 minus L5 (<= 8 days)": summarize(pairs(l5, l7, PAIR_DAYS), "Landsat 7 minus Landsat 5"),
        "L8 minus L7 (<= 8 days)": summarize(pairs(l7, l8, PAIR_DAYS), "Landsat 8 minus Landsat 7"),
        "L9 minus L8 (<= 8 days)": summarize(pairs(l8, l9, PAIR_DAYS), "Landsat 9 minus Landsat 8"),
        "HLS L30 minus Landsat C2 L2 (same day)": summarize(
            pairs(l8 + l9, by_sensor["HLS L30"], 0), "HLS L30 minus Landsat 8/9 C2 L2 of the same acquisition"
        ),
        "HLS S30 minus HLS L30 (<= 3 days)": summarize(
            pairs(by_sensor["HLS L30"], by_sensor["HLS S30"], 3), "HLS S30 minus HLS L30"
        ),
    }
    roy = [s for s in landsat if s["pct_bare_roy2016"] is not None]
    sensor_checks["Roy et al. 2016 ETM+->OLI transform applied to TM/ETM+"] = {
        "scenes": len(roy),
        "median_diff_pct_bare_points": r1(med([s["pct_bare_roy2016"] - s["pct_bare"] for s in roy])),
        "max_abs_diff_pct_bare_points": r1(
            max((abs(s["pct_bare_roy2016"] - s["pct_bare"]) for s in roy), default=None)
        ),
    }

    # Otsu valley of NDTI over no-green pixels (pooled), as a data check of the 0.06 choice
    iv = int(np.searchsorted(ndvi_edges, NDVI_MAIN - 1e-9))

    def pooled(rows):
        tot = np.zeros(nt, dtype=np.int64)
        for s in rows:
            tot += s["_m"][:iv, :].sum(axis=0)
        return tot

    otsu_check = {}
    for label, rows in (
        ("Landsat spring 1984-1995", [s for s in landsat if s["season"] == "spring" and s["year"] <= 1995]),
        ("Landsat spring, all years", [s for s in landsat if s["season"] == "spring"]),
        ("Landsat autumn, all years", [s for s in landsat if s["season"] == "autumn"]),
    ):
        counts = pooled(rows)
        if counts.sum():
            otsu_check[label] = {"scenes": len(rows), "otsu_ndti": r3(otsu(counts, ndti_edges))}

    # census (independent check)
    ctx = raw / "context"

    def sidra_values(name):
        doc = json.loads((ctx / f"{name}.json").read_text(encoding="utf-8"))
        vals = {}
        for v in doc["body"]:
            for res in v["resultados"]:
                cat = "/".join(next(iter(c["categoria"].values())) for c in res["classificacoes"])
                for sr in res["series"]:
                    for per, val in sr["serie"].items():
                        vals[(v["variavel"], sr["localidade"]["nome"], cat, per)] = val
        return doc["url"], doc["accessed_utc"], vals

    def num(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None

    census = {"sources": {}}
    for name in ("census_2006_849", "census_2017_6855", "pam_1612_area"):
        url, at, vals = sidra_values(name)
        census["sources"][name] = {"url": url, "accessed_utc": at}
        census[name] = {" | ".join(k): v for k, v in vals.items()}
    area06 = num(
        next(
            v
            for k, v in census["census_2006_849"].items()
            if k.startswith("Área com plantio direto") and "Cruz Alta" in k
        )
    )
    area17 = num(
        next(
            v
            for k, v in census["census_2017_6855"].items()
            if k.startswith("Área com plantio direto") and "Cruz Alta" in k
        )
    )
    pam = census["pam_1612_area"]
    soy06 = num(next(v for k, v in pam.items() if "Soja" in k and k.endswith("2006")))
    soy17 = num(next(v for k, v in pam.items() if "Soja" in k and k.endswith("2017")))
    mz06 = num(next(v for k, v in pam.items() if "Milho" in k and k.endswith("2006")))
    mz17 = num(next(v for k, v in pam.items() if "Milho" in k and k.endswith("2017")))
    sat = {
        y: r1(
            med(
                [
                    r["pct_bare_median"]
                    for r in series
                    if r["family"] == "landsat" and r["season"] == "spring" and abs(r["year"] - y) <= 2
                ]
            )
        )
        for y in (2006, 2017)
    }
    census["summary"] = {
        "no_till_area_ha": {"2006": area06, "2017": area17},
        "pam_planted_soybean_ha": {"2006": soy06, "2017": soy17},
        "pam_planted_maize_ha": {"2006": mz06, "2017": mz17},
        "no_till_area_over_soybean_plus_maize_pct": {
            "2006": r1(100 * area06 / (soy06 + mz06)),
            "2017": r1(100 * area17 / (soy17 + mz17)),
        },
        "satellite_spring_pct_bare_median_of_years_within_2": sat,
        "note": (
            "Census no-till area counts every crop of the reference year on establishments that used no-till, so it is "
            "compared with the summer-crop planted area (soybean + maize, PAM) only as an order of magnitude. Both "
            "census years say no-till covers about the whole summer-crop area of Cruz Alta; the satellite agrees if "
            "probable bare soil in the spring window is near zero around those years."
        ),
    }

    # write
    cols = [k for k in scenes[0] if not k.startswith("_")]
    allcols = list(dict.fromkeys(cols + [k for s in scenes for k in s if not k.startswith("_")]))
    with (results / "scenes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=allcols, lineterminator="\n")
        w.writeheader()
        for s in scenes:
            w.writerow({k: s.get(k) for k in allcols})
    with (results / "series.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(series[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(series)

    doc = {
        "question": "Share of Cruz Alta cropland with a probable bare-soil signature (no green, low NDTI), per year, "
        "in late October - mid November (before soybean canopy closes) and in April - May, 1984-2026 "
        "(Landsat 5 starts in 1984).",
        "thresholds": {
            "ndvi_green_min": NDVI_MAIN,
            "ndvi_sensitivity": list(NDVI_ALT),
            "ndti_bare_below": NDTI_MAIN,
            "ndti_sensitivity": [NDTI_LOW, NDTI_HIGH],
            "ndti_grid_available": list(NDTI_GRID),
            "min_cropland_clear_fraction": MIN_CLEAR,
            "wet_scene_rain_3d_mm": WET_MM_3D,
        },
        "classes": {
            "green": "NDVI >= 0.30",
            "straw": "NDVI < 0.30 and NDTI >= 0.06 (non-photosynthetic residue signature)",
            "probable_bare_soil": "NDVI < 0.30 and NDTI < 0.06",
        },
        "search": {
            k: index[k]
            for k in (
                "searched_utc",
                "stac",
                "windows",
                "max_tile_cloud_cover",
                "landsat_wrs",
                "hls_tiles",
                "worldcover_item",
            )
        },
        "scene_read_errors": index.get("errors", {}),
        "counts": {
            "scenes_read": len(scenes),
            "scenes_accepted": len(acc),
            "landsat_accepted": len(landsat),
            "hls_accepted": len(hls),
            "by_sensor_accepted": {k: len(v) for k, v in sorted(by_sensor.items())},
        },
        "epochs_landsat": epochs,
        "rain_check": rain_check,
        "sensor_checks": sensor_checks,
        "otsu_check": otsu_check,
        "census_check": census,
        "rain_sources": {
            "power": "NASA POWER daily PRECTOTCORR (MERRA-2 bias-corrected), committed cache "
            "data/cache/power/cruz-alta/daily_19810101_20261031.json plus a run-time tail: " + tail["url"],
            "power_tail_accessed_utc": tail["accessed_utc"],
            "imerg": "GPM IMERG daily as served by NASA POWER (IMERG_PRECTOT, UTC days), committed cache "
            "data/cache/power-imerg/cruz-alta/daily_19980101_20251231.json",
        },
        "attribution": "NASA/USGS Landsat Collection 2 Level-2; NASA HLS v2.0 (LP DAAC), both read through the "
        "Microsoft Planetary Computer; ESA WorldCover 2021 (contains modified Copernicus Sentinel data 2021); "
        "IBGE Censo Agropecuario 2006 and 2017, IBGE PAM; NASA POWER; GPM IMERG.",
        "caveats": [
            "No field calibration: 'probable bare soil' is a spectral inference with a threshold chosen by this "
            "analysis, not a measured residue cover.",
            "NDTI is sensitive to soil and residue moisture (Quemada and Daughtry 2016) and to kaolinite-rich soils "
            "(Hively et al. 2021); the Oxisols of Cruz Alta are kaolinitic.",
            "Different sensors (TM, ETM+, OLI, OLI-2, MSI) without a field-based cross-calibration of NDTI.",
            "One cropland mask (WorldCover 2021) for 40 years: fields that changed use are misclassified.",
        ],
    }
    (results / "residue_landsat.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n"
    )
    print(json.dumps({k: doc[k] for k in ("counts", "epochs_landsat", "otsu_check")}, indent=1))


if __name__ == "__main__":
    main()
