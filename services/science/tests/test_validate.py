# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""`fieldshift validate --all` (ADR-8 layer 1): passes on good data, fails on each bad case."""

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from fieldshift.cli import main
from fieldshift.config import data_dir, repo_root
from fieldshift.pipeline import run_power
from fieldshift.sites import DEV_SITES
from fieldshift.sources import power
from fieldshift.validate import validate_all

FIXTURE = Path(__file__).parent / "fixtures" / "power" / "dev-floripa_daily_20240101_20240229.json"
START, END = date(2024, 1, 1), date(2024, 2, 29)
DEV = DEV_SITES["dev-floripa"]


@pytest.fixture
def tree(tmp_path: Path) -> Path:
    """<tmp>/data with valid dev outputs written by the pipeline; <tmp>/content/methods empty."""
    data = tmp_path / "data"
    cache = power.cache_path(data / "cache", "dev-floripa", START, END)
    cache.parent.mkdir(parents=True)
    shutil.copy(FIXTURE, cache)
    run_power(DEV, data_dir=data, start=START, end=END, offline=True)
    (tmp_path / "content" / "methods").mkdir(parents=True)
    return data


def out(data: Path) -> Path:
    return data / "dev" / "dev-floripa" / "output"


def edit(path: Path, fn) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    fn(doc)
    path.write_text(json.dumps(doc), encoding="utf-8")


def run(data: Path):
    return validate_all(data, data.parent / "content" / "methods")


def test_valid_pipeline_output_passes(tree):
    report = run(tree)
    assert report.ok, report.render()
    assert {Path(p).name for p in report.checked} == {"series.json", "provenance.json",
                                                      "indices.json"}  # fmt: skip
    assert not any("cache" in p for p in report.checked)  # raw source cache is not a contract
    assert any("et0-fao56" in w for w in report.warnings)  # VL6 pages not written yet


def test_method_page_anchor_clears_the_warning(tree):
    page = tree.parent / "content" / "methods" / "et0.md"
    page.write_text(
        "---\nanchor: et0-fao56   # comment\ntitle: ET0\nrefs: []\n---\n# ET0\n", encoding="utf-8"
    )
    assert not any("'et0-fao56'" in w for w in run(tree).warnings)


def test_reference_to_missing_record_fails(tree):
    bad = "prov:power:dev-floripa:nope:daily"
    edit(out(tree) / "series.json", lambda d: d["series"][0].update(provenance_id=bad))
    report = run(tree)
    assert not report.ok and any("nope" in e and "no provenance record" in e for e in report.errors)


def test_computed_input_without_record_fails(tree):
    def drop_t2m_max(d):
        del d["records"]["prov:power:dev-floripa:t2m_max:daily"]

    edit(out(tree) / "provenance.json", drop_t2m_max)
    errors = run(tree).errors
    assert any("input prov:power:dev-floripa:t2m_max:daily has no record" in e for e in errors)
    assert any("series[1].provenance_id" in e for e in errors)  # the Tmax series too


def test_fr19_field_missing_for_modeled_fails(tree):
    rid = "prov:power:dev-floripa:t2m:daily"
    edit(out(tree) / "provenance.json", lambda d: d["records"][rid]["access"].update(terms_url=""))
    errors = run(tree).errors
    assert any("FR19" in e and "access.terms_url" in e and "t2m:daily" in e for e in errors)


def test_computed_without_inputs_fails_the_contract(tree):
    rid = "prov:computed:dev-floripa:et0:daily"
    edit(out(tree) / "provenance.json", lambda d: d["records"][rid].update(inputs=[]))
    assert any("does not match ProvenanceRegistry" in e for e in run(tree).errors)


def test_lineage_cycle_fails(tree):
    def cycle(d):
        d["records"]["prov:computed:dev-floripa:heat_days:daily"]["inputs"] = [
            "prov:computed:dev-floripa:frost_days:daily"
        ]
        d["records"]["prov:computed:dev-floripa:frost_days:daily"]["inputs"] = [
            "prov:computed:dev-floripa:heat_days:daily"
        ]

    edit(out(tree) / "provenance.json", cycle)
    assert any("lineage cycle" in e for e in run(tree).errors)


def test_data_type_must_match_the_record(tree):
    edit(out(tree) / "series.json", lambda d: d["series"][0].update(data_type="satellite_observed"))
    assert any("data_type 'satellite_observed'" in e for e in run(tree).errors)


@pytest.mark.parametrize(("version", "msg"), [("2.0.0", "major"), ("1.99.0", "newer")])
def test_schema_version_must_be_compatible(tree, version, msg):
    edit(out(tree) / "indices.json", lambda d: d.update(schema_version=version))
    assert any(msg in e and "indices.json" in e for e in run(tree).errors)


def test_site_id_must_match_folder(tree):
    edit(out(tree) / "indices.json", lambda d: d.update(site_id="dev-other"))
    assert any("folder 'dev-floripa'" in e for e in run(tree).errors)


def test_unknown_or_stray_json_fails(tree):
    (out(tree) / "extra.json").write_text("{}", encoding="utf-8")
    stray = tree / "dev" / "dev-floripa" / "notes.json"
    stray.write_text("{}", encoding="utf-8")
    errors = run(tree).errors
    assert any("extra.json: unknown file name" in e for e in errors)
    assert any("notes.json: JSON outside" in e for e in errors)


def test_invalid_contract_fails(tree):
    edit(out(tree) / "series.json", lambda d: d["series"][0].update(unit="kelvin"))
    assert any("series.json: does not match SeriesBundle" in e for e in run(tree).errors)


def test_cli_exit_codes(tree, capsys):
    methods = str(tree.parent / "content" / "methods")
    assert main(["validate", "--all", "--data-dir", str(tree), "--methods-dir", methods]) == 0
    assert "validate: passed" in capsys.readouterr().out
    edit(out(tree) / "indices.json", lambda d: d.update(site_id="dev-other"))
    assert main(["validate", "--all", "--data-dir", str(tree), "--methods-dir", methods]) == 1
    assert "validate: FAILED" in capsys.readouterr().out


def test_committed_repo_data_passes():
    """Same check as the CI step: every JSON committed under data/ is valid."""
    report = validate_all(data_dir(), repo_root() / "content" / "methods")
    assert report.ok, report.render()
