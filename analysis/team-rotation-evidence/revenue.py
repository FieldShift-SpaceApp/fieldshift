# SI-assisted: Claude Code (Anthropic), port of FieldShift team research; review: pending (see SI-USAGE.md)
"""Gross revenue per hectare of a winter-summer system on the same hectare, Cruz Alta, in 2025 reais.

    python -I revenue.py <results_dir>

Reads results/ibge_pam_1612_cruz_alta_value.csv and results/ibge_ipca_1737_annual_mean.csv (fetch_inputs.py).
Revenue of a crop in year y = value of production / harvested area (IBGE PAM), deflated to 2025 reais with the
annual mean of the IPCA index (crop-years with < 200 ha harvested are dropped, as in the team script).
Agricultural year Y = winter of Y-1 + summer of Y:
    soybean + winter fallow = soybean(Y)
    wheat + soybean         = soybean(Y) + wheat(Y-1)
Mean over Y = 2002..2025 (24 years). This is GROSS revenue, not a margin: production costs are not subtracted.
Writes <results_dir>/system_revenue_cruz_alta.csv.
"""

from __future__ import annotations

import csv
import statistics as st
import sys
from pathlib import Path

MIN_AREA_HA = 200
FIRST_YEAR = 2002


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(line for line in f if not line.startswith("#")))


def main() -> None:
    results = Path(sys.argv[1])
    ipca = {
        int(r["year"]): float(r["ipca_index_annual_mean"])
        for r in rows(results / "ibge_ipca_1737_annual_mean.csv")
        if r["months"] == "12"
    }
    base = ipca[2025]
    rev: dict[str, dict[int, float]] = {"soybean": {}, "wheat": {}}
    for r in rows(results / "ibge_pam_1612_cruz_alta_value.csv"):
        try:
            area, value = float(r["harvested_area_ha"]), float(r["value_thousand_brl"])
        except ValueError:
            continue
        y = int(r["year"])
        if area >= MIN_AREA_HA and value and y in ipca:
            rev[r["crop"]][y] = value * 1000 / area * base / ipca[y]
    systems = {
        "soybean + winter fallow": {y: s for y, s in rev["soybean"].items()},
        "wheat + soybean": {y: s + rev["wheat"][y - 1] for y, s in rev["soybean"].items() if y - 1 in rev["wheat"]},
    }
    out = results / "system_revenue_cruz_alta.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        f.write(
            "# FieldShift team research, ported; gross revenue (not margin), 2025 reais (IPCA annual mean), IBGE PAM\n"
        )
        w = csv.writer(f)
        w.writerow(
            [
                "system",
                "years",
                "first_year",
                "last_year",
                "mean_brl_per_ha",
                "cv_pct",
                "worst_brl_per_ha",
                "worst_year",
            ]
        )
        for name, series in systems.items():
            s = {y: v for y, v in series.items() if y >= FIRST_YEAR}
            vals = list(s.values())
            mean = st.mean(vals)
            worst = min(s, key=s.get)
            w.writerow(
                [name, len(s), min(s), max(s), round(mean), round(st.stdev(vals) / mean * 100), round(s[worst]), worst]
            )
            print(f"{name:26s} R$ {mean:,.0f}/ha  ({len(s)} years {min(s)}-{max(s)})")
    print("wrote", out)


if __name__ == "__main__":
    main()
