# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Re-downloads the daily inputs of the seven-city test from public services (no account) and compares them with the committed
inputs/daily_imerg_power_seven_cities.csv. It does not overwrite the committed file.

- NASA POWER Daily API, community AG, at the team's point of each municipality: T2M_MAX, T2M_MIN, T2M, RH2M, WS2M,
  ALLSKY_SFC_SW_DWN, 1 Jul 2000 - 30 Jun 2025.
- GPM IMERG V07 daily via SERVIR ClimateSERV (dataset 226), mean of a 0.1 degree box centred on the same point.
Points are those of the team research (FieldShift team research, daily master table).
Run: uv run --no-project --with pandas python fetch_inputs.py [power|imerg|all]
"""

import gzip
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
POINTS = {  # municipality: (lat, lon)
    "Cruz Alta": (-28.70, -53.56),
    "Ijuí": (-28.32, -53.89),
    "Jóia": (-28.77, -54.15),
    "São Miguel das Missões": (-28.67, -54.52),
    "São Luiz Gonzaga": (-28.42, -54.89),
    "Espumoso": (-28.86, -52.83),
    "Júlio de Castilhos": (-29.26, -53.65),
}
POWER_VARS = {
    "T2M_MAX": "power_tmax_c",
    "T2M_MIN": "power_tmin_c",
    "T2M": "power_tmean_c",
    "RH2M": "power_rh_pct",
    "WS2M": "power_wind2m_m_s",
    "ALLSKY_SFC_SW_DWN": "power_srad_mj_m2",
}
CLIMATESERV = "https://climateserv.servirglobal.net/api/"
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


def fetch_power(name: str) -> pd.DataFrame:
    lat, lon = POINTS[name]
    url = (
        "https://power.larc.nasa.gov/api/temporal/daily/point?parameters="
        f"{','.join(POWER_VARS)}&community=AG&longitude={lon}&latitude={lat}&start=20000701&end=20250630&format=JSON"
    )
    par = json.loads(get(url, 240))["properties"]["parameter"]
    df = pd.DataFrame({POWER_VARS[k]: pd.Series(v) for k, v in par.items()})
    df.index = pd.to_datetime(df.index, format="%Y%m%d")
    return df.where(df > -900)


def fetch_imerg(name: str) -> pd.Series:
    lat, lon = POINTS[name]
    h = 0.05
    ring = [[lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h], [lon - h, lat + h], [lon - h, lat - h]]
    poly = {"type": "Polygon", "coordinates": [ring]}
    geom = urllib.parse.quote(json.dumps(poly))
    series: dict[str, float] = {}
    for begin, end in RANGES:
        url = (
            f"{CLIMATESERV}submitDataRequest/?datatype=226&begintime={begin}&endtime={end}"
            f"&intervaltype=0&operationtype=5&geometry={geom}"
        )
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
        for e in data["data"]:
            v = e["value"]
            v = v.get("avg") if isinstance(v, dict) else v
            if v is None or v < -900:
                continue
            mm, dd, yy = e["date"].split("/")
            series[f"{yy}-{mm}-{dd}"] = round(float(v), 2)
    s = pd.Series(series, name="imerg_precip_mm")
    s.index = pd.to_datetime(s.index)
    return s


def compare(what: str) -> None:
    committed = pd.read_csv(os.path.join(HERE, "inputs", "daily_imerg_power_seven_cities.csv"), parse_dates=["date"])
    fn = fetch_power if what == "power" else fetch_imerg
    with ThreadPoolExecutor(max_workers=7) as ex:
        got = dict(zip(POINTS, ex.map(fn, POINTS), strict=True))
    for name, new in got.items():
        old = committed[committed.municipality == name].set_index("date")
        cols = list(POWER_VARS.values()) if what == "power" else ["imerg_precip_mm"]
        new = new.to_frame() if isinstance(new, pd.Series) else new
        for c in cols:
            a, b = old[c], new[c].reindex(old.index)
            ok = a.notna() & b.notna()
            worst = float((a[ok] - b[ok]).abs().max())
            print(f"{what} {name} {c}: {int(ok.sum())} days compared, max |diff| = {worst:.2f}", flush=True)


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for w in ("power", "imerg") if arg == "all" else (arg,):
        compare(w)
