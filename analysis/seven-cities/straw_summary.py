# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Aggregates the committed straw table (results/team_straw_ndti_seven_cities.csv, from straw_ndti_gee.py) per municipality.

Same aggregation as the team's comparison page (script 54): rows with >= 20 soybean pixels; per month, the yearly difference
NDTI(green winter) - NDTI(low-green winter) among low-NDVI pixels; reported if >= 8 years have both groups.
Output: results/straw_summary_by_city.csv (mean difference, years with a positive difference, years compared).
Run: uv run --no-project --with pandas python straw_summary.py
"""

import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    g = pd.read_csv(os.path.join(HERE, "results", "team_straw_ndti_seven_cities.csv"))
    g = g[g.n_soy_pixels >= 20]
    rows = []
    for city in g.municipality.unique():
        o = {"municipality": city}
        for month in ("oct", "nov", "apr"):
            p = (
                g[(g.municipality == city) & (g.month == month)]
                .pivot(index="winter_year", columns="winter_state", values="ndti_in_low_ndvi_pixels")
                .dropna()
            )
            if len(p) >= 8:
                diff = p["green"] - p["low green"]
                o[f"{month}_ndti_diff_mean"] = round(float(diff.mean()), 3)
                o[f"{month}_years_positive"] = int((diff > 0).sum())
                o[f"{month}_years"] = len(diff)
        rows.append(o)
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(HERE, "results", "straw_summary_by_city.csv"), index=False)
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
