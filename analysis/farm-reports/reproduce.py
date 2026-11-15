# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the whole farm-report pipeline for one municipality and time each step.

    python -I reproduce.py [--ibge 4306106] [--name "Cruz Alta (RS)"] [--raw DIR] [--results DIR]

Steps: fetch_car.py -> grids.py -> scenes.py now / series / winter -> winter.py -> report.py.
Every step is resumable (scenes already read are skipped). Raw files go to ~/.cache/fieldshift/farm-reports/<ibge>
(or --raw), never to git. Step times are written to <raw>/timing.json and copied into the results JSON.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ibge", default="4306106")
    ap.add_argument("--name", default="Cruz Alta (RS)")
    ap.add_argument("--raw", default=None)
    ap.add_argument("--results", default=None)
    a = ap.parse_args()
    common = ["--ibge", a.ibge] + (["--raw", a.raw] if a.raw else [])
    steps = [
        ("fetch_car", ["fetch_car.py", *common]),
        ("grids", ["grids.py", *common]),
        ("scenes_now", ["scenes.py", "now", *common]),
        ("scenes_series", ["scenes.py", "series", *common]),
        ("scenes_winter", ["scenes.py", "winter", *common]),
        ("winter", ["winter.py", *common]),
        ("report", ["report.py", *common, "--name", a.name] + (["--results", a.results] if a.results else [])),
    ]
    timing = {}
    for name, cmd in steps:
        t0 = time.time()
        subprocess.run([sys.executable, "-I", str(HERE / cmd[0]), *cmd[1:]], check=True)
        timing[name] = round(time.time() - t0, 1)
        print(f"[{name}] {timing[name]} s", flush=True)
    raw = Path(a.raw) if a.raw else Path.home() / ".cache" / "fieldshift" / "farm-reports" / a.ibge
    (raw / "timing.json").write_text(json.dumps(timing, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps(timing, indent=1))


if __name__ == "__main__":
    main()
