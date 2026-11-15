# SI-assisted: Claude Code (Anthropic), port of FieldShift team research; review: pending (see SI-USAGE.md)
"""Share of the heavy rain (days >= 25 mm) that falls on soil with no living plant, per winter sequence, Cruz Alta.

    python -I exposure.py <daily_rain_csv> <results_dir>

<daily_rain_csv> has the columns `date` (YYYY-MM-DD) and `rain_mm` (daily GPM IMERG V07 at Cruz Alta; written by
fetch_inputs.py). For each agricultural year Y (1 April of Y-1 to 31 March of Y, Y = 2001..2025) a crop calendar
gives, day by day, the fraction of the ground under a living plant (`alive`, 0..1). The index is

    sum(rain * [rain >= limit] * (1 - alive)) / sum(rain * [rain >= limit])     over all years, in %.

It is a relative exposure index, not a soil-loss estimate: straw is counted as "no living plant", and the sowing
dates and stage lengths below are assumptions of the team's research, to be validated by an agronomist.
Writes <results_dir>/heavy_rain_on_soil_without_live_plants.csv.
"""

from __future__ import annotations

import csv
import datetime as dt
import sys
from pathlib import Path

# (days vegetative, days critical, days maturation) per crop; only the stage lengths matter for `alive`.
CROPS = {
    "soybean": (45, 55, 30),
    "soybean_late": (40, 50, 30),
    "maize": (60, 45, 35),
    "wheat": (60, 45, 35),
    "canola": (55, 55, 40),
    "oat_cover": (40, 60, 20),
    "autumn_cover": (30, 30, 0),
}
# Sequences: (crop, sowing month, sowing day) inside the agricultural year April(Y-1) -> March(Y).  [assumptions]
SEQUENCES = {
    "winter fallow + soybean (sown 1 Nov)": [("soybean", 11, 1)],
    "wheat (15 Jun) + soybean (20 Nov)": [("wheat", 6, 15), ("soybean_late", 11, 20)],
    "autumn cover (10 Apr) + wheat + soybean (20 Nov)": [
        ("autumn_cover", 4, 10),
        ("wheat", 6, 15),
        ("soybean_late", 11, 20),
    ],
    "black oat cover (1 May) + soybean (1 Nov)": [("oat_cover", 5, 1), ("soybean", 11, 1)],
    "canola (1 May) + soybean (5 Nov)": [("canola", 5, 1), ("soybean", 11, 5)],
    "black oat cover (1 May) + early maize (1 Sep)": [("oat_cover", 5, 1), ("maize", 9, 1)],
    "winter fallow + early maize (1 Sep)": [("maize", 9, 1)],
}
LIMITS = (20, 25, 50)
YEARS = range(2001, 2026)


def alive_fraction(sequence: list[tuple[str, int, int]], year: int) -> list[float]:
    """Fraction of the ground under a living plant on each day of the agricultural year (1 Apr Y-1 .. 31 Mar Y)."""
    start = dt.date(year - 1, 4, 1)
    n_days = (dt.date(year, 3, 31) - start).days + 1
    alive = [0.0] * n_days
    for crop, month, day in sequence:
        n1, n2, n3 = CROPS[crop]
        sow = (dt.date(year - 1, month, day) - start).days
        for i in range(sow, min(n_days, sow + n1 + n2 + n3)):
            t = i - sow
            alive[i] = min(1.0, t / (n1 * 0.8)) if t < n1 else 1.0
    return alive


def read_rain(path: Path) -> dict[dt.date, float | None]:
    rain: dict[dt.date, float | None] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(line for line in f if not line.startswith("#")):
            v = row["rain_mm"].strip()
            rain[dt.date.fromisoformat(row["date"])] = float(v) if v else None
    return rain


def exposure(rain: dict[dt.date, float | None], sequence: list[tuple[str, int, int]]) -> dict[str, float]:
    tot = {lim: 0.0 for lim in LIMITS}
    bare = {lim: 0.0 for lim in LIMITS}
    days_without_plant = []
    used = 0
    for year in YEARS:
        start = dt.date(year - 1, 4, 1)
        alive = alive_fraction(sequence, year)
        values = [rain.get(start + dt.timedelta(i)) for i in range(len(alive))]
        if sum(v is None for v in values) / len(values) > 0.1:
            continue  # same rule as the team script: skip a year with more than 10% missing days
        used += 1
        days_without_plant.append(sum(a < 0.5 for a in alive))
        for v, a in zip(values, alive, strict=True):
            p = v or 0.0
            for lim in LIMITS:
                if p >= lim:
                    tot[lim] += p
                    bare[lim] += p * (1 - a)
    out: dict[str, float] = {"years": used, "days_without_live_plant": round(sum(days_without_plant) / used)}
    out["mm_per_year_25mm_on_soil_without_live_plant"] = round(bare[25] / used)
    for lim in LIMITS:
        out[f"pct_rain_ge{lim}mm_without_live_plant"] = round(100 * bare[lim] / tot[lim])
    return out


def main() -> None:
    rain = read_rain(Path(sys.argv[1]))
    results = Path(sys.argv[2])
    results.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, seq in SEQUENCES.items():
        r = exposure(rain, seq)
        rows.append({"sequence": name, **r})
        print(f"{name:52s} {r['pct_rain_ge25mm_without_live_plant']:3.0f}%  (years {r['years']})")
    out = results / "heavy_rain_on_soil_without_live_plants.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        f.write(
            f"# FieldShift team research, ported; daily rain: {Path(sys.argv[1]).name}; "
            "years 2001-2025 tried, > 10% missing skipped\n"
        )
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("wrote", out)


if __name__ == "__main__":
    main()
