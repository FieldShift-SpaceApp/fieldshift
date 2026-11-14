# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Issue #31: the station comparison (Cruz Alta) is a limitation of every POWER Tmax/rain record."""

from test_indices import DEV, synthetic_raw

from fieldshift.config import data_dir
from fieldshift.indices import climate as ix
from fieldshift.pipeline import build_all
from fieldshift.provenance.ground_check import (
    GROUND_CHECK_ANCHOR,
    RAIN_GROUND_CHECK,
    TMAX_GROUND_CHECK,
)


def _registry():
    params = ix.IndexParams(heat_tmax_c=29.0, baseline_start_year=2001, baseline_end_year=2002)
    _, registry, indices = build_all(DEV, synthetic_raw(range(2001, 2003)), params)
    return registry, indices


def _texts(registry, prov_id: str) -> list[str]:
    return [lim.en for lim in registry.records[prov_id].limitations]


def test_tmax_drift_is_declared_on_tmax_and_heat_day_records():
    registry, indices = _registry()
    ids = [
        "prov:power:dev-floripa:t2m_max:daily",
        "prov:computed:dev-floripa:heat_days:daily",
        *[
            m.provenance_id
            for m in [*indices.metrics, *indices.profiles]
            if m.index_key == "heat_days"
        ],
    ]
    assert len(ids) >= 4  # POWER Tmax, daily index, monthly profile and annual mean
    for prov_id in ids:
        assert TMAX_GROUND_CHECK in _texts(registry, prov_id), prov_id


def test_rain_frequency_and_extremes_are_declared_on_rain_records():
    registry, indices = _registry()
    ids = [
        "prov:power:dev-floripa:prectotcorr:daily",
        "prov:computed:dev-floripa:extreme_precip_days:daily",
        "prov:computed:dev-floripa:extreme_precip_total:daily",
        "prov:computed:dev-floripa:precip_p95:2001_2002",
    ]
    for prov_id in ids:
        assert RAIN_GROUND_CHECK in _texts(registry, prov_id), prov_id


def test_texts_state_drift_dry_spells_extremes_and_the_cross_check():
    assert "+1.84 °C in 2019-2025" in TMAX_GROUND_CHECK and "A853" in TMAX_GROUND_CHECK
    assert "local weather station" in TMAX_GROUND_CHECK
    assert "dry spells are shorter" in RAIN_GROUND_CHECK
    assert "heavy rain is smoothed" in RAIN_GROUND_CHECK
    assert "rain gauge or GPM IMERG" in RAIN_GROUND_CHECK
    for text in (TMAX_GROUND_CHECK, RAIN_GROUND_CHECK):
        assert f"#{GROUND_CHECK_ANCHOR}" in text  # points to the public method page


def test_public_method_page_defines_the_anchor_the_limitations_point_to():
    page = data_dir().parent / "content" / "methods" / "satellite-vs-ground.md"
    front = page.read_text(encoding="utf-8").split("---")[1]
    assert f"anchor: {GROUND_CHECK_ANCHOR}" in front.splitlines()


def test_records_that_do_not_read_tmax_or_rain_have_no_ground_check():
    registry, _ = _registry()
    for prov_id in (
        "prov:computed:dev-floripa:frost_days:daily",
        "prov:power:dev-floripa:t2m_min:daily",
    ):
        texts = _texts(registry, prov_id)
        assert TMAX_GROUND_CHECK not in texts and RAIN_GROUND_CHECK not in texts
