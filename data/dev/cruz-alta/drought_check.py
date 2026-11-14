# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""DEV ONLY check for issue #26: soybean yield (IBGE PAM) next to season rainfall (NASA POWER).

Reads only committed files in this folder and prints the Markdown tables used in README.md:
    uv run --directory services/science python ../../data/dev/cruz-alta/drought_check.py

Windows (analysis convention for this check, not a project decision): PAM year Y is the harvest
of the season planted in late Y-1, so rainfall is summed over Nov(Y-1)..Mar(Y) and Dec(Y-1)..Feb(Y).
Reference: the 1991-2020 mean of each window from the same POWER series. No causal claim.
"""

from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERIES_ID = "power.precip.monthly_sum"
WINDOWS = {"Nov-Mar": [(-1, 11), (-1, 12), (0, 1), (0, 2), (0, 3)],
           "Dec-Feb": [(-1, 12), (0, 1), (0, 2)]}  # fmt: skip
NORMAL = range(1991, 2021)
RECENT = range(2012, 2026)  # the last 14 PAM harvest years (2012..2025)


def monthly_precip() -> dict[str, float | None]:
    bundle = json.loads((HERE / "output" / "series.json").read_text(encoding="utf-8"))
    series = next(s for s in bundle["series"] if s["id"] == SERIES_ID)
    return {p["t"]: p["v"] for p in series["points"]}


def window_total(precip: dict[str, float | None], year: int, months) -> float | None:
    values = [precip.get(f"{year + dy}-{m:02d}") for dy, m in months]
    return None if any(v is None for v in values) else round(sum(values), 1)


def main() -> None:
    precip = monthly_precip()
    with (HERE / "ibge" / "pam_1612_4306106_2713.csv").open(encoding="utf-8") as fh:
        yields = {int(r["year"]): int(r["yield_kg_ha"]) for r in csv.DictReader(fh)}

    normals = {}
    for name, months in WINDOWS.items():
        totals = [window_total(precip, y, months) for y in NORMAL]
        normals[name] = round(statistics.mean(t for t in totals if t is not None), 1)
    recent = [yields[y] for y in RECENT]
    median = statistics.median(recent)

    print(f"Median soybean yield {RECENT.start}-{RECENT.stop - 1}: {median:g} kg/ha")
    print(f"POWER 1991-2020 mean: Nov-Mar {normals['Nov-Mar']} mm, Dec-Feb {normals['Dec-Feb']} mm")
    print()
    print("| Harvest year (safra) | Yield kg/ha | % of 2012-2025 median | Nov-Mar mm | % of "
          "1991-2020 | Dec-Feb mm | % of 1991-2020 |")  # fmt: skip
    print("|---|---|---|---|---|---|---|")
    for y in RECENT:
        cells = [f"{y} ({y - 1}/{str(y)[2:]})", str(yields[y]), f"{100 * yields[y] / median:.0f}%"]
        for name, months in WINDOWS.items():
            total = window_total(precip, y, months)
            share = "n/a" if total is None else f"{100 * total / normals[name]:.0f}%"
            cells += [str(total), share]
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
