# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Heavy rain (>= 50 mm in a day) by fortnight of the year beside the share of cropland with no
green cover, at Cruz Alta (RS, Brazil).

    python -I storms.py <raw_dir> <results_dir>

Rain: GPM IMERG via NASA POWER (main), NASA POWER PRECTOTCORR and the ANA 2853015 rain gauge
(checks), 2001-2025. No green: the published Sentinel-2 10 m / MODIS 250 m calendar
(data/sites/cruz-alta/output/bare-soil-calendar.json) and its per-scene input.

Loaders and constants are imported from the services/science package (read only, never edited):
`fieldshift.sources.power_imerg`, `fieldshift.sources.power`, `fieldshift.complements.rain_signal`
and `fieldshift.complements.baresoil`.
"""

import csv
import json
import statistics
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml
from fieldshift.complements import baresoil, rain_signal
from fieldshift.complements import provenance as cp
from fieldshift.sources import power, power_imerg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SITE = ROOT / "data" / "sites" / "cruz-alta"
IMERG_CACHE = ROOT / "data" / "cache" / "power-imerg" / "cruz-alta" / "daily_19980101_20251231.json"
POWER_CACHE = ROOT / "data" / "cache" / "power" / "cruz-alta" / "daily_19810101_20261031.json"
CALENDAR = SITE / "output" / "bare-soil-calendar.json"
RAIN_SIGNAL = SITE / "output" / "enso-rain-signal.json"
S2_SCENES = SITE / "input" / baresoil.S2_INPUT

HEAVY_MM = rain_signal.HEAVY_MM  # 50 mm, same threshold as the published ENSO heavy-rain signal
YEARS = range(2001, 2026)  # common window of the three rain sources (25 years)
ANA_LONG = range(1982, 2026)  # the gauge's long record, same first year as enso-rain-signal
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()


def fortnight_of(d: date) -> int:
    """0..23, as in the bare-soil calendar: days 1-15 = first half, 16-end = second half."""
    return (d.month - 1) * 2 + (0 if d.day <= 15 else 1)


def fortnight_days(year: int, idx: int) -> list[date]:
    month, half = idx // 2 + 1, idx % 2
    d = date(year, month, 1 if half == 0 else 16)
    out = []
    while d.month == month and (half == 1 or d.day <= 15):
        out.append(d)
        d += timedelta(days=1)
    return out


def label(idx: int) -> str:
    return f"{MONTHS[idx // 2]} {'1-15' if idx % 2 == 0 else '16-end'}"


def fortnight_stats(daily: dict[date, float | None], years: range) -> list[dict]:
    """Per fortnight: years with a complete fortnight, % of them with >= 1 heavy day, mean heavy days."""
    out = []
    for idx in range(24):
        n = hit = days = 0
        for y in years:
            vals = [daily.get(d) for d in fortnight_days(y, idx)]
            if any(v is None for v in vals):
                continue  # a year counts only when every day of the fortnight has a value
            k = sum(1 for v in vals if v >= HEAVY_MM)
            n, hit, days = n + 1, hit + (k > 0), days + k
        out.append(
            {
                "n_years": n,
                "years_with_heavy": hit,
                "pct_years_heavy": round(100 * hit / n, 1) if n else None,
                "mean_heavy_days": round(days / n, 3) if n else None,
            }
        )
    return out


def wilson(hit: int, n: int, z: float = 1.96) -> tuple[float | None, float | None]:
    """95% Wilson score interval of a proportion, in %: how much 25 years can say."""
    if not n:
        return None, None
    p = hit / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / (1 + z * z / n)
    return round(100 * (centre - half), 1), round(100 * (centre + half), 1)


def load_ana(raw: Path) -> tuple[dict[date, float | None], dict]:
    path = raw / "ana_daily_2853015.csv"
    with path.open(encoding="utf-8", newline="") as fh:
        daily = {
            date.fromisoformat(r["date"]): float(r["rain_mm"]) if r["rain_mm"] else None for r in csv.DictReader(fh)
        }
    access = json.loads((raw / "ana_serie_2853015.access.json").read_text(encoding="utf-8"))
    return daily, access


def cross_check(sid: str, daily: dict[date, float | None], first: int) -> dict:
    """Recompute September-November heavy days per year with the pipeline's own function and compare
    them with the published enso-rain-signal.json: proves the series read here is the same."""
    pub = next(s for s in json.loads(RAIN_SIGNAL.read_text(encoding="utf-8"))["sources"] if s["id"] == sid)
    mine = rain_signal.season_years(daily, range(first, rain_signal.LAST_YEAR + 1))
    compared = diff = 0
    for y in pub["years"]:
        if y["year"] < first or y["heavy_days"] is None:
            continue
        compared += 1
        v = mine.get(y["year"])
        if v is None or v[1] != y["heavy_days"] or abs(round(v[0], 1) - y["total_mm"]) > 0.11:
            diff += 1
    return {"source": sid, "years_compared": compared, "years_different": diff}


def main() -> None:
    raw, results = Path(sys.argv[1]), Path(sys.argv[2])
    results.mkdir(parents=True, exist_ok=True)
    point = yaml.safe_load((SITE / "input" / "site.yaml").read_text(encoding="utf-8"))["point"]
    lat, lon = point["lat"], point["lon"]

    imerg = power_imerg.parse(json.loads(IMERG_CACHE.read_text(encoding="utf-8")), lat=lat, lon=lon)
    pw = power.parse(json.loads(POWER_CACHE.read_text(encoding="utf-8")), lat=lat, lon=lon)
    pw_rain = pw.daily["PRECTOTCORR"]
    ana, ana_access = load_ana(raw)

    checks = [
        cross_check("gpm-imerg", imerg.daily, 1998),
        cross_check("nasa-power", pw_rain, rain_signal.FIRST_YEAR),
        cross_check("ana-2853015", ana, rain_signal.FIRST_YEAR),
    ]

    st = {
        "imerg": fortnight_stats(imerg.daily, YEARS),
        "ana": fortnight_stats(ana, YEARS),
        "power": fortnight_stats(pw_rain, YEARS),
        "ana_long": fortnight_stats(ana, ANA_LONG),
    }

    cal = json.loads(CALENDAR.read_text(encoding="utf-8"))
    fn = {f["index"]: f for f in cal["fortnights"]}

    # per-scene no-green share, with the calendar's own filters (years, clear fraction)
    scenes: dict[tuple[int, int], dict] = {}
    with S2_SCENES.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            y = int(r["year"])
            if baresoil.FIRST_YEAR <= y <= baresoil.LAST_YEAR and float(r["clear_fraction"]) >= baresoil.MIN_CLEAR:
                scenes[(y, int(r["fortnight"]))] = r
    s2_check_diff = 0
    for idx in range(24):
        v = [float(r["fraction_ndvi_lt_0_25"]) for (y, i), r in scenes.items() if i == idx]
        if v and round(100 * statistics.median(v), 1) != fn[idx]["s2_median_pct"]:
            s2_check_diff += 1

    rows = []
    for idx in range(24):
        f, im = fn[idx], st["imerg"][idx]
        exposure = (
            round(im["pct_years_heavy"] * f["s2_median_pct"] / 100, 1)
            if im["pct_years_heavy"] is not None and f["s2_median_pct"] is not None
            else None
        )
        row = {"fortnight_index": idx, "month": idx // 2 + 1, "half": idx % 2 + 1, "label": label(idx)}
        for key in ("imerg", "ana", "power"):
            s = st[key][idx]
            row[f"{key}_n_years"] = s["n_years"]
            row[f"{key}_pct_years_heavy"] = s["pct_years_heavy"]
            row[f"{key}_mean_heavy_days"] = s["mean_heavy_days"]
            if key == "imerg":
                row["imerg_pct_ci95_low"], row["imerg_pct_ci95_high"] = wilson(s["years_with_heavy"], s["n_years"])
        row["ana_1982_2025_n_years"] = st["ana_long"][idx]["n_years"]
        row["ana_1982_2025_pct_years_heavy"] = st["ana_long"][idx]["pct_years_heavy"]
        row["s2_no_green_median_pct"] = f["s2_median_pct"]
        row["s2_no_green_min_pct"] = f["s2_min_pct"]
        row["s2_no_green_max_pct"] = f["s2_max_pct"]
        row["s2_years"] = f["s2_years"]
        row["modis_no_green_median_pct"] = f["modis_median_pct"]
        row["exposure_index_pct"] = exposure
        rows.append(row)
    ranked = sorted((r for r in rows if r["exposure_index_pct"] is not None), key=lambda r: -r["exposure_index_pct"])
    for rank, r in enumerate(ranked, 1):
        r["exposure_rank"] = rank

    # observed coincidences 2019-2025: each heavy-rain day and the no-green share of the scene of
    # the same year and fortnight (the scene can be up to two weeks before or after the storm)
    events = []
    for sid, daily in (("gpm-imerg", imerg.daily), ("ana-2853015", ana)):
        for d, v in sorted(daily.items()):
            if v is None or v < HEAVY_MM or not (baresoil.FIRST_YEAR <= d.year <= baresoil.LAST_YEAR):
                continue
            sc = scenes.get((d.year, fortnight_of(d)))
            events.append(
                {
                    "source": sid,
                    "date": d.isoformat(),
                    "rain_mm": round(v, 1),
                    "fortnight": label(fortnight_of(d)),
                    "s2_scene_date": sc["date"] if sc else None,
                    "s2_no_green_pct": round(100 * float(sc["fraction_ndvi_lt_0_25"]), 1) if sc else None,
                }
            )

    def tally(sid: str) -> dict:
        ev = [e for e in events if e["source"] == sid]
        with_scene = [e for e in ev if e["s2_no_green_pct"] is not None]
        return {
            "heavy_days": len(ev),
            "with_a_scene_in_the_same_fortnight": len(with_scene),
            "on_no_green_ge_25pct": sum(1 for e in with_scene if e["s2_no_green_pct"] >= 25),
            "on_no_green_ge_50pct": sum(1 for e in with_scene if e["s2_no_green_pct"] >= 50),
        }

    ana_years_complete = {
        "2001_2025": [r["ana_n_years"] for r in rows],
        "note": "ANA 2853015 has a gap in 2013-2016; a year counts in a fortnight only when every day has a reading.",
    }

    sources = {
        "gpm-imerg": {
            "name": "GPM IMERG daily precipitation (IMERG_PRECTOT, UTC days), served by NASA POWER",
            "group": "NASA",
            "url": imerg.url,
            "accessed_at": imerg.accessed_at,
            "doi": power_imerg.IMERG_DOI,
            "cache": str(IMERG_CACHE.relative_to(ROOT)).replace("\\", "/"),
            "attribution": cp.NASA_IMERG.model_dump(exclude_none=True),
        },
        "nasa-power": {
            "name": "NASA POWER daily precipitation, PRECTOTCORR (MERRA-2 bias-corrected)",
            "group": "NASA",
            "url": pw.url,
            "accessed_at": pw.accessed_at,
            "cache": str(POWER_CACHE.relative_to(ROOT)).replace("\\", "/"),
            "attribution": cp.NASA_POWER.model_dump(exclude_none=True),
        },
        "ana-2853015": {
            "name": "ANA rain gauge 2853015 (Tres Capoes, 14.9 km from the site point), daily rain, HidroWeb",
            "group": "other public (Brazil)",
            "url": ana_access["url"],
            "accessed_at": ana_access["accessed_at"],
            "cache": "not committed (raw folder)",
            "attribution": cp.ANA.model_dump(exclude_none=True),
        },
        "sentinel-2": {
            "name": "Copernicus Sentinel-2 L2A, 10 m, share of cropland with NDVI < 0.25 (bare-soil calendar)",
            "group": "partner (ESA Copernicus)",
            "url": "https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a",
            "accessed_at": baresoil.S2_ACCESSED_AT,
            "file": str(CALENDAR.relative_to(ROOT)).replace("\\", "/"),
            "attribution": cp.ESA_S2.model_dump(exclude_none=True),
        },
        "modis": {
            "name": "MODIS MOD13Q1/MYD13Q1 v061 NDVI, 250 m, share of cropland with NDVI < 0.25",
            "group": "NASA",
            "url": "https://lpdaac.usgs.gov/products/mod13q1v061/",
            "accessed_at": baresoil.MODIS_ACCESSED_AT,
            "file": str(CALENDAR.relative_to(ROOT)).replace("\\", "/"),
            "attribution": cp.NASA_MODIS.model_dump(exclude_none=True),
        },
    }
    columns = {
        "fortnight_index": "0..23; days 1-15 and 16-end of each month (same index as bare-soil-calendar.json)",
        "imerg_n_years": "gpm-imerg: years 2001-2025 with a complete fortnight",
        "imerg_pct_years_heavy": "gpm-imerg: % of those years with at least one day >= 50 mm",
        "imerg_mean_heavy_days": "gpm-imerg: mean number of days >= 50 mm per fortnight",
        "imerg_pct_ci95_low": "gpm-imerg: 95% Wilson interval of imerg_pct_years_heavy, lower end "
        "(years as independent trials)",
        "imerg_pct_ci95_high": "gpm-imerg: 95% Wilson interval of imerg_pct_years_heavy, upper end",
        "ana_n_years": "ana-2853015: years 2001-2025 with a complete fortnight",
        "ana_pct_years_heavy": "ana-2853015: % of those years with at least one day >= 50 mm",
        "ana_mean_heavy_days": "ana-2853015: mean number of days >= 50 mm per fortnight",
        "power_n_years": "nasa-power: years 2001-2025 with a complete fortnight",
        "power_pct_years_heavy": "nasa-power: % of those years with at least one day >= 50 mm",
        "power_mean_heavy_days": "nasa-power: mean number of days >= 50 mm per fortnight",
        "ana_1982_2025_n_years": "ana-2853015: years 1982-2025 with a complete fortnight",
        "ana_1982_2025_pct_years_heavy": "ana-2853015: % of those years with at least one day >= 50 mm",
        "s2_no_green_median_pct": "sentinel-2: median over 2019-2025 of the cropland share with NDVI < 0.25",
        "s2_no_green_min_pct": "sentinel-2: lowest year 2019-2025",
        "s2_no_green_max_pct": "sentinel-2: highest year 2019-2025",
        "s2_years": "sentinel-2: years with a usable scene (at least half of the cropland pixels clear)",
        "modis_no_green_median_pct": "modis: median over 2019-2025 of the share of valid observations with NDVI < 0.25",
        "exposure_index_pct": "imerg_pct_years_heavy x s2_no_green_median_pct / 100. A ranking aid that treats "
        "the two as independent; not a measured erosion quantity and not a probability of soil loss",
        "exposure_rank": "1 = highest exposure_index_pct",
    }

    with (results / "storms_by_fortnight.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) + ["exposure_rank"], lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

    doc = {
        "_si": "SI-assisted: script written with Claude Code (Anthropic); numbers produced by running it on the "
        "sources below.",
        "question": "In which fortnights of the year do heavy-rain days (>= 50 mm) coincide with cropland that has "
        "no green cover?",
        "site": {"id": "cruz-alta", "point": {"lat": lat, "lon": lon}},
        "heavy_rain_mm": HEAVY_MM,
        "rain_years": f"{YEARS.start}-{YEARS.stop - 1}",
        "cover_years": f"{baresoil.FIRST_YEAR}-{baresoil.LAST_YEAR}",
        "ndvi_threshold": baresoil.NDVI_THRESHOLD,
        "columns": columns,
        "sources": sources,
        "fortnights": rows,
        "top_exposure": [
            {
                k: r[k]
                for k in (
                    "label",
                    "imerg_pct_years_heavy",
                    "ana_pct_years_heavy",
                    "s2_no_green_median_pct",
                    "exposure_index_pct",
                )
            }
            for r in ranked[:4]
        ],
        "observed_2019_2025": {
            "summary": {"gpm-imerg": tally("gpm-imerg"), "ana-2853015": tally("ana-2853015")},
            "note": "Heavy-rain day matched with the Sentinel-2 scene of the same year and fortnight; the scene "
            "date can differ from the storm by up to about two weeks, and the cover share is municipal (9 blocks), "
            "not the field under the storm.",
            "events": events,
        },
        "checks": {
            "sep_nov_heavy_days_vs_enso_rain_signal_json": checks,
            "s2_median_recomputed_from_scenes_fortnights_different": s2_check_diff,
        },
        "ana_coverage": ana_years_complete,
        "caveats": [
            baresoil.STRAW_CAVEAT,
            "The 50 mm threshold is a convention (the same as the published ENSO heavy-rain signal), "
            "not an erosion threshold.",
            "Rain is a single point (IMERG 0.1 degree cell, POWER 0.5 x 0.625 degree cell, one gauge 14.9 km away); "
            "cover is a municipal share. Neither is the field.",
            "Rain covers 25 years and cover only 7: the two curves describe different periods.",
            "IMERG and POWER use UTC days; the gauge is read in the morning, so its day is shifted against them.",
        ],
    }
    (results / "storms_bare_soil.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n"
    )
    print("checks:", json.dumps(doc["checks"]))
    print("top exposure:", json.dumps(doc["top_exposure"]))
    print("observed:", json.dumps(doc["observed_2019_2025"]["summary"]))


if __name__ == "__main__":
    main()
