# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the whole ENSO x wheat analysis from the public sources, in order.

    uv run --with httpx==0.28.1 --with numpy==2.5.4 python -I analysis/enso-wheat/reproduce.py

Options:
    --raw DIR          raw downloads (default ~/.cache/fieldshift/enso-wheat; never committed)
    --forecasts        also run the forecast-skill part (needs: --with xarray --with netCDF4;
                       downloads ~700 small files one at a time, several minutes)

Committed outputs go to analysis/enso-wheat/results/. The Atlas output, whose license is not
declared, goes to <raw>/derived/ only.
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def run(script: Path, *args: Path) -> None:
    print(f"\n== {script.relative_to(HERE)}", flush=True)
    subprocess.run([sys.executable, "-I", str(script), *map(str, args)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path.home() / ".cache" / "fieldshift" / "enso-wheat")
    ap.add_argument("--forecasts", action="store_true")
    a = ap.parse_args()
    raw, results = a.raw, HERE / "results"
    results.mkdir(exist_ok=True)
    started = datetime.now(UTC).isoformat(timespec="seconds")

    run(HERE / "fetch_sources.py", raw)
    run(HERE / "wheat_soy_enso.py", raw, results)
    run(HERE / "credit_sicor.py", raw, results)
    run(HERE / "disaster_atlas.py", raw, raw / "derived")
    run(HERE / "cpc_alerts_2023.py", results)
    if a.forecasts:
        run(HERE / "forecast_skill" / "fetch_forecasts.py", raw / "forecasts")
        run(HERE / "forecast_skill" / "forecast_skill.py", raw / "forecasts", results)

    import numpy  # only to record the version used

    versions = {"python": platform.python_version(), "numpy": numpy.__version__}
    for mod in ("httpx", "xarray", "netCDF4"):
        try:
            versions[mod] = __import__(mod).__version__
        except ImportError:
            pass
    info = {
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "forecast_skill_included": a.forecasts,
        "versions": versions,
    }
    (results / "run_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print("\nDone. Results in", results)


if __name__ == "__main__":
    main()
