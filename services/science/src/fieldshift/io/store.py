# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Stable, atomic JSON writing of validated contracts (architecture, Data Access Layer)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic import BaseModel


def dumps_stable(payload: Any) -> str:
    """Sorted keys and fixed indentation: the same data always gives the same bytes."""
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1) + "\n"


def write_json_atomic(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    return path


def write_model(model: BaseModel, path: Path) -> Path:
    """Write a contract. The model is validated when built, so nothing invalid is written."""
    return write_json_atomic(path, dumps_stable(model.model_dump(mode="json")))
