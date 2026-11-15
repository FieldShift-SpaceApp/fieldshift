# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Per-granule 30 m NDVI of every Cruz Alta cropland pixel, NASA HLS v2.0 (L30 + S30), summers December - March.

    python -I scenes_summer.py <raw_dir> <fingerprint_raw_dir>

Reuses, unchanged, the reader of analysis/rotation-fingerprint/scenes.py (same tile T22JBP, same 30 m grid, same
WorldCover cropland mask, same Fmask rule, same output format) and only changes the dates: 1 December - 31 March of
the summers 2020/21 to 2025/26. October and November are already in the fingerprint raw directory (April - November).
The cropland index (grid.npz) is copied from the fingerprint raw directory: both sets of vectors share one pixel order.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rotation-fingerprint"))
import scenes  # noqa: E402  (analysis/rotation-fingerprint/scenes.py)

# (years, (start MM-DD, end MM-DD)): December of 2020-2025 and January-March of 2021-2026
WINDOWS = [(range(2020, 2026), ("12-01", "12-31")), (range(2021, 2027), ("01-01", "03-31"))]


def main() -> None:
    raw, fp_raw = Path(sys.argv[1]), Path(sys.argv[2])
    raw.mkdir(parents=True, exist_ok=True)
    if not (raw / "grid.npz").exists():
        shutil.copyfile(fp_raw / "grid.npz", raw / "grid.npz")
    for years, season in WINDOWS:
        scenes.YEARS, scenes.SEASON = years, season
        sys.argv = [sys.argv[0], str(raw)]
        scenes.main()


if __name__ == "__main__":
    main()
