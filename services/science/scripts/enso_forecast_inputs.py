# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Build the forecast-scorecard inputs from the primary archives (run by hand, not in CI).

Writes, for one issue month (default February) and the JJA target of the same year:
- data/cache/noaa/oni.ascii.txt (+ oni.source.json): the NOAA CPC ONI file as published;
- data/sites/<site>/input/enso-forecasts.csv: one row per source and target year, with the URL of
  the primary file the value was read from.

Sources (open, no login; one connection at a time; raw files go to --cache, outside git):
- NOAA CPC ONI: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
- CPC/IRI official consensus probabilities: table of the IRI "quick look" page of the month.
- IRI objective probabilities (figure 3) and model plume (figure 4) of the IRI ENSO forecast
  archive, SVG served by https://ensoforecast.iri.columbia.edu/<figure3_plot|figure4_plot>/<y>/<m>.
- NASA GMAO GEOS-S2S in the NMME (NASA_GEOS5v2): ensemble-mean Niño-3.4 forecast files of
  https://ftp.cpc.ncep.noaa.gov/NMME/ENSO/NASA_GEOS5v2/<MM>0100/, anomaly against the model's own
  1991-2020 climatology for the same start month and lead (removes model drift).

Fails closed: each URL is retried with backoff on timeouts and transient statuses; the rows are
checked against the EXPECTED manifest (source x target year, February issue) and the NMME
climatology years; only a complete run replaces the ONI files and the CSV, each atomically.
Otherwise it exits 1 and leaves them untouched.

Run:
  uv run --with numpy --with xarray --with netCDF4 python -I scripts/enso_forecast_inputs.py \
      --cache <dir> --out ../../data/sites/cruz-alta/input --oni-out ../../data/cache/noaa
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html as htmlmod
import io
import json
import os
import re
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import httpx

CPC = "https://www.cpc.ncep.noaa.gov"
ONI_URL = f"{CPC}/data/indices/oni.ascii.txt"
IRI = "https://ensoforecast.iri.columbia.edu"
QL = "https://iri.columbia.edu/our-expertise/climate/forecasts/enso"
NMME = "https://ftp.cpc.ncep.noaa.gov/NMME/ENSO/NASA_GEOS5v2"
MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]
NUM = r"-?\d+(?:\.\d+)?"
LAST_TARGET_YEAR = 2025  # JJA 2026 is still preliminary in the ONI file (14/11/2026)
NMME_CLIMATOLOGY = range(1991, 2021)  # model climatology of the anomaly (same start and leads)

# Expected coverage of enso-forecasts.csv: target years per source, as read on 14/11/2026
# (121 values, equal to the team's research table). A run that yields anything else aborts and
# leaves the canonical files untouched. Asked for but not expected: 2003 objective bars (not
# drawn), 2012-2013 quick looks (no table), NMME 2023-2025 (no file for those starts). The NMME
# anomaly also needs every NMME_CLIMATOLOGY year (checked apart: those rows are in 1982-2022).
EXPECTED: dict[str, range] = {
    "cpc-iri-official": range(2014, LAST_TARGET_YEAR + 1),
    "iri-objective": range(2004, LAST_TARGET_YEAR + 1),
    "iri-plume-mean": range(2003, LAST_TARGET_YEAR + 1),
    "iri-plume-nasa-gmao": range(2003, LAST_TARGET_YEAR + 1),
    "nmme-nasa-geos": range(1982, 2023),
}
RETRIES = 4  # attempts per URL
BACKOFF_S = 2.0  # wait before attempt k >= 2: BACKOFF_S * 2 ** (k - 2)
RETRY_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class CoverageError(RuntimeError):
    """The downloaded archive does not cover the manifest: nothing is published."""


# ------------------------------------------------------------------ download


def fetch(
    client: httpx.Client,
    url: str,
    dest: Path,
    *,
    attempts: int = RETRIES,
    sleep: Callable[[float], None] = time.sleep,
) -> Path | None:
    """Raw file at `dest` (an existing non-empty file wins). Timeouts, transport errors and
    transient statuses are retried with exponential backoff; a definitive status (e.g. 404) or
    the last failed attempt gives None. The file is written whole or not at all."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    for k in range(1, attempts + 1):
        if k > 1:
            sleep(BACKOFF_S * 2 ** (k - 2))
        try:
            r = client.get(url)
        except httpx.TransportError as exc:  # every timeout is a TransportError
            print(f"attempt {k}/{attempts} {url}: {type(exc).__name__}")
            continue
        if r.status_code == 200 and r.content:
            write_atomic(dest, r.content)
            sleep(0.2)
            return dest
        print(f"attempt {k}/{attempts} {url}: HTTP {r.status_code}")
        if r.status_code not in RETRY_STATUS:
            return None
    return None


def write_atomic(path: Path, data: bytes) -> None:
    """Write next to `path`, then rename over it: a reader sees the old file or the new one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def missing_coverage(rows: list[list]) -> list[str]:
    """(source, year) pairs of EXPECTED without exactly one row, and rows outside EXPECTED."""
    got: dict[tuple[str, int], int] = {}
    for r in rows:
        key = (str(r[0]), int(r[2]))
        got[key] = got.get(key, 0) + 1
    out = [f"{sid} {y}" for sid, years in EXPECTED.items() for y in years if (sid, y) not in got]
    out += [f"{sid} {y} (x{n})" for (sid, y), n in sorted(got.items()) if n > 1]
    out += [
        f"{sid} {y} (not in the manifest)"
        for sid, y in sorted(got)
        if y not in EXPECTED.get(sid, ())
    ]
    return out


def csv_bytes(rows: list[list]) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(
        [
            "source_id",
            "issue_month",
            "target_year",
            "p_la_nina",
            "p_neutral",
            "p_el_nino",
            "nino34_anomaly_degC",
            "source_url",
        ]
    )
    w.writerows(sorted(rows, key=lambda r: (r[0], r[2])))
    return buf.getvalue().encode("utf-8")


def publish(rows: list[list], oni_raw: bytes, oni_accessed: str, out: Path, oni_out: Path) -> None:
    """Check the manifest first; only then replace the ONI file and the CSV, each atomically."""
    if missing := missing_coverage(rows):
        raise CoverageError(
            f"{len(missing)} coverage problems, {out / 'enso-forecasts.csv'} and "
            f"{oni_out / 'oni.ascii.txt'} left untouched: {', '.join(missing)}"
        )
    source = {
        "url": ONI_URL,
        "accessed_at": oni_accessed,
        "sha256": hashlib.sha256(oni_raw).hexdigest(),
    }
    write_atomic(oni_out / "oni.ascii.txt", oni_raw)
    write_atomic(oni_out / "oni.source.json", (json.dumps(source, indent=1) + "\n").encode())
    write_atomic(out / "enso-forecasts.csv", csv_bytes(rows))


# ------------------------------------------------------------------ IRI SVG (matplotlib)


def _blocks(txt: str, prefix: str, indent: int | None = None) -> list[str]:
    """<g id="prefixN"> blocks up to the next block of the same prefix. `indent` filters by the
    line indentation (matplotlib indents axis objects by 3 spaces, the legend by 4)."""
    pat = rf'\n {{{indent}}}<g id="({prefix}\d+)">' if indent else rf'<g id="({prefix}\d+)">'
    starts = [m.start() for m in re.finditer(pat, txt)]
    return [
        txt[a : (starts[i + 1] if i + 1 < len(starts) else len(txt))] for i, a in enumerate(starts)
    ]


def _comment(s: str) -> str | None:
    m = re.search(r"<!-- (.*?) -->", s)
    return m.group(1).strip() if m else None


def _xticks(txt: str) -> list[tuple[str, float]]:
    out = {}
    for b in _blocks(txt, "xtick_"):
        b = b.split('<g id="ytick_')[0]
        m = re.search(rf'<use xlink:href="#[^"]+" x="({NUM})" y="{NUM}"', b)
        lbl = _comment(b)
        if m and lbl:
            out[lbl] = float(m.group(1))
    return sorted(out.items(), key=lambda kv: kv[1])


def _style(block: str, markers: dict[str, str]) -> tuple | None:
    m = re.search(r'<path d="[^"]*"[^>]*style="([^"]*)"', block)
    if not m:
        return None
    st = {
        k.strip(): v.strip()
        for k, v in (x.split(":", 1) for x in m.group(1).split(";") if ":" in x)
    }
    mk = re.search(r'<use xlink:href="#(m[0-9a-f]+)"', block)
    shape = markers.get(mk.group(1), "") if mk else ""
    return (st.get("stroke"), st.get("stroke-width", "1.5"), st.get("stroke-dasharray", ""), shape)


def _points(block: str) -> list[tuple[float, float]]:
    m = re.search(r'<path d="([^"]*)"', block)
    return (
        [(float(x), float(y)) for x, y in re.findall(rf"[ML] ({NUM}) ({NUM})", m.group(1))]
        if m
        else []
    )


def plume_jja(path: Path, names: tuple[str, ...]) -> dict[str, float]:
    """JJA value of the named plume lines. The y axis is calibrated on the black reference lines
    (solid = 0, dash-dot = +/-0.5): some old SVGs have swapped y labels."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    markers = {
        m.group(1): re.sub(r"\s+", " ", m.group(2)).strip()
        for m in re.finditer(r'<path id="(m[0-9a-f]+)" d="([^"]*)"', txt)
    }
    cut = txt.find('<g id="legend_1">')
    body, legend = txt[:cut], txt[cut:]
    entries = [(_comment(b), _style(b, markers)) for b in _blocks(legend, "line2d_")]
    entries = [
        (n.strip(), k)
        for n, k in entries
        if k and n is not None and n.strip() and not n.strip().endswith(":")
    ]
    lines = [
        (k, p)
        for k, p in ((_style(b, markers), _points(b)) for b in _blocks(body, "line2d_", 3))
        if k and len(p) >= 2
    ]
    flat = [
        (k, p)
        for k, p in lines
        if k[0] == "#000000" and k[1] == "2" and abs(p[0][1] - p[-1][1]) < 1e-6
    ]
    zero = [p[0][1] for k, p in flat if not k[2]]
    half = sorted(p[0][1] for k, p in flat if k[2])
    if len(zero) != 1 or len(half) != 2:
        raise ValueError(f"{path.name}: reference lines not found")
    a = 1.0 / (half[0] - half[1])  # half[0] is +0.5 (higher on screen = smaller y)
    c = -a * zero[0]
    import numpy as np  # only for the archive run (`uv run --with numpy`), not the CI tests

    ticks = _xticks(txt)
    step = float(np.median(np.diff([x for _, x in ticks])))
    jja_x = dict(ticks).get("JJA")
    out: dict[str, float] = {}
    count: dict[tuple, int] = {}
    per_style: dict[tuple, int] = {}
    for _, k in entries:
        per_style[k] = per_style.get(k, 0) + 1
    for name, k in entries:
        cand = [p for kk, p in lines if kk == k]
        j = count.get(k, 0)
        count[k] = j + 1
        if name not in names or jja_x is None or len(cand) != per_style[k]:
            continue  # repeated style with a different number of lines: ambiguous, skipped
        # repeated styles: matplotlib draws in legend order, so the j-th line is the j-th entry
        for x, y in cand[j]:
            if abs(x - jja_x) < 0.2 * step:
                out[name] = round(a * y + c, 3)
    return out


def probbars_jja(path: Path) -> dict[str, float] | None:
    """IRI figure 3 bars for JJA, normalized by their sum (the three categories add to 100%)."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    cut = txt.find('<g id="legend_1">')
    body, legend = txt[:cut], txt[cut:]
    colours = {}
    for b in _blocks(legend, "patch_"):
        m, name = re.search(r"fill: (#[0-9a-fA-F]{6})", b), _comment(b)
        if m and name and "Forecast" in name:
            colours[m.group(1).lower()] = (
                "la_nina" if "La Ni" in name else "neutral" if "Neutral" in name else "el_nino"
            )
    ticks = _xticks(txt)
    heights: dict[str, float] = {}
    for b in _blocks(body, "patch_", 3):
        m, p = re.search(r"fill: (#[0-9a-fA-F]{6})", b), re.search(r'<path d="([^"]*)"', b)
        if not (m and p) or m.group(1).lower() not in colours:
            continue
        pts = [(float(x), float(y)) for x, y in re.findall(rf"[ML] ({NUM}) ({NUM})", p.group(1))]
        if len(pts) < 4:
            continue
        xm = (min(x for x, _ in pts) + max(x for x, _ in pts)) / 2
        if min(ticks, key=lambda kv: abs(kv[1] - xm))[0] == "JJA":
            heights[colours[m.group(1).lower()]] = max(y for _, y in pts) - min(y for _, y in pts)
    total = sum(heights.values())
    if len(heights) != 3 or not total:
        return None
    return {k: round(v / total, 3) for k, v in heights.items()}


def quicklook_jja(path: Path) -> dict[str, float] | None:
    """First La Niña / Neutral / El Niño table (official CPC/IRI consensus), JJA row."""
    txt = path.read_text(encoding="utf-8", errors="replace")
    for t in re.findall(r"<table.*?</table>", txt, flags=re.S | re.I):
        plain = htmlmod.unescape(re.sub(r"<[^>]+>", " ", t))
        if "Neutral" not in plain or "Ni" not in plain:
            continue
        for row in re.findall(r"<tr.*?</tr>", t, flags=re.S | re.I):
            cells = [
                htmlmod.unescape(re.sub(r"<[^>]+>", " ", x)).strip()
                for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S | re.I)
            ]
            if len(cells) >= 4 and cells[0][:3] == "JJA":
                v = [float(re.sub(r"[^0-9.]", "", x)) / 100 for x in cells[1:4]]
                return {"la_nina": v[0], "neutral": v[1], "el_nino": v[2]}
        return None  # only the first matching table is the official consensus
    return None


# ------------------------------------------------------------------ NMME GEOS


def nmme_jja_anomalies(files: dict[int, Path], issue_month: int) -> dict[int, float]:
    """Ensemble-mean Niño-3.4 of each start year, JJA mean, minus the 1991-2020 mean of the same
    start month and leads. First target = the month in the file name (checked by the shape of the
    annual cycle in the team's analysis: 14 of 18 model/month combinations agree)."""
    import numpy as np
    import xarray as xr

    idx = [6 - issue_month + i for i in range(3)]  # positions of June, July, August
    series = {}
    for year, f in files.items():
        with xr.open_dataset(f, decode_times=False) as ds:
            v = ds["fcst"].values.ravel().astype(float)
        if np.all(np.isfinite(v)) and len(v) > max(idx):
            series[year] = v[idx]
    if missing := sorted(set(NMME_CLIMATOLOGY) - set(series)):  # a shorter mean shifts every year
        raise CoverageError(f"NMME climatology years without a usable forecast: {missing}")
    clim = np.mean([series[y] for y in NMME_CLIMATOLOGY], axis=0)
    return {y: round(float(np.mean(v - clim)), 3) for y, v in sorted(series.items())}


# ------------------------------------------------------------------ main


def collect(
    client: httpx.Client, cache: Path, m: int, sleep: Callable[[float], None] = time.sleep
) -> tuple[list[list], bytes, str]:
    """Download (into `cache`) and read every source: (rows, raw ONI file, ONI access time).
    Nothing outside `cache` is written here."""

    def get(url: str, dest: Path) -> Path | None:
        return fetch(client, url, dest, sleep=sleep)

    # Raw ONI file, kept as published (30 kB) so the pipeline derives every phase from it.
    oni_path = get(ONI_URL, cache / "oni.ascii.txt")
    if oni_path is None:
        raise CoverageError(f"ONI file not downloaded: {ONI_URL}")
    accessed = datetime.fromtimestamp(oni_path.stat().st_mtime).astimezone()

    rows: list[list] = []
    for y in range(2003, LAST_TARGET_YEAR + 1):
        url = f"{IRI}/figure4_plot/{y}/{m}"
        f4 = get(url, cache / "iri" / f"figure4_plot_{y}_{m:02d}.svg")
        if f4:
            vals = plume_jja(f4, ("COMBINED AVG", "NASA GMAO"))
            for name, sid in (
                ("COMBINED AVG", "iri-plume-mean"),
                ("NASA GMAO", "iri-plume-nasa-gmao"),
            ):
                if name in vals:
                    rows.append([sid, m, y, "", "", "", f"{vals[name]:.3f}", url])
        url = f"{IRI}/figure3_plot/{y}/{m}"
        f3 = get(url, cache / "iri" / f"figure3_plot_{y}_{m:02d}.svg")
        q = probbars_jja(f3) if f3 else None
        if q:
            rows.append(["iri-objective", m, y, q["la_nina"], q["neutral"], q["el_nino"], "", url])
        if y >= 2012:
            url = f"{QL}/{y}-{MONTHS[m - 1]}-quick-look/"
            fq = get(url, cache / "iri" / f"quicklook_{y}_{m:02d}.html")
            q = quicklook_jja(fq) if fq else None
            if q:
                rows.append(
                    ["cpc-iri-official", m, y, q["la_nina"], q["neutral"], q["el_nino"], "", url]
                )
    files: dict[int, Path] = {}
    urls: dict[int, str] = {}
    for y in range(1982, LAST_TARGET_YEAR + 1):
        name = f"NASA_GEOS5v2.tmpsfc.{y}{m:02d}.Nino34.fcst.nc"
        url = f"{NMME}/{m:02d}0100/{name}"
        f = get(url, cache / "nmme" / name)
        if f:
            files[y], urls[y] = f, url
    if missing := sorted(set(NMME_CLIMATOLOGY) - set(files)):
        raise CoverageError(f"NMME climatology files not downloaded: {missing}")
    for y, v in nmme_jja_anomalies(files, m).items():
        rows.append(["nmme-nasa-geos", m, y, "", "", "", f"{v:.3f}", urls[y]])
    return rows, oni_path.read_bytes(), accessed.isoformat(timespec="seconds")


def main(argv: list[str] | None = None, client: httpx.Client | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--oni-out", type=Path, required=True)
    ap.add_argument("--issue-month", type=int, default=2, choices=[1, 2, 3])
    args = ap.parse_args(argv)
    client = client or httpx.Client(
        headers={"User-Agent": "fieldshift-science"},
        timeout=120,
        follow_redirects=True,
        limits=httpx.Limits(max_connections=1),
    )
    started = datetime.now().astimezone().isoformat(timespec="seconds")
    try:
        rows, oni_raw, oni_accessed = collect(client, args.cache, args.issue_month)
        publish(rows, oni_raw, oni_accessed, args.out, args.oni_out)
    except CoverageError as exc:
        print(f"aborted, nothing published: {exc}")
        return 1
    print(f"started {started}; {len(rows)} forecasts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
