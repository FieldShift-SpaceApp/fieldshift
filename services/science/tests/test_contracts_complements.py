# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Contracts v1.2.0 (MINOR): ForecastScorecard, EventTimeline and BareSoilCalendar."""

import copy

import pytest
from pydantic import ValidationError

from fieldshift.contracts import (
    SCHEMA_VERSION,
    TOP_LEVEL_MODELS,
    BareSoilCalendar,
    EnsoRainSignal,
    EventTimeline,
    ForecastScorecard,
    Provenance,
)
from fieldshift.contracts.export import build_schema

URL = "https://example.org/source"


def scorecard(**over):
    data = {
        "schema_version": SCHEMA_VERSION,
        "site_id": "cruz-alta",
        "target_season": "JJA",
        "observed": [
            {"year": 2022, "oni_jja": -0.7, "phase": "la_nina"},
            {"year": 2023, "oni_jja": 1.0, "phase": "el_nino"},
        ],
        "observed_provenance_id": "prov:noaa:global:oni",
        "sources": [
            {
                "id": "official",
                "label": {"en": "Official"},
                "kind": "probability",
                "provider": "NOAA CPC / IRI",
                "provenance_id": "prov:forecast:official",
            },
            {
                "id": "plume",
                "label": {"en": "Plume"},
                "kind": "nino34_anomaly",
                "provider": "IRI",
                "real_time_from": 2011,
                "provenance_id": "prov:forecast:plume",
            },
        ],
        "forecasts": [
            {
                "source_id": "official",
                "issue_month": 2,
                "target_year": 2023,
                "p_la_nina": 0.04,
                "p_neutral": 0.47,
                "p_el_nino": 0.49,
                "predicted_phase": "el_nino",
                "observed_phase": "el_nino",
                "hit": True,
                "source_url": URL,
            },
            {
                "source_id": "plume",
                "issue_month": 2,
                "target_year": 2022,
                "nino34_anomaly": -0.03,
                "predicted_phase": "neutral",
                "observed_phase": "la_nina",
                "hit": False,
                "source_url": URL,
            },
        ],
        "scores": [
            {
                "source_id": "official",
                "issue_month": 2,
                "first_year": 2023,
                "last_year": 2023,
                "n": 1,
                "phase_hit_rate": 1.0,
                "always_neutral_hit_rate": 0.0,
                "el_nino_observed": 1,
                "el_nino_hits": 1,
                "el_nino_forecasts": 1,
                "false_alarm_ratio": 0.0,
                "brier_el_nino": 0.26,
                "brier_climatology": 0.5,
                "brier_always_neutral": 1.0,
                "brier_skill_score": 0.48,
                "provenance_id": "prov:computed:cruz-alta:forecast-scores",
            }
        ],
    }
    data.update(over)
    return data


def timeline(**over):
    data = {
        "schema_version": SCHEMA_VERSION,
        "site_id": "cruz-alta",
        "id": "winter-2023",
        "title": {"en": "Winter 2023"},
        "period": {"start": "2023-01-01", "end": "2023-12-31"},
        "events": [
            {
                "id": "watch",
                "kind": "forecast",
                "date": "2023-04-13",
                "title": {"en": "El Niño Watch"},
                "detail": {"en": "62% chance of El Niño in May-July"},
                "values": [
                    {"id": "p", "label": {"en": "chance"}, "value": 0.62, "unit": "probability"}
                ],
                "provenance_id": "prov:user:cruz-alta:replay-2023",
                "refs": [{"label": "CPC", "url": URL}],
            },
            {
                "id": "outcome",
                "kind": "outcome",
                "period": {"start": "2023-05-21", "end": "2023-12-31"},
                "title": {"en": "Result"},
                "detail": {"en": "per hectare"},
                "values": [
                    {"id": "wheat", "label": {"en": "wheat"}, "value": -3829, "unit": "BRL/ha"},
                    {"id": "yield", "label": {"en": "yield"}, "value": 1500, "unit": "kg/ha"},
                ],
                "provenance_id": "prov:user:cruz-alta:replay-2023",
                "refs": [{"label": "IBGE", "url": URL}],
            },
        ],
    }
    data.update(over)
    return data


def fortnight(i, **over):
    data = {
        "index": i,
        "month": i // 2 + 1,
        "half": i % 2 + 1,
        "s2_median_pct": 10.0,
        "s2_min_pct": 5.0,
        "s2_max_pct": 20.0,
        "s2_years": 7,
        "modis_median_pct": 0.1,
        "modis_years": 7,
    }
    data.update(over)
    return data


def calendar(**over):
    data = {
        "schema_version": SCHEMA_VERSION,
        "site_id": "cruz-alta",
        "period": {"start": "2019-01-01", "end": "2025-12-31"},
        "ndvi_threshold": 0.25,
        "fortnights": [fortnight(i) for i in range(24)],
        "s2_provenance_id": "prov:computed:cruz-alta:s2",
        "modis_provenance_id": "prov:computed:cruz-alta:modis",
        "caveats": [{"en": "NDVI < 0.25 does not separate straw from bare soil."}],
    }
    data.update(over)
    return data


# --- registry and schema ---------------------------------------------------------------------


def test_new_documents_are_top_level_and_in_the_schema():
    for model in (ForecastScorecard, EventTimeline, BareSoilCalendar, EnsoRainSignal):
        assert model in TOP_LEVEL_MODELS
        assert model.__name__ in build_schema()["$defs"]
    assert "ReplayExtraUnit" in build_schema()["$defs"]


# --- ForecastScorecard -----------------------------------------------------------------------


def test_scorecard_is_valid():
    assert ForecastScorecard.model_validate(scorecard()).sources[1].real_time_from == 2011


def test_forecast_needs_probabilities_or_anomaly_not_both():
    data = scorecard()
    data["forecasts"][0]["nino34_anomaly"] = 0.5
    with pytest.raises(ValidationError, match="either three probabilities or an anomaly"):
        ForecastScorecard.model_validate(data)
    data = scorecard()
    del data["forecasts"][0]["p_neutral"]
    with pytest.raises(ValidationError, match="all three probabilities"):
        ForecastScorecard.model_validate(data)


def test_forecast_probabilities_sum_to_one():
    data = scorecard()
    data["forecasts"][0]["p_el_nino"] = 0.6
    with pytest.raises(ValidationError, match="sum to 1"):
        ForecastScorecard.model_validate(data)


def test_forecast_hit_must_match_phases():
    data = scorecard()
    data["forecasts"][1]["hit"] = True
    with pytest.raises(ValidationError, match="hit"):
        ForecastScorecard.model_validate(data)


def test_forecast_kind_must_match_its_source():
    data = scorecard()
    data["sources"][0]["kind"] = "nino34_anomaly"
    with pytest.raises(ValidationError, match="source kind"):
        ForecastScorecard.model_validate(data)


def test_forecast_observed_phase_must_match_observed_winter():
    data = scorecard()
    data["forecasts"][1]["observed_phase"] = "neutral"
    data["forecasts"][1]["hit"] = True
    with pytest.raises(ValidationError, match="observed winter"):
        ForecastScorecard.model_validate(data)


def test_forecast_unknown_source_and_duplicates_fail():
    data = scorecard()
    data["forecasts"][0]["source_id"] = "nobody"
    with pytest.raises(ValidationError, match="unknown source"):
        ForecastScorecard.model_validate(data)
    data = scorecard()
    data["forecasts"].append(copy.deepcopy(data["forecasts"][0]))
    with pytest.raises(ValidationError, match="duplicate forecast"):
        ForecastScorecard.model_validate(data)


def test_score_counts_are_checked():
    data = scorecard()
    data["scores"][0]["el_nino_hits"] = 2
    with pytest.raises(ValidationError, match="more El Niño hits"):
        ForecastScorecard.model_validate(data)
    data = scorecard()
    data["scores"][0]["el_nino_forecasts"] = 0
    data["scores"][0]["el_nino_hits"] = 0
    with pytest.raises(ValidationError, match="false_alarm_ratio"):
        ForecastScorecard.model_validate(data)


def test_probabilities_are_bounded():
    data = scorecard()
    data["scores"][0]["phase_hit_rate"] = 1.2
    with pytest.raises(ValidationError):
        ForecastScorecard.model_validate(data)


# --- EventTimeline ---------------------------------------------------------------------------


def test_timeline_is_valid():
    assert EventTimeline.model_validate(timeline()).events[1].values[0].unit == "BRL/ha"


def test_timeline_event_needs_exactly_one_of_date_or_period():
    data = timeline()
    data["events"][0]["period"] = {"start": "2023-04-13", "end": "2023-04-13"}
    with pytest.raises(ValidationError, match="exactly one of date or period"):
        EventTimeline.model_validate(data)


def test_timeline_keeps_narrative_order_and_stays_inside_its_period():
    data = timeline()
    data["events"].reverse()
    assert EventTimeline.model_validate(data).events[0].id == "outcome"
    data = timeline()
    data["events"][1]["period"]["end"] = "2024-01-31"
    with pytest.raises(ValidationError, match="outside the timeline period"):
        EventTimeline.model_validate(data)


def test_timeline_rejects_unknown_units_and_needs_refs():
    data = timeline()
    data["events"][1]["values"][0]["unit"] = "USD/ac"
    with pytest.raises(ValidationError):
        EventTimeline.model_validate(data)
    data = timeline()
    data["events"][0]["refs"] = []
    with pytest.raises(ValidationError):
        EventTimeline.model_validate(data)


# --- BareSoilCalendar ------------------------------------------------------------------------


def test_calendar_is_valid():
    assert len(BareSoilCalendar.model_validate(calendar()).fortnights) == 24


def test_calendar_needs_24_fortnights_in_order():
    with pytest.raises(ValidationError):
        BareSoilCalendar.model_validate(calendar(fortnights=[fortnight(i) for i in range(23)]))
    swapped = [fortnight(i) for i in range(24)]
    swapped[0], swapped[1] = swapped[1], swapped[0]
    with pytest.raises(ValidationError, match="0..23 in order"):
        BareSoilCalendar.model_validate(calendar(fortnights=swapped))


def test_fortnight_month_half_and_range_are_checked():
    with pytest.raises(ValidationError, match="month/half"):
        BareSoilCalendar.model_validate(
            calendar(fortnights=[fortnight(i, half=1) for i in range(24)])
        )
    bad = [fortnight(i) for i in range(24)]
    bad[3] = fortnight(3, s2_min_pct=30.0)
    with pytest.raises(ValidationError, match="min <= median <= max"):
        BareSoilCalendar.model_validate(calendar(fortnights=bad))
    bad[3] = fortnight(3, modis_median_pct=None)
    with pytest.raises(ValidationError, match="modis value is null only with 0 years"):
        BareSoilCalendar.model_validate(calendar(fortnights=bad))


def test_calendar_allows_a_fortnight_without_scenes_and_needs_a_caveat():
    empty = [fortnight(i) for i in range(24)]
    empty[5] = fortnight(5, s2_median_pct=None, s2_min_pct=None, s2_max_pct=None, s2_years=0)
    assert BareSoilCalendar.model_validate(calendar(fortnights=empty)).fortnights[5].s2_years == 0
    with pytest.raises(ValidationError):
        BareSoilCalendar.model_validate(calendar(caveats=[]))


# --- Provenance.attribution (v1.2.0) ---------------------------------------------------------


def _record(**over):
    data = {
        "id": "prov:computed:cruz-alta:s2",
        "data_type": "computed",
        "title": {"en": "t"},
        "variable": {"code": "x", "name": {"en": "x"}, "unit": "%"},
        "spatial": {"resolution": "10 m", "support": "regional"},
        "temporal": {
            "resolution": "16-day",
            "period": {"start": "2019-01-01", "end": "2025-12-31"},
        },
        "aggregation": {"en": "a"},
        "method": {"name": "m", "ref": {"label": "r"}, "doc_anchor": "a"},
        "inputs": ["prov:esa:cruz-alta:s2"],
        "limitations": [],
    }
    data.update(over)
    return data


def test_attribution_is_optional_and_grouped():
    assert Provenance.model_validate(_record()).attribution == []
    rec = Provenance.model_validate(
        _record(
            attribution=[
                {"group": "partner", "name": "ESA Copernicus Sentinel-2", "credit": "Copernicus"},
                {"group": "nasa", "name": "MODIS MOD13Q1"},
                {"group": "other_public", "name": "IBGE"},
            ]
        )
    )
    assert [a.group for a in rec.attribution] == ["partner", "nasa", "other_public"]
    with pytest.raises(ValidationError):
        Provenance.model_validate(_record(attribution=[{"group": "private", "name": "x"}]))


# --- EnsoRainSignal --------------------------------------------------------------------------


def rain_signal(**over):
    years = [
        {"year": 2015, "oni": 1.8, "phase": "el_nino", "total_mm": 900.0, "heavy_days": 3},
        {"year": 2016, "oni": -0.7, "phase": "la_nina", "total_mm": 400.0, "heavy_days": 0},
        {"year": 2017, "oni": -0.2, "phase": "neutral", "total_mm": None, "heavy_days": None},
    ]
    stats = [
        {"phase": p, "n_years": n, "mean_heavy_days": d, "mean_total_mm": t,
         "median_total_mm": t, "years_with_heavy_day": h}
        for p, n, d, t, h in (
            ("el_nino", 1, 3.0, 900.0, 1),
            ("la_nina", 1, 0.0, 400.0, 0),
            ("neutral", 0, None, None, 0),
        )
    ]  # fmt: skip
    data = {
        "schema_version": SCHEMA_VERSION,
        "site_id": "cruz-alta",
        "label": {"en": "Heavy rain in September-November by ENSO phase"},
        "months": [9, 10, 11],
        "phase_season": "SON",
        "heavy_rain_mm": 50.0,
        "oni_provenance_id": "prov:noaa:global:oni",
        "sources": [
            {
                "id": "nasa-power",
                "label": {"en": "NASA POWER"},
                "first_year": 2015,
                "last_year": 2017,
                "years": years,
                "by_phase": stats,
                "provenance_id": "prov:computed:cruz-alta:rain-signal:power",
            }
        ],
    }
    data.update(over)
    return data


def test_rain_signal_is_valid():
    doc = EnsoRainSignal.model_validate(rain_signal())
    assert doc.sources[0].by_phase[2].n_years == 0


def test_rain_signal_counts_and_phases_are_checked():
    data = rain_signal()
    data["sources"][0]["by_phase"][0]["n_years"] = 2
    with pytest.raises(ValidationError, match="complete years"):
        EnsoRainSignal.model_validate(data)
    data = rain_signal()
    data["sources"][0]["by_phase"][2]["phase"] = "el_nino"
    with pytest.raises(ValidationError):
        EnsoRainSignal.model_validate(data)
    data = rain_signal()
    data["sources"][0]["years"].reverse()
    with pytest.raises(ValidationError, match="ascending"):
        EnsoRainSignal.model_validate(data)
    data = rain_signal()
    data["sources"].append(copy.deepcopy(data["sources"][0]))
    with pytest.raises(ValidationError, match="unique"):
        EnsoRainSignal.model_validate(data)
