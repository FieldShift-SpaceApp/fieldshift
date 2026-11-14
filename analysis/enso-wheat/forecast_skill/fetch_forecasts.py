# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Forecast skill, step A. Download the archive of ENSO forecasts issued in Jan/Feb/Mar and the observations.

Usage: python -I fetch_forecasts.py <cache_dir>

Sources (all open, no account; one connection at a time):
1. NOAA CPC ONI (oni.ascii.txt) and monthly Nino-3.4 ERSSTv5 (ersst5.nino.mth.91-20.ascii).
2. NOAA CPC NMME, folder NMME/ENSO/<model>/<MM>0100/: ensemble-mean Nino-3.4 per model and start
   month (hindcast + real time, 1982-2022 depending on the model).
   Models: CanCM4i, CFSv2, GEM5_NEMO, GFDL_SPEAR, NASA_GEOS5v2 (GMAO), NCAR_CCSM4.
3. IRI (Columbia) ENSO forecast archive: figure 4 (model plume, SVG) and figure 3 (IRI objective
   probability, SVG) served by ensoforecast.iri.columbia.edu/<fig>/<year>/<month>.
4. IRI quick look (HTML), which reproduces the official early-month CPC/IRI probability table.
5. NOAA CPC: Jan-Mar 2026 ENSO discussions (2026 official table is only an image in the quick look).

Everything goes to <cache_dir> (outside git); URLs and times go to <cache_dir>/sources.json.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx

CACHE = Path(sys.argv[1])
for p in (CACHE / "nmme", CACHE / "iri", CACHE / "cpc"):
    p.mkdir(parents=True, exist_ok=True)

CLIENT = httpx.Client(
    headers={"User-Agent": "fieldshift-analysis/1.0"},
    timeout=120,
    follow_redirects=True,
    limits=httpx.Limits(max_connections=1),
)
LOG: dict[str, dict] = {"_start": {"utc": datetime.now(UTC).isoformat(timespec="seconds")}}
FAILURES: list[dict] = []
MONTHS = [
    "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
]  # fmt: skip


def fetch(url: str, dest: Path, refresh: bool = False) -> bool:
    """Download unless already cached. Returns True if the file exists at the end."""
    if dest.exists() and dest.stat().st_size > 0 and not refresh:
        return True
    try:
        r = CLIENT.get(url)
    except httpx.HTTPError as e:
        FAILURES.append({"url": url, "error": type(e).__name__})
        return False
    if r.status_code != 200:
        FAILURES.append({"url": url, "status": r.status_code})
        return False
    dest.write_bytes(r.content)
    time.sleep(0.2)
    return True


# 1. observations
CPC = "https://www.cpc.ncep.noaa.gov"
for name, url in {
    "oni.ascii.txt": f"{CPC}/data/indices/oni.ascii.txt",
    "ersst5.nino.mth.91-20.ascii": f"{CPC}/data/indices/ersst5.nino.mth.91-20.ascii",
}.items():
    fetch(url, CACHE / name, refresh=True)
    LOG[name] = {"url": url}

# 2. NMME Nino-3.4 (January, February, March starts)
NM = "https://ftp.cpc.ncep.noaa.gov/NMME/ENSO"
MODELS = ["CanCM4i", "CFSv2", "GEM5_NEMO", "GFDL_SPEAR", "NASA_GEOS5v2", "NCAR_CCSM4"]
n_nmme = 0
for mod in MODELS:
    for mm in ("01", "02", "03"):
        index = CLIENT.get(f"{NM}/{mod}/{mm}0100/").text
        names = sorted({s.split('"')[0] for s in index.split('href="')[1:] if s.split('"')[0].endswith(".nc")})
        for fn in names:
            if fetch(f"{NM}/{mod}/{mm}0100/{fn}", CACHE / "nmme" / fn):
                n_nmme += 1
LOG["nmme_enso"] = {"url": f"{NM}/<model>/<MM>0100/", "models": MODELS, "files": n_nmme}

# 3. IRI plume (fig. 4) and objective probability (fig. 3), Jan-Mar issues 2002-2026
IRI = "https://ensoforecast.iri.columbia.edu"
issues = [(a, m) for a in range(2002, 2027) for m in (1, 2, 3)]
n_iri = {"figure4_plot": 0, "figure3_plot": 0}
for fig in n_iri:
    for a, m in issues:
        if fetch(f"{IRI}/{fig}/{a}/{m}", CACHE / "iri" / f"{fig}_{a}_{m:02d}.svg"):
            n_iri[fig] += 1
LOG["iri_svg"] = {"url": f"{IRI}/<figure4_plot|figure3_plot>/<year>/<month>", "downloaded": n_iri,
                  "requested_per_figure": len(issues)}  # fmt: skip

# 4. IRI quick look (official CPC/IRI table), 2012-2026
QL = "https://iri.columbia.edu/our-expertise/climate/forecasts/enso"
n_ql = 0
for a in range(2012, 2027):
    for m in (1, 2, 3):
        if fetch(f"{QL}/{a}-{MONTHS[m - 1]}-quick-look/", CACHE / "iri" / f"quicklook_{a}_{m:02d}.html"):
            n_ql += 1
LOG["iri_quicklook"] = {"url": f"{QL}/<year>-<month>-quick-look/", "downloaded": n_ql}

# 5. Jan-Mar 2026 CPC discussions: the 2026 quick look shows the official table only as an image,
# so the favoured category comes from the synopsis text.
for s in ("jan2026", "feb2026", "mar2026"):
    url = f"{CPC}/products/analysis_monitoring/enso_disc_{s}/ensodisc.shtml"
    fetch(url, CACHE / "cpc" / f"disc_{s}.html")
    LOG[f"cpc_disc_{s}"] = {"url": url}

LOG["_end"] = {"utc": datetime.now(UTC).isoformat(timespec="seconds"), "failures": len(FAILURES)}
LOG["_failures"] = {"list": FAILURES}
(CACHE / "sources.json").write_text(json.dumps(LOG, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: v for k, v in LOG.items() if k != "_failures"}, ensure_ascii=False, indent=1))
print("failures:", len(FAILURES), FAILURES[:10])
