# SI-assisted: Claude Code (Anthropic), port of FieldShift team research; review: pending (see SI-USAGE.md)
"""Public inputs of the team rotation evidence, Cruz Alta (RS, Brazil). No login, no key.

    python -I fetch_inputs.py <raw_dir> <results_dir> [imerg|pam|ipca ...]

imerg  Daily GPM IMERG V07 (NASA) through SERVIR ClimateSERV (datatype 226, the id used by the team
       research), mean over a 0.1 degree box centred on the Cruz Alta site point, 1 July 2000 - 30 June 2025.
       -> results/imerg_daily_cruz_alta.csv
pam    IBGE PAM, SIDRA table 1612: harvested area (216) and value of production (215) of soybean and wheat,
       Cruz Alta (4306106), 2001-2025.  -> results/ibge_pam_1612_cruz_alta_value.csv
ipca   IBGE IPCA, SIDRA table 1737, variable 2266 (index number), monthly, 2000-2025.
       -> results/ibge_ipca_1737_annual_mean.csv (annual mean of the monthly index)
Raw API answers go to <raw_dir> (not committed).
"""

from __future__ import annotations

import csv
import datetime as dt
import gzip
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

LAT, LON, HALF = -28.70, -53.56, 0.05  # Cruz Alta site point (same as data/sites/cruz-alta)
MUN = "4306106"
CLIMATESERV = "https://climateserv.servirglobal.net/api/"
IMERG_DATATYPE = 226  # ClimateSERV dataset id used by the team research script (IMERG V07 daily)
RANGES = [("07/01/2000", "06/30/2015"), ("07/01/2015", "06/30/2025")]
UA = {"User-Agent": "fieldshift-analysis/1.0"}


def get(url: str, timeout: int = 120, tries: int = 4) -> bytes:
    err: Exception | None = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                b = r.read()
            return gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b
        except Exception as e:  # noqa: BLE001 - retried, then raised
            err = e
            time.sleep(3 + 3 * attempt)
    raise RuntimeError(f"{url}: {err}")


def stamp() -> str:
    return dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_imerg(raw: Path, results: Path) -> None:
    poly = {
        "type": "Polygon",
        "coordinates": [
            [
                [LON - HALF, LAT - HALF],
                [LON + HALF, LAT - HALF],
                [LON + HALF, LAT + HALF],
                [LON - HALF, LAT + HALF],
                [LON - HALF, LAT - HALF],
            ]
        ],
    }
    geom = urllib.parse.quote(json.dumps(poly))
    series: dict[str, float] = {}
    urls = []
    for begin, end in RANGES:
        url = (
            f"{CLIMATESERV}submitDataRequest/?datatype={IMERG_DATATYPE}&begintime={begin}&endtime={end}"
            f"&intervaltype=0&operationtype=5&geometry={geom}"
        )
        urls.append(url)
        job = json.loads(get(url, 60))[0]
        t0 = time.time()
        data = None
        while time.time() - t0 < 2400:
            time.sleep(6)
            try:
                p = json.loads(get(f"{CLIMATESERV}getDataRequestProgress/?id={job}", 40, 1))
            except Exception:  # noqa: BLE001 - progress polling is retried
                continue
            if p and float(p[0]) >= 100:
                data = json.loads(get(f"{CLIMATESERV}getDataFromRequest/?id={job}", 180))
                break
            if p and float(p[0]) < 0:
                break
        if data is None:
            raise RuntimeError(f"ClimateSERV job {job} did not finish")
        (raw / f"climateserv_imerg_{begin[-4:]}.json").write_text(json.dumps(data), encoding="utf-8")
        for e in data["data"]:
            v = e["value"]
            v = v.get("avg") if isinstance(v, dict) else v
            if v is None or v < -900:
                continue
            mm, dd, yy = e["date"].split("/")
            series[f"{yy}-{mm}-{dd}"] = round(float(v), 2)
        print("IMERG", begin, end, len(series), flush=True)
    out = results / "imerg_daily_cruz_alta.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        f.write(
            f"# GPM IMERG V07 daily precipitation (NASA GES DISC), via SERVIR ClimateSERV datatype {IMERG_DATATYPE}, "
            f"mean of a {2 * HALF} degree box centred on {LAT}, {LON}; accessed {stamp()}\n"
        )
        f.write(f"# requests: {' | '.join(u.split('&geometry=')[0] for u in urls)}\n")
        w = csv.writer(f)
        w.writerow(["date", "rain_mm"])
        d = dt.date(2000, 7, 1)
        while d <= dt.date(2025, 6, 30):
            w.writerow([d.isoformat(), series.get(d.isoformat(), "")])
            d += dt.timedelta(1)
    print("wrote", out)


def fetch_pam(raw: Path, results: Path) -> None:
    years = ",".join(str(y) for y in range(2001, 2026))
    url = f"https://apisidra.ibge.gov.br/values/t/1612/n6/{MUN}/v/215,216/p/{years}/c81/2713,2716"
    rows = json.loads(get(url, 180))
    (raw / "sidra_1612_value_area.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    crop = {"2713": "soybean", "2716": "wheat"}
    var = {"215": "value_thousand_brl", "216": "harvested_area_ha"}
    table: dict[tuple[int, str], dict[str, str]] = {}
    for r in rows[1:]:
        table.setdefault((int(r["D3C"]), crop[r["D4C"]]), {})[var[r["D2C"]]] = r["V"]
    out = results / "ibge_pam_1612_cruz_alta_value.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        f.write(
            f"# IBGE, Produção Agrícola Municipal (PAM), SIDRA table 1612, Cruz Alta (RS) {MUN}; "
            f"{url}; accessed {stamp()}\n"
        )
        w = csv.writer(f)
        w.writerow(["year", "crop", "harvested_area_ha", "value_thousand_brl"])
        for (y, c), v in sorted(table.items()):
            w.writerow([y, c, v.get("harvested_area_ha", ""), v.get("value_thousand_brl", "")])
    print("wrote", out)


def fetch_ipca(raw: Path, results: Path) -> None:
    url = "https://apisidra.ibge.gov.br/values/t/1737/n1/all/v/2266/p/200001-202512"
    rows = json.loads(get(url, 120))
    (raw / "sidra_1737_ipca.json").write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    by_year: dict[str, list[float]] = {}
    for r in rows[1:]:
        if r["V"] in ("...", "-", ""):
            continue
        by_year.setdefault(r["D3C"][:4], []).append(float(r["V"]))
    out = results / "ibge_ipca_1737_annual_mean.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        f.write(
            f"# IBGE, IPCA index number (Dec 1993 = 100), SIDRA table 1737 variable 2266; {url}; accessed {stamp()}\n"
        )
        w = csv.writer(f)
        w.writerow(["year", "months", "ipca_index_annual_mean"])
        for y, v in sorted(by_year.items()):
            w.writerow([y, len(v), round(sum(v) / len(v), 2)])
    print("wrote", out)


def main() -> None:
    raw, results = Path(sys.argv[1]), Path(sys.argv[2])
    raw.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    which = sys.argv[3:] or ["pam", "ipca", "imerg"]
    for name in which:
        {"imerg": fetch_imerg, "pam": fetch_pam, "ipca": fetch_ipca}[name](raw, results)


if __name__ == "__main__":
    main()
