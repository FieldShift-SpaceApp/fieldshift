# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Straw clock: how much winter straw is still on the ground when the November storms arrive,
per rotation. Arithmetic from measured half-lives, not a field measurement.

    python -I straw_clock.py <results_dir>

straw(t) = initial * 2 ** (-(t - management) / half_life), with the half-lives measured under
no-till in the Cruz Alta long-term trial (Campos et al. 2011b) and the initial straw ranges and
scenario windows in straw_parameters.json (every number there carries its source).
"""

import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
YEAR = 2025  # a non-leap reference year: only day differences matter
LABEL = "arithmetic from measured half-lives, not a field measurement"


def md(s: str) -> date:
    m, d = s.split("-")
    return date(YEAR, int(m), int(d))


def remaining(initial: float, days: int, half_life: float) -> float:
    return initial * 2 ** (-days / half_life)


def clock(rot: dict, target: date) -> dict:
    lo0, hi0 = rot["initial_t_ha"]["low"], rot["initial_t_ha"]["high"]
    base = {"rotation": rot["id"], "target": target.strftime("%m-%d"), "label": LABEL}
    if rot["window"] is None:
        return base | {
            "status": "no winter straw",
            "share_of_window_not_yet_managed_pct": None,
            "straw_t_ha_low": 0.0,
            "straw_t_ha_high": 0.0,
            "fraction_left_low": None,
            "fraction_left_high": None,
            "days_since_management_min": None,
            "days_since_management_max": None,
        }
    start, end, hl = md(rot["window"]["start"]), md(rot["window"]["end"]), rot["half_life_days"]
    days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    done = [d for d in days if d <= target]
    not_yet = round(100 * (len(days) - len(done)) / len(days), 1)
    if not done:
        return base | {
            "status": "crop still standing (management date after the target for the whole window)",
            "share_of_window_not_yet_managed_pct": not_yet,
            "straw_t_ha_low": None,
            "straw_t_ha_high": None,
            "fraction_left_low": None,
            "fraction_left_high": None,
            "days_since_management_min": None,
            "days_since_management_max": None,
        }
    age_max, age_min = (target - done[0]).days, (target - done[-1]).days
    return base | {
        "status": "managed" if not_yet == 0 else "partly managed (fields managed after the target are excluded)",
        "share_of_window_not_yet_managed_pct": not_yet,
        "straw_t_ha_low": round(remaining(lo0, age_max, hl), 2),
        "straw_t_ha_high": round(remaining(hi0, age_min, hl), 2),
        "fraction_left_low": round(2 ** (-age_max / hl), 3),
        "fraction_left_high": round(2 ** (-age_min / hl), 3),
        "days_since_management_min": age_min,
        "days_since_management_max": age_max,
    }


def main() -> None:
    results = Path(sys.argv[1])
    results.mkdir(parents=True, exist_ok=True)
    params = json.loads((HERE / "straw_parameters.json").read_text(encoding="utf-8"))
    rows = [clock(rot, md(t)) for rot in params["rotations"] for t in params["targets"]]
    with (results / "straw_clock.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    doc = {
        "_si": "SI-assisted: script written with Claude Code (Anthropic); inputs copied from the cited sources.",
        "label": LABEL,
        "model": params["model"],
        "how_to_read": "straw_t_ha_low = lowest initial straw managed at the start of the window (oldest straw); "
        "straw_t_ha_high = highest initial straw managed on the latest date that is still before the target. "
        "Fields whose management date falls after the target are not counted (their crop is still standing).",
        "rotations": params["rotations"],
        "sources": params["sources"],
        "rows": rows,
        "limitations": [
            "The half-lives come from one long-term trial (Cruz Alta, no-till, Campos et al. 2011b); decomposition "
            "changes with rain, temperature and residue placement, so another year or field can differ.",
            "A single exponential is assumed; the trial reports half-lives, and the curve shape between the "
            "measurements is not tested here.",
            "The initial straw values come from other sites (Santa Maria, Coxilha, and Roman 1990 as cited by "
            "Embrapa), not from Cruz Alta fields.",
            "No source here converts straw (t/ha) into the share of soil covered, so how much straw is "
            "enough is not given.",
            "The management windows are scenarios from the team brief, not observed dates.",
        ],
    }
    (results / "straw_clock.json").write_text(
        json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n"
    )
    for r in rows:
        print(r["rotation"], r["target"], r["straw_t_ha_low"], r["straw_t_ha_high"], r["status"])


if __name__ == "__main__":
    main()
