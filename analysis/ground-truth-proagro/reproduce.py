# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Run the whole ground-truth test (Proagro excess-rain wheat claims x NASA GPM IMERG) from the public sources.

    uv run --with httpx==0.28.1 --with numpy==2.5.4 --with matplotlib==3.10.7 \
        python -I analysis/ground-truth-proagro/reproduce.py

Options:
    --raw DIR   raw downloads (default ~/.cache/fieldshift/ground-truth-proagro; ~130 MB; never committed)

Committed outputs go to analysis/ground-truth-proagro/results/.
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def run(script: Path, *args: Path) -> None:
    print(f"\n== {script.name}", flush=True)
    subprocess.run([sys.executable, "-I", str(script), *map(str, args)], check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path.home() / ".cache" / "fieldshift" / "ground-truth-proagro")
    a = ap.parse_args()
    results = HERE / "results"
    results.mkdir(exist_ok=True)
    started = datetime.now(UTC).isoformat(timespec="seconds")

    run(HERE / "fetch_sources.py", a.raw, results)
    run(HERE / "ground_truth.py", results, REPO / "data" / "sites" / "cruz-alta" / "output" / "enso-rain-signal.json")
    run(HERE / "figure.py", results)

    versions = {"python": platform.python_version()}
    for mod in ("httpx", "numpy", "matplotlib"):
        versions[mod] = __import__(mod).__version__
    info = {
        "started_utc": started,
        "finished_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "versions": versions,
    }
    (results / "run_info.json").write_text(json.dumps(info, indent=1) + "\n", encoding="utf-8")
    print("\nDone. Results in", results)


if __name__ == "__main__":
    main()
