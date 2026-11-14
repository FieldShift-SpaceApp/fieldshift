# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""POWER layer end to end on a recorded response: contracts, FR19 provenance, ADR-3, sites, CLI."""

import json
import shutil
from datetime import date
from pathlib import Path

import pytest

from fieldshift.cli import main
from fieldshift.config import data_dir
from fieldshift.contracts import ProvenanceRegistry, SeriesBundle
from fieldshift.errors import PipelineError
from fieldshift.pipeline import build_all, build_power, run_power
from fieldshift.sites import DEV_SITES, SitePoint, resolve_site
from fieldshift.sources import power

FIXTURE = Path(__file__).parent / "fixtures" / "power" / "dev-floripa_daily_20240101_20240229.json"
START, END = date(2024, 1, 1), date(2024, 2, 29)
DEV = DEV_SITES["dev-floripa"]


@pytest.fixture
def wrapped() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    """A data/ tree whose cache already holds the recorded response."""
    target = power.cache_path(tmp_path / "cache", "dev-floripa", START, END)
    target.parent.mkdir(parents=True)
    shutil.copy(FIXTURE, target)
    return tmp_path


def built(wrapped):
    return build_power(DEV, power.parse(wrapped, lat=DEV.lat, lon=DEV.lon))


def test_bundle_and_registry_are_valid_contracts(wrapped):
    bundle, registry = built(wrapped)
    SeriesBundle.model_validate(bundle.model_dump(mode="json"))
    ProvenanceRegistry.model_validate(registry.model_dump(mode="json"))
    assert len(bundle.series) == len(power.PARAMS) + 1  # + ET0
    assert {s.provenance_id for s in bundle.series} <= set(registry.records)  # VL1 data layer


def test_every_record_has_fr19_fields(wrapped):
    _, registry = built(wrapped)
    for rec in registry.records.values():
        assert rec.variable.unit and rec.spatial.resolution and rec.temporal.period
        assert rec.aggregation.en and rec.data_type in ("modeled", "computed")
        if rec.data_type == "modeled":
            assert rec.source.dataset == "NASA POWER" and rec.source.version.startswith("v2.")
            assert rec.access.url.startswith(power.POWER_URL) and "community=AG" in rec.access.url
            assert rec.access.terms_url and rec.access.accessed_at.endswith("-03:00")
            assert rec.spatial.support == "containing_pixel"
        assert any("DEV ONLY" in lim.en for lim in rec.limitations)


def test_soil_wetness_is_labeled_modeled(wrapped):
    bundle, registry = built(wrapped)
    for key in ("soil_wetness_top_modeled", "soil_wetness_root_modeled"):
        s = next(s for s in bundle.series if s.variable_key == key)
        assert s.data_type == "modeled" and s.unit == "1"
        assert any(
            "not volumetric" in lim.en for lim in registry.records[s.provenance_id].limitations
        )


def test_et0_is_computed_with_lineage_to_existing_power_records(wrapped):
    bundle, registry = built(wrapped)
    s = next(s for s in bundle.series if s.variable_key == "et0")
    rec = registry.records[s.provenance_id]
    assert s.data_type == "computed" and s.aggregation.temporal == "sum" and s.unit == "mm"
    assert rec.method.doc_anchor == "et0-fao56"
    assert set(rec.inputs) <= set(registry.records) and len(rec.inputs) == 6
    jan = s.points[0].v
    assert 60 < jan < 250  # plausible summer month total at the dev point (mm)


def test_aggregators_follow_adr3(wrapped):
    bundle, _ = built(wrapped)
    by_key = {s.variable_key: s for s in bundle.series}
    assert by_key["precip"].aggregation.temporal == "sum" and by_key["precip"].unit == "mm"
    for key in ("air_temp_mean", "air_temp_max", "rel_humidity", "soil_wetness_top_modeled"):
        assert by_key[key].aggregation.temporal == "mean"
    daily = wrapped["response"]["properties"]["parameter"]["PRECTOTCORR"]
    jan_total = sum(v for k, v in daily.items() if k.startswith("202401"))
    assert by_key["precip"].points[0].v == round(jan_total, 1)
    tmax = wrapped["response"]["properties"]["parameter"]["T2M_MAX"]
    feb = [v for k, v in tmax.items() if k.startswith("202402")]
    assert by_key["air_temp_max"].points[1].v == round(sum(feb) / 29, 1)


def test_missing_day_leaves_month_null_and_declares_gap(wrapped):
    wrapped["response"]["properties"]["parameter"]["T2M_MIN"]["20240215"] = -999.0
    bundle, _ = built(wrapped)
    tmin = next(s for s in bundle.series if s.variable_key == "air_temp_min")
    et0 = next(s for s in bundle.series if s.variable_key == "et0")
    for s in (tmin, et0):  # ET0 needs Tmin, so its February is a gap too
        assert [p.v is None for p in s.points] == [False, True]
        assert s.points[1].q == "gap"
        assert s.coverage.valid_pct == 50.0
        assert [(g.start, g.end) for g in s.coverage.known_gaps] == [("2024-02", "2024-02")]
        assert "At least one day" in s.coverage.known_gaps[0].reason.en


def test_run_power_offline_writes_dev_outputs_outside_data_sites(data_root):
    out = run_power(DEV, data_dir=data_root, start=START, end=END, offline=True)
    assert out.series_path == data_root / "dev" / "dev-floripa" / "output" / "series.json"
    assert out.indices_path.name == "indices.json" and out.indices_path.is_file()
    assert not (data_root / "sites").exists()  # scripts/sync-data.mjs publishes data/sites only
    first = out.series_path.read_bytes()
    run_power(DEV, data_dir=data_root, start=START, end=END, offline=True)
    assert out.series_path.read_bytes() == first  # deterministic
    assert b"\r\n" not in first


def test_run_power_merges_provenance_records_of_other_stages(data_root):
    """#25: the rotation stage writes to the same provenance.json; POWER must not drop it."""
    first = run_power(DEV, data_dir=data_root, start=START, end=END, offline=True)
    other = first.registry.records["prov:power:dev-floripa:t2m:daily"].model_copy(
        update={"id": "prov:power:dev-floripa:other_stage:daily"}
    )
    path = first.provenance_path
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["records"][other.id] = other.model_dump(mode="json")
    doc["records"]["prov:power:dev-floripa:t2m:daily"]["title"]["en"] = "stale title"
    path.write_text(json.dumps(doc), encoding="utf-8")
    again = run_power(DEV, data_dir=data_root, start=START, end=END, offline=True)
    written = ProvenanceRegistry.model_validate_json(path.read_text(encoding="utf-8"))
    assert other.id in written.records  # other stage's record kept
    assert set(first.registry.records) <= set(written.records)
    t2m = written.records["prov:power:dev-floripa:t2m:daily"]
    assert t2m.title.en != "stale title"  # same id: replaced by the new record
    assert again.registry == written


def test_cli_fetch_power_offline(data_root, capsys):
    code = main(["fetch", "power", "--site", "dev-floripa", "--start", "2024-01-01",
                 "--end", "2024-02-29", "--offline", "--data-dir", str(data_root)])  # fmt: skip
    assert code == 0
    assert "[DEV ONLY]" in capsys.readouterr().out


def test_cli_offline_without_cache_fails_cleanly(tmp_path, capsys):
    code = main(["fetch", "power", "--site", "dev-floripa", "--start", "2024-01-01",
                 "--end", "2024-02-29", "--offline", "--data-dir", str(tmp_path)])  # fmt: skip
    assert code == 1
    assert "NOT_EXTRACTED_YET" in capsys.readouterr().err


# --- sites ---------------------------------------------------------------------------------


def test_dev_site_is_marked_and_routed_to_data_dev(tmp_path):
    assert DEV.dev and DEV.id.startswith("dev-") and "DEV ONLY" in DEV.label
    assert DEV.output_dir(tmp_path) == tmp_path / "dev" / "dev-floripa" / "output"


def test_only_dev_prefixed_ids_can_be_dev():
    with pytest.raises(PipelineError):
        SitePoint("brasil", -27.6, -48.5, "x", dev=True)
    with pytest.raises(PipelineError):
        SitePoint("dev-x", -27.6, -48.5, "x", dev=False)


def test_real_site_without_input_file_points_to_surgeon(tmp_path):
    with pytest.raises(PipelineError, match="SURGEON"):
        resolve_site("brasil", tmp_path)


def test_real_site_uses_field_centroid_from_site_yaml(tmp_path):
    site_dir = tmp_path / "sites" / "testsite" / "input"
    site_dir.mkdir(parents=True)
    (site_dir / "site.yaml").write_text(
        "id: testsite\nname: { en: Test field }\nfield:\n  type: Polygon\n"
        "  coordinates: [[[10.0, 20.0], [10.2, 20.0], [10.2, 20.2], [10.0, 20.2], [10.0, 20.0]]]\n",
        encoding="utf-8",
    )
    site = resolve_site("testsite", tmp_path)
    assert (site.lat, site.lon) == pytest.approx((20.1, 10.1))
    assert not site.dev and site.output_dir(tmp_path).parts[-3:] == ("sites", "testsite", "output")


def test_explicit_lat_lon_needs_both(tmp_path):
    with pytest.raises(PipelineError):
        resolve_site("dev-x", tmp_path, lat=1.0)
    site = resolve_site("dev-x", tmp_path, lat=1.0, lon=2.0)
    assert site.dev and (site.lat, site.lon) == (1.0, 2.0)


# --- committed dev data (the CI works on the committed cache, never the network) ------------


def test_committed_dev_outputs_regenerate_from_committed_cache():
    root = data_dir()
    caches = sorted((root / "cache" / "power" / "dev-floripa").glob("daily_*.json"))
    assert caches, "data/cache/power/dev-floripa/ must hold the committed raw response"
    cache = caches[-1]
    _, start, end = cache.stem.split("_")
    raw = power.parse(json.loads(cache.read_text(encoding="utf-8")), lat=DEV.lat, lon=DEV.lon)
    bundle, registry, indices = build_all(DEV, raw)
    out = DEV.output_dir(root)
    for model, name in ((bundle, "series"), (registry, "provenance"), (indices, "indices")):
        committed = json.loads((out / f"{name}.json").read_text(encoding="utf-8"))
        assert model.model_dump(mode="json") == committed, name
    assert raw.first_day.strftime("%Y%m%d") == start and raw.last_day.strftime("%Y%m%d") == end
