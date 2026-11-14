# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Rotation stage end to end on the TEST FIXTURE input: YAML, provenance, CLI, web fixture.

The web fixture (apps/web/tests/fixtures/rotation-file.json) is this stage's output for the same
input, so the TS components are tested on exactly what the pipeline writes. To regenerate it after a
deliberate change: FIELDSHIFT_UPDATE_FIXTURES=1 uv run pytest tests/test_rotation_stage.py
"""

import json
import os
import shutil
from pathlib import Path

import pytest

from fieldshift.cli import main
from fieldshift.contracts import ProvenanceRegistry, RotationFile
from fieldshift.errors import PipelineError
from fieldshift.io.store import dumps_stable
from fieldshift.rotation.inputs import load_rotation_input
from fieldshift.rotation.stage import build_rotation, run_rotation

FIXTURE_INPUT = Path(__file__).parent / "fixtures" / "rotation" / "test-fixture" / "input"
REPO_ROOT = Path(__file__).resolve().parents[3]
WEB_FIXTURE = REPO_ROOT / "apps" / "web" / "tests" / "fixtures" / "rotation-file.json"
SITE = "test-fixture"


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    """A data/ tree with the TEST FIXTURE site inputs (never the repo's data/sites)."""
    shutil.copytree(FIXTURE_INPUT, tmp_path / "sites" / SITE / "input")
    return tmp_path


def rotation_yaml(data_root: Path) -> Path:
    return data_root / "sites" / SITE / "input" / "rotation-current.yaml"


def built() -> tuple[RotationFile, ProvenanceRegistry]:
    return build_rotation(SITE, load_rotation_input(FIXTURE_INPUT / "rotation-current.yaml"), 9)


def test_fixture_is_marked_in_every_text_field():
    spec = load_rotation_input(FIXTURE_INPUT / "rotation-current.yaml")
    texts = [spec.name.en, spec.authored_by]
    for s in spec.segments:
        texts += [s.label.en, *(r.label for r in s.refs)]
        assert s.crop_id is None or s.crop_id.startswith("test-fixture")
    assert all("TEST FIXTURE" in t for t in texts)


def test_fixture_timeline_month_by_month():
    file, _ = built()
    tl = file.timeline
    states = [(m.year_index, m.month, m.state) for m in tl.months]
    assert states == [
        (0, 9, "residue"), (0, 10, "transition"), (0, 11, "covered"), (0, 12, "covered"),
        (0, 1, "covered"), (0, 2, "covered"), (0, 3, "covered"), (0, 4, "covered"),
        (0, 5, "covered"), (0, 6, "covered"), (0, 7, "bare"), (0, 8, "bare"),
        (1, 9, "bare"), (1, 10, "transition"), (1, 11, "covered"), (1, 12, "covered"),
        (1, 1, "covered"), (1, 2, "covered"), (1, 3, "transition"), (1, 4, "covered"),
        (1, 5, "covered"), (1, 6, "covered"), (1, 7, "covered"), (1, 8, "residue"),
    ]  # fmt: skip
    assert tl.months[12].segment_ids == []  # implicit bare month
    assert tl.months[10].segment_ids == ["tf-fallow-bare"]  # explicit bare fallow
    assert tl.bare_months_per_year.value == 1.5
    assert (tl.bare_months_per_year.period.start, tl.bare_months_per_year.period.end) == (
        "2000-09-01",
        "2002-08-31",
    )


def test_rotation_file_and_provenance_are_valid_and_linked():
    file, registry = built()
    RotationFile.model_validate(file.model_dump(mode="json"))
    ProvenanceRegistry.model_validate(registry.model_dump(mode="json"))
    assert file.rotation.kind == "current" and file.rotation.data_type == "user_provided"
    ids = {file.rotation.provenance_id, file.timeline.provenance_id}
    assert ids == set(registry.records)  # VL1 data layer
    user = registry.records[file.rotation.provenance_id]
    assert user.authored_by == "TEST FIXTURE (no agronomist)"
    assert [r.label for r in user.refs] == ["TEST FIXTURE: not a calendar source"]  # de-duplicated
    computed = registry.records[file.timeline.provenance_id]
    assert computed.method.name == "soil-cover-derivation v1"
    assert computed.inputs == [file.rotation.provenance_id]


def test_run_writes_outputs_and_keeps_other_provenance_records(data_root):
    out_dir = data_root / "sites" / SITE / "output"
    out_dir.mkdir(parents=True)
    other = {
        "id": "prov:fixture:test:other:daily",
        "data_type": "computed",
        "title": {"en": "TEST FIXTURE record from another stage"},
        "variable": {"code": "x", "name": {"en": "TEST FIXTURE"}, "unit": "mm"},
        "spatial": {"resolution": "TEST FIXTURE", "support": "point"},
        "temporal": {"resolution": "daily", "period": {"start": "2000-01-01", "end": "2000-01-31"}},
        "aggregation": {"en": "TEST FIXTURE"},
        "method": {"name": "TEST FIXTURE", "ref": {"label": "TEST FIXTURE"}, "doc_anchor": "x"},
        "inputs": ["prov:fixture:test:input:daily"],
        "limitations": [],
    }
    (out_dir / "provenance.json").write_text(
        json.dumps({"schema_version": "1.0.0", "site_id": SITE, "records": {other["id"]: other}}),
        encoding="utf-8",
    )
    out = run_rotation(SITE, data_dir=data_root)
    written = RotationFile.model_validate_json(out.rotation_path.read_text(encoding="utf-8"))
    assert written == out.file
    registry = ProvenanceRegistry.model_validate_json(
        out.provenance_path.read_text(encoding="utf-8")
    )
    assert other["id"] in registry.records
    assert out.file.timeline.provenance_id in registry.records
    # Idempotent: a second run gives the same bytes.
    before = out.rotation_path.read_bytes(), out.provenance_path.read_bytes()
    run_rotation(SITE, data_dir=data_root)
    assert (out.rotation_path.read_bytes(), out.provenance_path.read_bytes()) == before


def test_yaml_error_names_line_and_field(data_root):
    path = rotation_yaml(data_root)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("main: residue", "main: mulch"), encoding="utf-8")
    line = next(i for i, ln in enumerate(text.splitlines(), 1) if "main: residue" in ln)
    with pytest.raises(PipelineError) as exc:
        run_rotation(SITE, data_dir=data_root)
    assert f"rotation-current.yaml:{line} segments.5.soil.main" in str(exc.value)


def test_unknown_key_is_rejected_with_its_line(data_root):
    path = rotation_yaml(data_root)
    path.write_text(
        path.read_text(encoding="utf-8").replace("irrigated: false", "irigated: false", 1),
        encoding="utf-8",
    )
    with pytest.raises(PipelineError, match=r"segments\.0\.irigated: Extra inputs"):
        run_rotation(SITE, data_dir=data_root)


def test_segment_without_source_is_rejected(data_root):
    path = rotation_yaml(data_root)
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace('refs: [ { label: "TEST FIXTURE: not a calendar source" } ]', "refs: []", 1),
        encoding="utf-8",
    )
    with pytest.raises(PipelineError, match="segments without refs .*tf-cash-1"):
        run_rotation(SITE, data_dir=data_root)


def test_establishment_longer_than_segment_fails_the_stage(data_root):
    path = rotation_yaml(data_root)
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("main: bare, establishment_months: 0", "main: bare, establishment_months: 5"),
        encoding="utf-8",
    )
    with pytest.raises(PipelineError, match="tf-fallow-bare: establishment_months 5"):
        run_rotation(SITE, data_dir=data_root)


def test_missing_inputs_fail_clearly(tmp_path):
    with pytest.raises(PipelineError, match="site.yaml not found"):
        run_rotation("brasil", data_dir=tmp_path)
    with pytest.raises(PipelineError, match="invalid site id"):
        run_rotation("../x", data_dir=tmp_path)


def test_site_id_mismatch_is_rejected(data_root):
    site_yaml = data_root / "sites" / SITE / "input" / "site.yaml"
    site_yaml.write_text(
        site_yaml.read_text(encoding="utf-8").replace("id: test-fixture", "id: other"),
        encoding="utf-8",
    )
    with pytest.raises(PipelineError, match="'other' != 'test-fixture'"):
        run_rotation(SITE, data_dir=data_root)


def test_cli_rotation(data_root, capsys):
    assert main(["rotation", "--site", SITE, "--data-dir", str(data_root)]) == 0
    assert "bare-soil months per year: 1.5" in capsys.readouterr().out
    assert main(["rotation", "--site", "nowhere", "--data-dir", str(data_root)]) == 1
    assert "not found" in capsys.readouterr().err


def test_web_fixture_is_the_pipeline_output():
    file, _ = built()
    expected = dumps_stable(file.model_dump(mode="json"))
    if os.environ.get("FIELDSHIFT_UPDATE_FIXTURES") == "1":
        WEB_FIXTURE.write_text(expected, encoding="utf-8", newline="\n")
    assert WEB_FIXTURE.read_text(encoding="utf-8") == expected, (
        "apps/web/tests/fixtures/rotation-file.json is out of date; see this module's docstring"
    )
