# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""NOAA CPC Oceanic Niño Index (ONI): the raw file as published, and two phase rules.

- `threshold_phase`: one season on its own, El Niño if ONI >= +0.5, La Niña if <= -0.5 (used for
  the JJA winters, same rule as the team's wheat analysis).
- `operational_phases`: NOAA CPC operational definition, the threshold met for at least five
  consecutive overlapping seasons (used for the rain signal, same rule as the team's analysis).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from fieldshift.errors import PipelineError

SEASONS = ("DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ")
THRESHOLD = 0.5
MIN_RUN = 5
ONI_FILE = "oni.ascii.txt"
ONI_SOURCE = "oni.source.json"


@dataclass(frozen=True)
class OniFile:
    values: dict[tuple[str, int], float]  # (season, year) -> anomaly, degC
    url: str
    accessed_at: str
    sha256: str


def load_oni(cache_dir: Path) -> OniFile:
    """data/cache/noaa/oni.ascii.txt + oni.source.json (URL, access time, sha256 checked)."""
    raw_path, meta_path = cache_dir / ONI_FILE, cache_dir / ONI_SOURCE
    if not raw_path.is_file() or not meta_path.is_file():
        raise PipelineError(f"ONI file missing: {raw_path} and {meta_path} are both required")
    raw = raw_path.read_bytes()
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    digest = hashlib.sha256(raw).hexdigest()
    if digest != meta["sha256"]:
        raise PipelineError(f"{raw_path}: sha256 {digest} != {meta['sha256']} in {ONI_SOURCE}")
    values: dict[tuple[str, int], float] = {}
    for line in raw.decode("ascii").splitlines()[1:]:
        parts = line.split()
        if len(parts) == 4 and parts[0] in SEASONS:
            values[(parts[0], int(parts[1]))] = float(parts[3])
    return OniFile(values=values, url=meta["url"], accessed_at=meta["accessed_at"], sha256=digest)


def threshold_phase(value: float) -> str:
    if value >= THRESHOLD:
        return "el_nino"
    if value <= -THRESHOLD:
        return "la_nina"
    return "neutral"


def operational_phases(oni: OniFile) -> dict[tuple[str, int], str]:
    keys = sorted(oni.values, key=lambda k: (k[1], SEASONS.index(k[0])))
    signs = []
    for k in keys:
        v = oni.values[k]
        signs.append(1 if v >= THRESHOLD else -1 if v <= -THRESHOLD else 0)
    phase = [0] * len(keys)
    i = 0
    while i < len(keys):
        j = i
        while j < len(keys) and signs[j] == signs[i] and signs[i] != 0:
            j += 1
        if j - i >= MIN_RUN:
            phase[i:j] = [signs[i]] * (j - i)
        i = max(j, i + 1)
    names = {1: "el_nino", -1: "la_nina", 0: "neutral"}
    return {k: names[p] for k, p in zip(keys, phase, strict=True)}
