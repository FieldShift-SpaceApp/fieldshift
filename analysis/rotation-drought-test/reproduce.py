# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the rotation x drought test: fingerprint classes (if missing), summer HLS scenes, POWER rain, models, figure.

    python -I analysis/rotation-drought-test/reproduce.py [--raw DIR] [--fingerprint-raw DIR]

Defaults: ~/.cache/fieldshift/rotation-drought-test and ~/.cache/fieldshift/rotation-fingerprint (never committed).
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FP = HERE.parent / "rotation-fingerprint"
CACHE = Path.home() / ".cache" / "fieldshift"


def step(script: Path, *args: str) -> None:
    print(f"== {script.name} {' '.join(args)}", flush=True)
    subprocess.run([sys.executable, "-I", str(script), *args], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=CACHE / "rotation-drought-test")
    ap.add_argument("--fingerprint-raw", type=Path, default=CACHE / "rotation-fingerprint")
    a = ap.parse_args()
    res = HERE / "results"
    if not (a.fingerprint_raw / "classes.npz").exists():
        subprocess.run([sys.executable, "-I", str(FP / "reproduce.py"), "--raw", str(a.fingerprint_raw)], check=True)
    step(HERE / "scenes_summer.py", str(a.raw), str(a.fingerprint_raw))
    step(HERE / "fetch_power.py", str(a.raw / "power"), str(res))
    step(HERE / "analyze.py", str(a.raw), str(a.fingerprint_raw), str(res))
    step(HERE / "figure.py", str(res))


if __name__ == "__main__":
    main()
