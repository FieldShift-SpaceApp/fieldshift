# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Download the public sources of the drought-resilience test and write small per-year tables.

    python -I fetch_sources.py <raw_dir> <results_dir>

  yield    IBGE PAM, SIDRA table 1612: soybean (c81/2713) average yield (v/112) and planted area (v/109),
           the 18 municipalities, every year.
  climate  NASA POWER Daily API, PRECTOTCORR and T2M_MAX, one point per municipality centroid (IBGE),
           1981-01-01 to 2025-12-31. Per municipality and harvest year Y, the Dec(Y-1)-Feb(Y) window:
           rain total, longest dry spell (< 1 mm) and days with Tmax >= 32 C.
  gauge    ANA rain gauge 2853015 (same service and parser as analysis/storms-bare-soil/fetch_ana.py):
           the same DJF indices, a year only with a complete window.

Raw files stay in <raw_dir> (never committed). Small CSVs and sources.json go to <results_dir>.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import httpx

HERE = Path(__file__).resolve().parent
RAW = Path(sys.argv[1])
OUT = Path(sys.argv[2])
RAW.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
CLIENT = httpx.Client(headers={"User-Agent": "fieldshift-analysis/1.0"}, timeout=900, follow_redirects=True)
SOURCES: dict = {}
MUNS_CSV = HERE.parent / "ground-truth-proagro" / "results" / "municipalities.csv"
FIRST_HARVEST, LAST_HARVEST = 1982, 2025
DRY_MM, HOT_C = 1.0, 32.0


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def write_csv(name: str, rows: list[dict]) -> None:
    with (OUT / name).open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def municipalities() -> list[dict]:
    with MUNS_CSV.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def djf(y: int) -> list[date]:
    d, out = date(y - 1, 12, 1), []
    while d < date(y, 3, 1):
        out.append(d)
        d += timedelta(days=1)
    return out


def longest_dry(vals: list[float]) -> int:
    best = run = 0
    for v in vals:
        run = run + 1 if v < DRY_MM else 0
        best = max(best, run)
    return best


# --- yield ------------------------------------------------------------------------------------------
def yields() -> None:
    muns = municipalities()
    codes = ",".join(m["ibge_code"] for m in muns)
    url = f"https://apisidra.ibge.gov.br/values/t/1612/n6/{codes}/v/109,112/p/all/c81/2713?formato=json"
    p = RAW / "sidra_1612_soy.json"
    if not p.exists():
        r = CLIENT.get(url)
        r.raise_for_status()
        p.write_bytes(r.content)
    rows = json.loads(p.read_text(encoding="utf-8"))[1:]
    name = {m["ibge_code"]: m["municipality"] for m in muns}
    data: dict[tuple[str, int], dict] = {}
    for r in rows:
        key = (r["D1C"], int(r["D3C"]))
        v = r["V"].strip()
        val = float(v) if v.replace(".", "", 1).isdigit() else None
        col = {"112": "yield_kg_ha", "109": "planted_ha"}[r["D2C"]]
        data.setdefault(key, {})[col] = val
    out = []
    for (code, y), v in sorted(data.items()):
        if code in name and y >= 1974:
            out.append(
                {
                    "ibge_code": code,
                    "municipality": name[code],
                    "harvest_year": y,
                    "yield_kg_ha": "" if v.get("yield_kg_ha") is None else v["yield_kg_ha"],
                    "planted_ha": "" if v.get("planted_ha") is None else v["planted_ha"],
                }
            )
    write_csv("soy_yield.csv", out)
    SOURCES["ibge_pam_1612"] = {
        "url": url,
        "variables": {"112": "average yield kg/ha", "109": "planted area ha"},
        "product": "soybean (c81/2713)",
        "accessed_utc": now(),
    }


# --- climate ----------------------------------------------------------------------------------------
POWER = "https://power.larc.nasa.gov/api/temporal/daily/point"


def climate() -> None:
    rows, urls, versions = [], {}, set()
    for m in municipalities():
        params = {
            "parameters": "PRECTOTCORR,T2M_MAX",
            "community": "AG",
            "longitude": f"{float(m['lon']):.4f}",
            "latitude": f"{float(m['lat']):.4f}",
            "start": "19810101",
            "end": "20251231",
            "format": "JSON",
        }
        dest = RAW / "power" / f"{m['ibge_code']}.json"
        dest.parent.mkdir(exist_ok=True)
        if not dest.exists():
            for attempt in range(4):
                r = CLIENT.get(POWER, params=params)
                if r.status_code == 200:
                    dest.write_bytes(r.content)
                    break
                time.sleep(10 * (attempt + 1))
            else:
                raise RuntimeError(f"POWER {m['municipality']}: HTTP {r.status_code}")
        urls[m["ibge_code"]] = str(httpx.URL(POWER, params=params))
        d = json.loads(dest.read_text(encoding="utf-8"))
        versions.add(str(d.get("header", {}).get("api", {}).get("version", "")))
        fill = float(d.get("header", {}).get("fill_value", -999.0))
        par = d["properties"]["parameter"]

        def series(k: str, fill: float = fill, par: dict = par) -> dict[date, float | None]:
            return {
                datetime.strptime(t, "%Y%m%d").date(): (None if v is None or v == fill else float(v))
                for t, v in par[k].items()
            }

        rain, tmax = series("PRECTOTCORR"), series("T2M_MAX")
        for y in range(FIRST_HARVEST, LAST_HARVEST + 1):
            pr = [rain.get(dd) for dd in djf(y)]
            tx = [tmax.get(dd) for dd in djf(y)]
            if any(v is None for v in pr):
                continue
            rows.append(
                {
                    "ibge_code": m["ibge_code"],
                    "municipality": m["municipality"],
                    "harvest_year": y,
                    "djf_rain_mm": round(sum(pr), 1),
                    "djf_longest_dry_days": longest_dry(pr),
                    "djf_hot_days": "" if any(v is None for v in tx) else sum(v >= HOT_C for v in tx),
                }
            )
        print("power", m["municipality"], flush=True)
    write_csv("djf_power.csv", rows)
    SOURCES["nasa_power"] = {
        "api": POWER,
        "api_version": sorted(versions),
        "community": "AG",
        "time_standard": "LST (API default)",
        "parameters": {
            "PRECTOTCORR": "bias-corrected precipitation (MERRA-2 based), mm/day",
            "T2M_MAX": "daily maximum 2 m temperature, C (descriptive only)",
        },
        "urls": urls,
        "rule": "Dec 1 (Y-1) to end of Feb (Y); a year only with complete rain",
        "accessed_utc": now(),
    }


# --- gauge ------------------------------------------------------------------------------------------
def gauge() -> None:
    fetch = HERE.parent / "storms-bare-soil" / "fetch_ana.py"
    subprocess.run([sys.executable, "-I", str(fetch), str(RAW)], check=True)
    rain: dict[date, float | None] = {}
    with (RAW / "ana_daily_2853015.csv").open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rain[date.fromisoformat(r["date"])] = float(r["rain_mm"]) if r["rain_mm"] != "" else None
    rows = []
    for y in range(FIRST_HARVEST, LAST_HARVEST + 1):
        pr = [rain.get(dd) for dd in djf(y)]
        if any(v is None for v in pr):
            continue
        rows.append({"harvest_year": y, "djf_rain_mm": round(sum(pr), 1), "djf_longest_dry_days": longest_dry(pr)})
    write_csv("djf_ana_2853015.csv", rows)
    access = json.loads((RAW / "ana_serie_2853015.access.json").read_text(encoding="utf-8"))
    SOURCES["ana_2853015"] = {
        **access,
        "station": "2853015 (Tres Capoes, 14.9 km from the Cruz Alta point)",
        "rule": "level 2 (consisted) wins over level 1; a year only with a complete DJF",
    }


if __name__ == "__main__":
    steps = sys.argv[3].split(",") if len(sys.argv) > 3 else ["yields", "climate", "gauge"]
    path = OUT / "sources.json"
    for s in steps:
        {"yields": yields, "climate": climate, "gauge": gauge}[s]()
        cur = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        cur.update(SOURCES)
        path.write_text(json.dumps(cur, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
