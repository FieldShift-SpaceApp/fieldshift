# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Step 4. Atlas Digital de Desastres no Brasil (MIDR/SEDEC) x ENSO, 18 municipalities.

Usage: python -I disaster_atlas.py <raw_dir> <out_dir>
Reads atlas.csv (BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv, ';'-separated, latin-1),
municipalities_rs.json, oni.ascii.txt and sidra_1612_v112.json (to know whether the municipality
existed in a year).

Method:
- unit: municipality-year; counts if there was >= 1 record of "Estiagem e Seca" (drought and dry
  spell) in the window;
- soybean window: Nov of Y-1 to Apr of Y, phase from the ONI JJA of Y-1;
- wheat window: Jun to Nov of year A, phase from the ONI JJA of A.
Date used: Data_Evento (event date), Data_Registro (record date) when empty.

The Atlas download page declares no license, so this output is NOT committed: reproduce.py writes
it to the raw folder and the README quotes the counts.
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

DROUGHT = "Estiagem e Seca"  # Atlas typology label (drought and dry spell)


def phase(x):
    return "el_nino" if x >= 0.5 else ("la_nina" if x <= -0.5 else "neutral")


def main() -> None:
    raw_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    munis = json.loads((raw_dir / "municipalities_rs.json").read_text(encoding="utf-8"))
    codes = {str(m["code"]): m["name"] for m in munis}
    oni = {}
    for ln in (raw_dir / "oni.ascii.txt").read_text(encoding="utf-8").splitlines()[1:]:
        p = ln.split()
        if len(p) == 4 and p[0] == "JJA":
            oni[int(p[1])] = float(p[3])
    # a municipality "exists" in a year if SIDRA has a numeric yield for it
    sidra = json.loads((raw_dir / "sidra_1612_v112.json").read_text(encoding="utf-8"))[1:]
    exists = set()
    for r in sidra:
        try:
            if float(r["V"]) > 0:
                exists.add((r["D1C"], int(r["D3C"])))
        except ValueError:
            pass

    events = []  # (code, date, typology, status, protocol)
    types = Counter()
    with (raw_dir / "atlas.csv").open(encoding="latin-1", newline="") as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            code = r["Cod_IBGE_Mun"].strip()
            if code not in codes:
                continue
            txt = (r["Data_Evento"] or r["Data_Registro"]).strip()
            d, m, y = txt.split("/")
            events.append(
                (
                    code,
                    date(int(y), int(m), int(d)),
                    r["descricao_tipologia"].strip(),
                    r["Status"].strip(),
                    r["Protocolo_S2iD"].strip(),
                )
            )
            types[r["descricao_tipologia"].strip()] += 1
    drought = [e for e in events if e[2] == DROUGHT]

    def table(window, years, only_existing):
        g = defaultdict(lambda: [0, 0])
        by_year = defaultdict(lambda: [0, 0])
        for year in years:
            start, end, phase_year = window(year)
            if phase_year not in oni:
                continue
            f = phase(oni[phase_year])
            for code in codes:
                if only_existing and (code, year) not in exists:
                    continue
                hit = any(e[0] == code and start <= e[1] <= end for e in drought)
                g[f][0] += 1
                g[f][1] += hit
                by_year[(f, phase_year)][0] += 1
                by_year[(f, phase_year)][1] += hit
        out = {}
        for f in ("el_nino", "neutral", "la_nina"):
            n, h = g[f]
            out[f] = {
                "municipality_years": n,
                "with_record": h,
                "pct": round(100 * h / n, 1) if n else None,
                "by_phase_year": [
                    {"jja_year": a, "n": v[0], "with_record": v[1]} for (ff, a), v in sorted(by_year.items()) if ff == f
                ],
            }
        return out

    def soy(y):
        return date(y - 1, 11, 1), date(y, 4, 30), y - 1

    def wheat(a):
        return date(a, 6, 1), date(a, 11, 30), a

    res = {
        "records_18_municipalities": len(events),
        "by_typology": dict(types.most_common()),
        "period": [min(e[1] for e in events).isoformat(), max(e[1] for e in events).isoformat()],
        "drought_records": len(drought),
        "soy_1992_2025_existing": table(soy, range(1992, 2026), True),
        "soy_1992_2025_all_18": table(soy, range(1992, 2026), False),
        "soy_1991_2025_existing": table(soy, range(1991, 2026), True),
        "wheat_1991_2025_existing": table(wheat, range(1991, 2026), True),
    }
    # sensitivity: soybean window without the 2022 winter (La Nina 2022 -> 2022/23 summer)
    s = res["soy_1992_2025_all_18"]["la_nina"]
    no22 = [x for x in s["by_phase_year"] if x["jja_year"] != 2022]
    res["soy_all_18_la_nina_without_2022"] = {
        "municipality_years": sum(x["n"] for x in no22),
        "with_record": sum(x["with_record"] for x in no22),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "disaster_atlas.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(res["records_18_municipalities"], res["period"], res["drought_records"])
    for k in ("soy_1992_2025_existing", "soy_1992_2025_all_18", "soy_1991_2025_existing", "wheat_1991_2025_existing"):
        t = res[k]
        print(k, {f: (t[f]["with_record"], t[f]["municipality_years"], t[f]["pct"]) for f in t})
        for f in ("el_nino", "la_nina"):
            print("  ", f, [(x["jja_year"], x["with_record"], x["n"]) for x in t[f]["by_phase_year"]])
    print("soy all 18, La Nina without 2022:", res["soy_all_18_la_nina_without_2022"])


if __name__ == "__main__":
    main()
