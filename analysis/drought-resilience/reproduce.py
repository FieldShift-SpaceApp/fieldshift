# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the whole drought-resilience test, in order, from the repository root:

    uv run --project services/science --with matplotlib==3.10.7 python -I analysis/drought-resilience/reproduce.py

Options:
    --raw DIR   raw downloads (default ~/.cache/fieldshift/drought-resilience; never committed)

Downloads IBGE PAM (SIDRA 1612), NASA POWER daily for 18 points (about 18 x 1 MB) and the ANA gauge
2853015 (about 2 MB). Results go to analysis/drought-resilience/results/.
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
    ap.add_argument("--raw", type=Path, default=Path.home() / ".cache" / "fieldshift" / "drought-resilience")
    a = ap.parse_args()
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    started = datetime.now(UTC).isoformat(timespec="seconds")

    run("fetch_sources.py", a.raw, results)
    run("resilience.py", results)
    run("figure.py", results)

    import httpx
    import matplotlib
    import numpy

    info = {
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "versions": {
            "python": platform.python_version(),
            "numpy": numpy.__version__,
            "matplotlib": matplotlib.__version__,
            "httpx": httpx.__version__,
        },
    }
    (results / "run_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8", newline="\n")
    print("\nDone. Results in", results)


if __name__ == "__main__":
    main()
