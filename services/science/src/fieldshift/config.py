# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Paths of the pipeline. `data/` lives at the repository root (architecture, Database Schema)."""

from __future__ import annotations

from pathlib import Path

from fieldshift.contracts.export import find_repo_root

# Time zone used for "today" and for access timestamps (team clock, AGENTS.md §1).
LOCAL_UTC_OFFSET_HOURS = -3


def repo_root() -> Path:
    return find_repo_root(Path(__file__).resolve())


def data_dir() -> Path:
    return repo_root() / "data"
