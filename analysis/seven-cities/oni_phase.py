# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Checks the team's ENSO phase table (results/team_enso_phase_oni_jja.csv) against NOAA CPC's ONI file.

Phase of calendar year Y = ONI of the June-July-August season of Y: El Niño >= +0.5, La Niña <= -0.5, neutral otherwise
(simple threshold, not NOAA's five-consecutive-season rule). No account needed.
Run: uv run --no-project --with pandas python oni_phase.py
"""

import os
import urllib.request

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"


def phase(v: float) -> str:
    return "El Niño" if v >= 0.5 else ("La Niña" if v <= -0.5 else "neutral")


def main() -> None:
    req = urllib.request.Request(URL, headers={"User-Agent": "fieldshift-analysis"})
    text = urllib.request.urlopen(req, timeout=60).read().decode()
    oni = {}
    for line in text.splitlines():
        q = line.split()
        if len(q) == 4 and q[0] == "JJA" and q[1].isdigit():
            oni[int(q[1])] = float(q[3])
    team = pd.read_csv(os.path.join(HERE, "results", "team_enso_phase_oni_jja.csv")).set_index("year")
    noaa = pd.DataFrame({"oni_jja_noaa": [oni.get(y) for y in team.index]}, index=team.index)
    noaa["phase_noaa"] = noaa.oni_jja_noaa.map(phase)
    both = team.join(noaa)
    diff = both[(both.phase_jja != both.phase_noaa) | ((both.oni_jja - both.oni_jja_noaa).abs() > 0.005)]
    print(both.to_string())
    print("El Niño years:", both.index[both.phase_noaa == "El Niño"].tolist())
    print("years that differ from the team table:", len(diff))
    if len(diff):
        print(diff.to_string())


if __name__ == "__main__":
    main()
