# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Published site `cruz-alta` (promoted from DEV, issue #26): input, outputs and provenance.

Runs against the committed repository files, so it fails if the site is removed, turns into a
DEV point, or loses the ground-check limitations (#31) in its provenance.
"""

import json

from fieldshift.config import data_dir
from fieldshift.contracts import ProvenanceRegistry, SeriesBundle
from fieldshift.provenance.ground_check import RAIN_GROUND_CHECK, TMAX_GROUND_CHECK
from fieldshift.sites import DEV_SITES, resolve_site

SITE = "cruz-alta"


def test_site_yaml_resolves_to_the_ibge_centroid_and_is_not_dev():
    site = resolve_site(SITE, data_dir())
    dev = DEV_SITES["dev-cruz-alta"]
    assert (site.lat, site.lon) == (dev.lat, dev.lon) == (-28.703, -53.563)
    assert site.dev is False
    assert site.output_dir(data_dir()) == data_dir() / "sites" / SITE / "output"


def test_outputs_are_published_without_dev_label_and_keep_the_ground_check():
    out = data_dir() / "sites" / SITE / "output"
    bundle = SeriesBundle.model_validate_json((out / "series.json").read_text(encoding="utf-8"))
    registry = ProvenanceRegistry.model_validate_json(
        (out / "provenance.json").read_text(encoding="utf-8")
    )
    assert bundle.site_id == registry.site_id == SITE
    assert bundle.series
    assert {s.provenance_id for s in bundle.series} <= set(registry.records)
    texts = [lim.en for rec in registry.records.values() for lim in rec.limitations]
    assert not any("DEV ONLY" in t for t in texts)
    assert TMAX_GROUND_CHECK in texts
    assert RAIN_GROUND_CHECK in texts
    assert "DEV ONLY" not in json.dumps(json.loads((out / "indices.json").read_text("utf-8")))
