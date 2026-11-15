# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Download the full daily series of the ANA rain gauge 2853015 (HidroWeb legacy web service, no key)
and write it as a small daily CSV in the raw folder (never committed).

    python -I fetch_ana.py <raw_dir>

HidroSerieHistorica, tipoDados=2 (rain). Each record is one month with Chuva01..Chuva31 and a
consistency level (1 = raw, 2 = consisted). When a month comes in both levels, level 2 wins: the
same rule as the gauge input of `fieldshift.complements.rain_signal`.
"""

import calendar
import csv
import json
import sys
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

import httpx

STATION = "2853015"
# same service URL that data/sites/cruz-alta/input/ana-2853015-sep-nov-daily.csv records per row
URL = (
    "https://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica?codEstacao="
    f"{STATION}&dataInicio=&dataFim=&tipoDados=2&nivelConsistencia="
)
HEADERS = {"User-Agent": "fieldshift-analysis/0.1"}


def main() -> None:
    raw = Path(sys.argv[1])
    raw.mkdir(parents=True, exist_ok=True)
    xml_path = raw / f"ana_serie_{STATION}.xml"
    log_path = raw / f"ana_serie_{STATION}.access.json"
    if not (xml_path.exists() and xml_path.stat().st_size > 0 and log_path.exists()):
        r = httpx.get(URL, headers=HEADERS, timeout=600)
        r.raise_for_status()
        xml_path.write_bytes(r.content)
        access = {"url": URL, "accessed_at": datetime.now().astimezone().isoformat(timespec="seconds")}
        log_path.write_text(json.dumps(access, indent=1), encoding="utf-8")
        print("downloaded", xml_path, len(r.content), "bytes")
    else:
        print("cached", xml_path)

    months: dict[tuple[int, int], tuple[int, list[float | None]]] = {}
    for el in ET.fromstring(xml_path.read_bytes()).iter():
        if el.tag.split("}")[-1] != "SerieHistorica":
            continue
        f = {c.tag.split("}")[-1]: (c.text or "").strip() for c in el}
        dt = datetime.strptime(f["DataHora"][:10], "%Y-%m-%d")
        level = int(f.get("NivelConsistencia") or 0)
        nd = calendar.monthrange(dt.year, dt.month)[1]
        vals = [float(f[k]) if f.get(k := f"Chuva{d:02d}", "") != "" else None for d in range(1, nd + 1)]
        key = (dt.year, dt.month)
        if key not in months or level > months[key][0]:
            months[key] = (level, vals)
    if not months:
        raise SystemExit("ANA returned no SerieHistorica records")

    out = raw / f"ana_daily_{STATION}.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "rain_mm", "consistency_level"])
        for (y, m), (level, vals) in sorted(months.items()):
            for d, v in enumerate(vals, 1):
                w.writerow([date(y, m, d).isoformat(), "" if v is None else v, level])
    print("wrote", out, f"({min(months)[0]}-{max(months)[0]}, {len(months)} months)")


if __name__ == "__main__":
    main()
