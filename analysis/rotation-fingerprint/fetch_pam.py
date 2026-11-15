# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""IBGE PAM (SIDRA table 1612): planted area of every winter and summer grain crop of Cruz Alta (RS), 2015-2025.

    python -I fetch_pam.py <raw_dir> <results_dir>

The independent check of the satellite classes. Writes the raw API answer to <raw_dir>/sidra_1612_planted.json
(not committed) and the municipality-year table to <results_dir>/ibge_pam_1612_cruz_alta.csv (committed, with
attribution). PAM counts the crop by harvest year; winter crops of Rio Grande do Sul are sown and harvested in the
same calendar year, so PAM year y matches the satellite winter of year y.
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

MUNICIPALITY = "4306106"  # Cruz Alta (RS)
PRODUCTS = {  # SIDRA 1612 classification 81
    "2716": ("wheat", "winter_grain"),
    "2693": ("oat", "winter_grain"),
    "2699": ("barley", "winter_grain"),
    "2698": ("rye", "winter_grain"),
    "109180": ("triticale", "winter_grain"),
    "83384": ("canola", "winter_grain"),
    "2713": ("soybean", "summer"),
    "2711": ("maize", "summer"),
}
URL = ("https://apisidra.ibge.gov.br/values/t/1612/n6/{m}/v/109/p/2015-2025/c81/" + ",".join(PRODUCTS)).format(
    m=MUNICIPALITY
)


def num(v: str) -> float | None:
    # SIDRA symbols: "-" = zero (absolute), ".." / "..." = not applicable / not available, "X" = suppressed
    if v == "-":
        return 0.0
    try:
        return float(v)
    except ValueError:
        return None


def main() -> None:
    raw, res = Path(sys.argv[1]), Path(sys.argv[2])
    raw.mkdir(parents=True, exist_ok=True)
    res.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(URL, headers={"User-Agent": "fieldshift-analysis"})
    with urllib.request.urlopen(req, timeout=120) as r:
        body = r.read()
    accessed = datetime.now(UTC).isoformat(timespec="seconds")
    (raw / "sidra_1612_planted.json").write_bytes(body)
    rows = json.loads(body)[1:]
    table: dict[int, dict] = {}
    for r in rows:
        y = int(r["D3C"])
        name, _ = PRODUCTS[r["D4C"]]
        table.setdefault(y, {"year": y})[f"{name}_ha"] = num(r["V"])
    cols = ["year"] + [f"{n}_ha" for n, _ in PRODUCTS.values()] + ["winter_grain_ha", "summer_ha"]
    out = res / "ibge_pam_1612_cruz_alta.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        f.write(
            "# IBGE, Producao Agricola Municipal (PAM), SIDRA table 1612, variable 109 planted area (ha), "
            f"municipality {MUNICIPALITY} Cruz Alta (RS). Source: {URL} (accessed {accessed}). "
            "Empty cell = not available in SIDRA ('...'); '-' in SIDRA is written as 0. "
            "winter_grain_ha = wheat + oat + barley + rye + triticale + canola (missing counted as 0).\n"
        )
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for y in sorted(table):
            t = table[y]
            t["winter_grain_ha"] = sum(t.get(f"{n}_ha") or 0 for n, g in PRODUCTS.values() if g == "winter_grain")
            t["summer_ha"] = sum(t.get(f"{n}_ha") or 0 for n, g in PRODUCTS.values() if g == "summer")
            w.writerow({c: ("" if t.get(c) is None else t.get(c)) for c in cols})
    (raw / "sidra_access.json").write_text(json.dumps({"url": URL, "accessed_utc": accessed}), encoding="utf-8")
    print(f"wrote {out} ({len(table)} years)")


if __name__ == "__main__":
    main()
