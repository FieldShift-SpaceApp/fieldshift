# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""IBGE PAM (SIDRA 1612) on a recorded response: parsing, SIDRA symbols, checks, CLI offline.

The fixture is the real response for Cruz Alta (4306106) / soybean (2713) accessed on 2026-11-14,
trimmed to the years 1987, 1988, 2021 and 2022 (planted area is SIDRA "..." in 1987).
"""

import json
import shutil
from pathlib import Path

import httpx
import pytest

from fieldshift.cli import main
from fieldshift.config import data_dir
from fieldshift.errors import LayerError, PipelineError
from fieldshift.sources import ibge_pam

FIXTURE = Path(__file__).parent / "fixtures" / "ibge" / "pam_1612_4306106_2713_trimmed.json"
MUN, SOY = "4306106", "2713"


@pytest.fixture
def wrapped() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_parse_recorded_response(wrapped):
    s = ibge_pam.parse(wrapped, MUN, SOY)
    assert (s.municipality_name, s.product_name) == ("Cruz Alta (RS)", "Soja (em grão)")
    assert [y.year for y in s.years] == [1987, 1988, 2021, 2022]
    rows = s.by_year()
    assert rows[2021] == ibge_pam.PamYear(2021, 91500, 91500, 358650, 3920)
    assert rows[2022] == ibge_pam.PamYear(2022, 92200, 92200, 123240, 1337)
    assert rows[1987].area_planted_ha is None  # SIDRA "..." -> no value, never 0
    assert rows[1987].area_harvested_ha == 90000
    assert s.accessed_at.endswith("-03:00") and s.url == ibge_pam.build_url(MUN, SOY)


def test_sidra_symbols():
    assert ibge_pam._number("-") == 0
    assert [ibge_pam._number(x) for x in ("..", "...", "X")] == [None, None, None]
    with pytest.raises(PipelineError):
        ibge_pam._number("1.5")


def test_parse_rejects_other_municipality_or_product(wrapped):
    with pytest.raises(PipelineError, match="municipality"):
        ibge_pam.parse(wrapped, "4300000", SOY)
    with pytest.raises(PipelineError, match="product"):
        ibge_pam.parse(wrapped, MUN, "2711")


def test_parse_rejects_missing_variable(wrapped):
    wrapped["response"] = [v for v in wrapped["response"] if v["id"] != "112"]
    with pytest.raises(PipelineError, match="112"):
        ibge_pam.parse(wrapped, MUN, SOY)


def test_build_url_validates_codes():
    url = ibge_pam.build_url(MUN)
    assert "/1612/" in url and "N6[4306106]" in url and "81[2713]" in url
    assert "109|216|214|112" in url
    with pytest.raises(PipelineError):
        ibge_pam.build_url("430610")


def test_csv_and_provenance(wrapped):
    s = ibge_pam.parse(wrapped, MUN, SOY)
    lines = ibge_pam.to_csv(s).splitlines()
    assert lines[0] == "year,area_planted_ha,area_harvested_ha,production_t,yield_kg_ha"
    assert lines[1] == "1987,,90000,162000,1800"
    prov = ibge_pam.provenance(s)
    assert prov["temporal"]["period"] == "1987/2022"
    assert prov["access"]["url"] == s.url
    assert any("area_planted_ha: [1987]" in lim for lim in prov["limitations"])


def test_fetch_offline_without_file_fails(tmp_path):
    with pytest.raises(LayerError, match="NOT_EXTRACTED_YET"):
        ibge_pam.fetch(MUN, SOY, cache_dir=tmp_path, offline=True)


def test_fetch_downloads_wraps_and_writes(tmp_path, wrapped):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=wrapped["response"])

    client = httpx.Client(transport=httpx.MockTransport(handler))
    s = ibge_pam.fetch(MUN, SOY, cache_dir=tmp_path, client=client)
    saved = json.loads((tmp_path / f"{ibge_pam.cache_name(MUN, SOY)}.raw.json").read_text("utf-8"))
    assert saved["fieldshift_request"]["url"] == ibge_pam.build_url(MUN, SOY)
    assert s.by_year()[2022].yield_kg_ha == 1337


def test_fetch_http_error_is_reported(tmp_path):
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(500, text="x")))
    with pytest.raises(PipelineError, match="500"):
        ibge_pam.fetch(MUN, SOY, cache_dir=tmp_path, client=client)


def test_cli_offline_writes_csv_and_provenance(tmp_path, capsys):
    cache, out = tmp_path / "cache", tmp_path / "out"
    cache.mkdir()
    shutil.copy(FIXTURE, cache / f"{ibge_pam.cache_name(MUN, SOY)}.raw.json")
    code = main(["fetch", "ibge-pam", "--municipality", MUN, "--cache-dir", str(cache),
                 "--out-dir", str(out), "--offline"])  # fmt: skip
    assert code == 0
    assert "Cruz Alta (RS)" in capsys.readouterr().out
    assert (out / "pam_1612_4306106_2713.csv").read_bytes().count(b"\n") == 5
    assert (cache / "pam_1612_4306106_2713.provenance.json").is_file()
    assert not list(out.glob("*.json"))  # no plain JSON where validate expects contracts


def test_committed_cruz_alta_files_regenerate_from_committed_raw():
    cache = data_dir() / "cache" / "ibge" / "dev-cruz-alta"
    out = data_dir() / "dev" / "dev-cruz-alta" / "ibge"
    stem = ibge_pam.cache_name(MUN, SOY)
    raw = json.loads((cache / f"{stem}.raw.json").read_text(encoding="utf-8"))
    s = ibge_pam.parse(raw, MUN, SOY)
    assert (out / f"{stem}.csv").read_text(encoding="utf-8") == ibge_pam.to_csv(s)
    committed = json.loads((cache / f"{stem}.provenance.json").read_text(encoding="utf-8"))
    assert committed == ibge_pam.provenance(s)


# Regression (Codex review of #30): a value outside the SIDRA format is an error, no coercion
@pytest.mark.parametrize(
    "value", ["1.5", "-3", " 12", "+7", "1_000", "١٢", "", True, 3.7, 12, None]
)
def test_number_rejects_non_sidra_values(value):
    with pytest.raises(PipelineError):
        ibge_pam._number(value)


@pytest.mark.parametrize(("value", "expected"), [("12", 12), ("0", 0), ("-", 0), ("..", None),
                                                 ("...", None), ("X", None)])  # fmt: skip
def test_number_accepts_sidra_formats(value, expected):
    assert ibge_pam._number(value) == expected


def test_harvest_year_note_is_specific_only_to_soybean_in_rs():
    from types import SimpleNamespace

    soy_rs = SimpleNamespace(product_id=ibge_pam.SOYBEAN, municipality_id="4306106")
    soy_mt = SimpleNamespace(product_id=ibge_pam.SOYBEAN, municipality_id="5107925")
    wheat_rs = SimpleNamespace(product_id="2716", municipality_id="4306106")
    assert "soybean in RS" in ibge_pam._harvest_year_note(soy_rs)
    assert "soybean" not in ibge_pam._harvest_year_note(soy_mt)
    assert "soybean" not in ibge_pam._harvest_year_note(wheat_rs)
