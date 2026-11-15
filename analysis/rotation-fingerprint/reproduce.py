# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the whole "every field's winter, from space" analysis, in order, from the repository root:

    uv run --project services/science --with numpy==2.3.4 --with rasterio==1.4.3 --with pystac-client==0.9.0 \
        --with planetary-computer==1.0.0 --with matplotlib==3.10.7 python -I analysis/rotation-fingerprint/reproduce.py

Options:
    --raw DIR        raw downloads (default ~/.cache/fieldshift/rotation-fingerprint; never committed)
    --quadrats FILE  reuse the quadrats of another analysis (JSON with quadrant_id, lat, lon), optional

Reads about 640 NASA HLS granules (red, NIR, Fmask windows; about 25 minutes on a fast link, resumable) and one
IBGE SIDRA table. Results go to analysis/rotation-fingerprint/results/.
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script: str, *args) -> None:
    print(f"\n== {script}", flush=True)
    subprocess.run([sys.executable, "-I", str(HERE / script), *map(str, args)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path.home() / ".cache" / "fieldshift" / "rotation-fingerprint")
    ap.add_argument("--quadrats", type=Path, default=None)
    a = ap.parse_args()
    res = HERE / "results"
    started = datetime.now(UTC)
    run("scenes.py", a.raw)
    run("fetch_pam.py", a.raw, res)
    run("classify.py", a.raw, res, *(["--quadrats", a.quadrats] if a.quadrats else []))
    run("figure.py", a.raw, res)
    info = {
        "started_utc": started.isoformat(timespec="seconds"),
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "libraries": {
            p: version(p) for p in ("numpy", "rasterio", "pystac-client", "planetary-computer", "matplotlib", "pillow")
        },
    }
    (res / "run_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
