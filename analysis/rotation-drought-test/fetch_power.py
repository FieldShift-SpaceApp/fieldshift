# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""December-February rainfall at Cruz Alta from NASA POWER (daily point API), summers 2000/01 to 2025/26.

    python -I fetch_power.py <raw_dir> <results_dir>

Asks POWER for PRECTOTCORR (MERRA-2 precipitation bias-corrected to gauge/satellite products; IMERG_PRECTOT was
all -999 for this point when this was written) at the point used by the team's other analyses (-28.703, -53.563),
sums December-February per summer and ranks the summers. Used only to confirm, not to choose, the pre-registered
drought summers. Writes <results_dir>/power_rain_dec_feb.csv (URL and access time in the header). The raw JSON
stays in <raw_dir>.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

LAT, LON = -28.703, -53.563
PARAMS = ("PRECTOTCORR",)  # IMERG_PRECTOT came back all -999 for this point on 15 Nov 2026
URL = (
    "https://power.larc.nasa.gov/api/temporal/daily/point?parameters={p}&community=AG"
    f"&latitude={LAT}&longitude={LON}&start=20001201&end=20260331&format=JSON"
)


def main() -> None:
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    series, urls = {}, {}
    accessed = datetime.now(UTC).isoformat(timespec="seconds")
    for p in PARAMS:
        url = URL.format(p=p)
        path = raw / f"power_{p}.json"
        if not path.exists():
            with urllib.request.urlopen(url, timeout=180) as r:
                path.write_bytes(r.read())
        d = json.loads(path.read_text(encoding="utf-8"))["properties"]["parameter"][p]
        series[p], urls[p] = d, url
    rows = []
    for y in range(2000, 2026):  # summer y/y+1 = Dec y + Jan-Feb y+1
        row = {"summer": f"{y}/{str(y + 1)[2:]}"}
        for p, d in series.items():
            vals = [v for k, v in d.items() if (k[:6] == f"{y}12" or k[:6] in (f"{y + 1}01", f"{y + 1}02"))]
            ok = [v for v in vals if v is not None and v >= 0]
            row[p] = round(sum(ok), 1) if len(ok) >= 85 else None
        rows.append(row)
    for p in PARAMS:
        vals = sorted(r[p] for r in rows if r[p] is not None)
        for r in rows:
            r[f"rank_{p}"] = vals.index(r[p]) + 1 if r[p] is not None else None  # 1 = driest
    head = [f"# NASA POWER daily point {LAT}, {LON}; accessed {accessed} UTC"]
    head += [f"# {p}: {u}" for p, u in urls.items()]
    head.append("# December-February totals in mm; rank 1 = driest of the summers with data")
    cols = ["summer", *PARAMS, *(f"rank_{p}" for p in PARAMS)]
    lines = [",".join(cols)] + [",".join("" if r[c] is None else str(r[c]) for c in cols) for r in rows]
    (out / "power_rain_dec_feb.csv").write_text("\n".join(head + lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-8:]))


if __name__ == "__main__":
    main()
