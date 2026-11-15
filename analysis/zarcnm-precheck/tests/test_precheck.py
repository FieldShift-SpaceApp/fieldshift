# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""The pre-check output keeps the format the app reads and never claims a final NM."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import precheck  # noqa: E402

COMMITTED = Path(__file__).resolve().parents[1] / "results" / "precheck.json"


def test_build_matches_committed_file_except_timestamp():
    built = precheck.build()
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    built.pop("generated_at")
    committed.pop("generated_at")
    assert built == committed


def test_format_for_the_app():
    data = precheck.build()
    assert data["site"] == "cruz-alta"
    assert set(data["norm"]) >= {"in", "portaria", "subsidy", "subsidy_pct", "subsidy_budget_note"}
    assert data["norm"]["subsidy_pct"] == {"NM1": 20, "NM2": 30, "NM3": 35, "NM4": 40}
    assert [p["id"] for p in data["paths"]] == ["soy-wheat", "soy-cover", "soy-fallow"]
    for p in data["paths"]:
        assert set(p) >= {"id", "indicators", "nm_range", "locks", "subsidy_pct_range", "notes"}
        assert set(p["nm_range"]) == {"min", "max", "condition"}
        assert p["nm_range"]["min"] <= p["nm_range"]["max"]
        codes = [i["code"] for i in p["indicators"]]
        assert codes == ["V%", "Ca", "m%", "T", "C", "D"]
        for i in p["indicators"]:
            assert set(i) >= {"code", "name", "level_min", "level_max", "observable", "basis", "source"}
            if i["code"] in ("V%", "Ca", "m%"):
                assert i["observable"] is False and i["level_min"] is None
                assert "not observable from satellite: needs soil test" in i["basis"]
            else:
                assert i["observable"] is True and 1 <= i["level_min"] <= i["level_max"] <= 4
        assert p["summary"].startswith("pre-check: 3 of 6 indicators observable; NM range ")
        assert p["summary"].endswith("contour to confirm")
        assert p["subsidy_brl_per_ha"] is None


def test_expected_ranges_and_ordering():
    paths = {p["id"]: p for p in precheck.build()["paths"]}
    assert (paths["soy-wheat"]["nm_range"]["min"], paths["soy-wheat"]["nm_range"]["max"]) == (2, 3)
    assert (paths["soy-cover"]["nm_range"]["min"], paths["soy-cover"]["nm_range"]["max"]) == (3, 4)
    assert (paths["soy-fallow"]["nm_range"]["min"], paths["soy-fallow"]["nm_range"]["max"]) == (1, 2)
    assert paths["soy-cover"]["subsidy_pct_range"] == {"min": 35, "max": 40}
    d = {k: next(i for i in v["indicators"] if i["code"] == "D") for k, v in paths.items()}
    assert (d["soy-wheat"]["level_min"], d["soy-cover"]["level_min"], d["soy-fallow"]["level_min"]) == (2, 3, 1)
    # soil tests at level 1 put every path at NM1 (three indicators at level 1, item 3.2.1-IV-a)
    assert all(p["nm_range_by_soil_level"]["1"] == {"min": 1, "max": 1} for p in paths.values())


def test_cover_conversion_is_monotonic_and_bounded():
    assert precheck.cover_pct(0, precheck.AM_HIGH) == 0
    assert precheck.cover_pct(2.0, precheck.AM_LOW) < precheck.cover_pct(2.0, precheck.AM_HIGH) < 100
