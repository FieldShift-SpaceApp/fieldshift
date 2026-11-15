# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the whole "straw, not bare soil" analysis, in order, from the repository root:

    uv run --project services/science --with numpy==2.3.4 --with rasterio==1.4.3 --with pystac-client==0.9.0 \
      --with planetary-computer==1.0.0 --with matplotlib==3.10.7 python -I analysis/residue-landsat/reproduce.py

Options:
    --raw DIR   raw downloads and per-scene histograms (default ~/.cache/fieldshift/residue-landsat; never committed)

Reads about 930 Landsat / HLS scenes through the Microsoft Planetary Computer (anonymous token, no account;
small windows at about 60 m, resumable: re-running skips scenes already read). Results go to
analysis/residue-landsat/results/.
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script: str, *args: Path) -> None:
    print(f"\n== {script}", flush=True)
    subprocess.run([sys.executable, "-I", str(HERE / script), *map(str, args)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path.home() / ".cache" / "fieldshift" / "residue-landsat")
    a = ap.parse_args()
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    started = datetime.now(UTC).isoformat(timespec="seconds")

    run("scenes.py", a.raw)
    run("fetch_context.py", a.raw)
    run("series.py", a.raw, results)
    run("figure.py", results)
    run("map.py", results)
    run("zarcnm.py", a.raw, results)

    import matplotlib
    import numpy
    import planetary_computer
    import pystac_client
    import rasterio

    info = {
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "versions": {
            "python": platform.python_version(),
            "numpy": numpy.__version__,
            "rasterio": rasterio.__version__,
            "gdal": rasterio.__gdal_version__,
            "pystac_client": pystac_client.__version__,
            "planetary_computer": getattr(planetary_computer, "__version__", "unknown"),
            "matplotlib": matplotlib.__version__,
        },
    }
    (results / "run_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8", newline="\n")
    print("\nDone. Results in", results)


if __name__ == "__main__":
    main()
