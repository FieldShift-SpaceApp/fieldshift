# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""The per-municipality scene footprints (no network): Cruz Alta keeps the footprints of its published run."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import common  # noqa: E402


def _landsat(path, row):
    return SimpleNamespace(
        collection_id="landsat-c2-l2", id="x", properties={"landsat:wrs_path": path, "landsat:wrs_row": row}
    )


def _hls(tile):
    return SimpleNamespace(collection_id="hls2-s30", id=f"HLS.S30.{tile}.2026300T133841.v2.0", properties={})


def test_cruz_alta_footprints_are_the_published_ones():
    ar = common.area("4306106")
    assert ar["landsat_path_rows"] == {("223", "080"), ("222", "080")}
    assert ar["hls_tiles"] == {"T22JBP", "T22JBN"}
    assert ar["winter_tile"] == "T22JBP"
    assert common.LANDSAT_PATH_ROWS == ar["landsat_path_rows"] and common.HLS_TILES == ar["hls_tiles"]


def test_item_keep_follows_the_municipality():
    assert common.item_keep(_landsat("223", "080"))  # default: Cruz Alta
    assert not common.item_keep(_landsat("222", "081"))
    assert common.item_keep(_hls("T22JBN"), "4311205")
    assert not common.item_keep(_hls("T21JYH"), "4311205")
    assert common.area("4311205")["winter_tile"] == "T22JBN"


def test_unknown_municipality_stops_instead_of_reading_cruz_alta_scenes():
    with pytest.raises(SystemExit):
        common.area("4310207")
