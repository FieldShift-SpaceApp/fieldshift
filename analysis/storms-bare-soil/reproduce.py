# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the whole "storms meet soil" analysis, in order, from the repository root:

    uv run --project services/science --with matplotlib==3.10.7 python -I analysis/storms-bare-soil/reproduce.py

Options:
    --raw DIR   raw downloads (default ~/.cache/fieldshift/storms-bare-soil; never committed)

Only the ANA gauge series is downloaded (about 2 MB). IMERG, POWER and the bare-soil calendar are
read from files already committed in data/. Results go to analysis/storms-bare-soil/results/.
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
    ap.add_argument("--raw", type=Path, default=Path.home() / ".cache" / "fieldshift" / "storms-bare-soil")
    a = ap.parse_args()
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    started = datetime.now(UTC).isoformat(timespec="seconds")

    run("fetch_ana.py", a.raw)
    run("storms.py", a.raw, results)
    run("straw_clock.py", results)
    run("figure.py", results)

    import matplotlib
    import yaml

    info = {
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "versions": {
            "python": platform.python_version(),
            "matplotlib": matplotlib.__version__,
            "pyyaml": yaml.__version__,
        },
    }
    (results / "run_info.json").write_text(json.dumps(info, indent=1), encoding="utf-8", newline="\n")
    print("\nDone. Results in", results)


if __name__ == "__main__":
    main()
