"""Contratos v1.0.0 (ADR-4, Data Models): formato e validadores (VL1, VL3, VL4, FR5, FR21)."""

import copy

import pytest
from pydantic import ValidationError

from fieldshift.contracts import (
    SCHEMA_VERSION,
    ClimateIndices,
    Confidence,
    Evidence,
    Period,
    Provenance,
    ProvenanceRegistry,
    Rotation,
    RotationFile,
    SeriesBundle,
    Site,
    SiteManifest,
    SitesIndex,
    StrategySet,
    TimeSeries,
    ValidationFile,
)

LT = {"en": "text"}
PERIOD = {"start": "1991-01-01", "end": "2020-12-31"}


def prov_observed(**over):
    data = {
        "id": "prov:power:brasil:t2m_max:daily",
        "data_type": "modeled",
        "title": {"en": "NASA POWER daily maximum air temperature"},
        "source": {
            "dataset": "NASA POWER",
            "provider": "NASA LaRC",
            "product": "POWER Daily API, community AG",
            "version": "2.x",
        },
        "variable": {"code": "T2M_MAX", "name": LT, "unit": "degC"},
        "spatial": {"resolution": "0.5° × 0.625°", "support": "containing_pixel"},
        "temporal": {"resolution": "daily", "period": PERIOD},
        "aggregation": LT,
        "access": {
            "url": "https://power.larc.nasa.gov/api/temporal/daily/point",
            "accessed_at": "2026-11-14T13:05:00-03:00",
            "terms_url": "https://power.larc.nasa.gov/",
        },
        "limitations": [],
    }
    data.update(over)
    return data


def prov_computed(**over):
    data = prov_observed(
        id="prov:computed:brasil:et0:monthly",
        data_type="computed",
        source=None,
        access=None,
        method={"name": "FAO-56", "ref": {"label": "FAO-56"}, "doc_anchor": "method-et0-fao56"},
        inputs=["prov:power:brasil:t2m_max:daily"],
    )
    data.update(over)
    return data


def confidence(level="medium", sources=1):
    return {"level": level, "reason": LT, "independent_sources": sources}


def evidence(**over):
    data = {
        "id": "ev-1",
        "statement": LT,
        "value": 12.0,
        "unit": "days",
        "period": PERIOD,
        "dataset_label": "NASA POWER",
        "series_ids": ["power.air_temp_max.monthly_mean"],
        "provenance_ids": ["prov:power:brasil:t2m_max:daily"],
        "data_type": "computed",
        "confidence": confidence(),
    }
    data.update(over)
    return data


def metric(**over):
    data = {
        "id": "bare_months_per_year",
        "label": LT,
        "value": 2.0,
        "unit": "count",
        "period": PERIOD,
        "data_type": "computed",
        "provenance_id": "prov:computed:brasil:soil-cover",
    }
    data.update(over)
    return data


def segment(**over):
    data = {
        "id": "soy",
        "label": {"en": "Soybean"},
        "role": "cash_crop",
        "crop_id": "soybean",
        "start": {"year_index": 0, "month": 10},
        "end": {"year_index": 0, "month": 2},
        "soil": {"main": "covered", "establishment_months": 1},
        "irrigated": False,
        "refs": [{"label": "ZARC"}],
    }
    data.update(over)
    return data


def rotation(**over):
    data = {
        "id": "brasil-current",
        "site_id": "brasil",
        "name": LT,
        "kind": "current",
        "cycle_years": 1,
        "segments": [segment()],
        "data_type": "user_provided",
        "provenance_id": "prov:user:brasil:rotation-current",
    }
    data.update(over)
    return data


def timeline(n=12, **over):
    data = {
        "rotation_id": "brasil-current",
        "months": [
            {
                "position": i,
                "year_index": i // 12,
                "month": (i % 12) + 1,
                "state": "bare",
                "segment_ids": [],
            }
            for i in range(n)
        ],
        "bare_months_per_year": metric(),
        "provenance_id": "prov:computed:brasil:soil-cover",
    }
    data.update(over)
    return data


def strategy(sid, is_current=False):
    item = {"text": LT}
    return {
        "id": sid,
        "site_id": "brasil",
        "is_current": is_current,
        "name": LT,
        "rotation_id": "brasil-current",
        "blocks": {
            "why": [item],
            "evidence": [evidence()],
            "benefits": [item],
            "gaps": [item],
            "local_review": [item],
        },
        "confidence": confidence(),
        "criteria": {},
        "requirements": {"irrigation": False, "livestock": False, "equipment": []},
        "generator": {
            "method_id": "placeholder",
            "version": "0",
            "provenance_id": "prov:computed:brasil:gen",
        },
    }


def strategy_set(strategies):
    return {
        "schema_version": SCHEMA_VERSION,
        "site_id": "brasil",
        "rotations": [rotation()],
        "timelines": [timeline()],
        "strategies": strategies,
    }


def site(**over):
    data = {
        "schema_version": SCHEMA_VERSION,
        "id": "brasil",
        "name": {"en": "Demo field"},
        "country": "BR",
        "hemisphere": "S",
        "timezone": "America/Sao_Paulo",
        "point": {"lat": -12.5, "lon": -55.7},
        "field": {
            "type": "Polygon",
            "coordinates": [[[-55.7, -12.5], [-55.6, -12.5], [-55.6, -12.4], [-55.7, -12.5]]],
        },
        "area_ha": {"value": 100.0, "provenance_id": "prov:computed:brasil:area"},
        "elevation_m": {"value": 380.0, "provenance_id": "prov:srtm:brasil:elevation"},
        "ag_year": {"start_month": 9, "label": "split"},
        "default_units": "metric",
        "context": {"region": LT, "summary": LT, "refs": []},
        "validated_by": None,
    }
    data.update(over)
    return data


# --- comuns ---------------------------------------------------------------------------------


def test_schema_version_is_semver():
    assert SCHEMA_VERSION == "1.2.0"


def test_period_rejects_end_before_start():
    with pytest.raises(ValidationError):
        Period(start="2020-01-02", end="2020-01-01")


def test_contracts_reject_unknown_keys():
    with pytest.raises(ValidationError):
        Site.model_validate(site(heat_threshold_typo=35))


def test_contracts_are_frozen():
    s = Site.model_validate(site())
    with pytest.raises(ValidationError):
        s.id = "nevada"


# --- Provenance (VL1, FR19) -----------------------------------------------------------------


def test_observed_provenance_is_valid():
    p = Provenance.model_validate(prov_observed())
    assert p.source is not None and p.source.dataset == "NASA POWER"


@pytest.mark.parametrize("missing", ["source", "access"])
def test_observed_provenance_requires_source_and_access(missing):
    with pytest.raises(ValidationError, match="FR19"):
        Provenance.model_validate(prov_observed(**{missing: None}))


def test_observed_provenance_requires_version_or_collection():
    data = prov_observed()
    data["source"]["version"] = ""
    with pytest.raises(ValidationError, match="collection_id"):
        Provenance.model_validate(data)
    data["source"]["collection_id"] = "NASA/SMAP/SPL4SMGP/008"
    Provenance.model_validate(data)


def test_computed_provenance_requires_method_and_inputs():
    Provenance.model_validate(prov_computed())
    with pytest.raises(ValidationError, match="computed"):
        Provenance.model_validate(prov_computed(inputs=[]))
    with pytest.raises(ValidationError, match="computed"):
        Provenance.model_validate(prov_computed(method=None))


def test_user_provided_requires_author_and_refs():
    base = prov_observed(
        id="prov:user:brasil:rotation-current",
        data_type="user_provided",
        source=None,
        access=None,
    )
    with pytest.raises(ValidationError, match="user_provided"):
        Provenance.model_validate(base)
    Provenance.model_validate({**base, "authored_by": "Agronomist", "refs": [{"label": "ZARC"}]})


def test_provenance_id_pattern():
    with pytest.raises(ValidationError):
        Provenance.model_validate(prov_observed(id="power:brasil"))


def test_registry_keys_must_match_ids():
    rec = prov_observed()
    ok = {"schema_version": SCHEMA_VERSION, "site_id": "brasil", "records": {rec["id"]: rec}}
    ProvenanceRegistry.model_validate(ok)
    ProvenanceRegistry.model_validate({**ok, "site_id": "global"})
    with pytest.raises(ValidationError, match="key"):
        ProvenanceRegistry.model_validate({**ok, "records": {"prov:other": rec}})


# --- Site ------------------------------------------------------------------------------------


def test_site_is_valid():
    s = Site.model_validate(site())
    assert s.ag_year.start_month == 9


@pytest.mark.parametrize("bad_id", ["Brasil", "b", "1abc", "brasil_x"])
def test_site_id_pattern(bad_id):
    with pytest.raises(ValidationError):
        Site.model_validate(site(id=bad_id))


def test_site_polygon_must_be_closed():
    bad = site()
    bad["field"]["coordinates"][0][-1] = [-55.0, -12.0]
    with pytest.raises(ValidationError, match="closed"):
        Site.model_validate(bad)


def test_site_month_out_of_range():
    with pytest.raises(ValidationError):
        Site.model_validate(site(ag_year={"start_month": 13, "label": "split"}))


def test_sites_index():
    SitesIndex.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "sites": [
                {
                    "id": "brasil",
                    "name": LT,
                    "country": "BR",
                    "hemisphere": "S",
                    "default_units": "metric",
                    "summary": LT,
                }
            ],
        }
    )


# --- TimeSeries ------------------------------------------------------------------------------


def series(**over):
    data = {
        "id": "power.air_temp_max.monthly_mean",
        "site_id": "brasil",
        "variable_key": "air_temp_max",
        "label": LT,
        "unit": "degC",
        "frequency": "monthly",
        "aggregation": {"temporal": "mean", "spatial": "containing_pixel"},
        "data_type": "modeled",
        "provenance_id": "prov:power:brasil:t2m_max:daily",
        "points": [{"t": "2024-01", "v": 31.2}, {"t": "2024-02", "v": None, "q": "gap"}],
        "coverage": {
            "first": "2024-01",
            "last": "2024-02",
            "valid_pct": 50,
            "known_gaps": [{"start": "2024-02", "end": "2024-02", "reason": LT}],
        },
    }
    data.update(over)
    return data


def test_series_bundle_is_valid():
    b = SeriesBundle.model_validate(
        {"schema_version": SCHEMA_VERSION, "site_id": "brasil", "series": [series()]}
    )
    assert b.series[0].points[1].v is None


def test_series_rejects_unknown_variable_key():
    with pytest.raises(ValidationError):
        TimeSeries.model_validate(series(variable_key="temperature"))


def test_series_baseline_needs_12_values():
    base = {"period": PERIOD, "monthly_mean": [1.0] * 11, "provenance_id": "prov:x"}
    with pytest.raises(ValidationError):
        TimeSeries.model_validate(series(baseline=base))
    TimeSeries.model_validate(series(baseline={**base, "monthly_mean": [1.0] * 11 + [None]}))


def test_series_valid_pct_range():
    data = series()
    data["coverage"]["valid_pct"] = 101
    with pytest.raises(ValidationError):
        TimeSeries.model_validate(data)


# --- Metric / MonthlyProfile -----------------------------------------------------------------


def test_climate_indices_is_valid():
    m = metric(
        comparison={
            "baseline_value": 20.0,
            "baseline_period": PERIOD,
            "delta": 1.1,
            "delta_unit": "delta_degC",
        },
        tags=["impact_finding"],
    )
    prof = {
        "id": "frost_probability.by_month.1991_2020",
        "label": LT,
        "unit": "probability",
        "values": [0.0] * 12,
        "period": PERIOD,
        "data_type": "computed",
        "provenance_id": "prov:computed:brasil:frost",
    }
    ClimateIndices.model_validate(
        {"schema_version": SCHEMA_VERSION, "site_id": "brasil", "metrics": [m], "profiles": [prof]}
    )
    with pytest.raises(ValidationError):
        ClimateIndices.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "site_id": "brasil",
                "metrics": [],
                "profiles": [{**prof, "values": [0.0] * 13}],
            }
        )


def test_v1_1_index_key_is_optional_and_controlled():
    """MINOR 1.1.0: a 1.0.0 document (no `index_key`) still validates; unknown keys fail."""
    base = {"schema_version": SCHEMA_VERSION, "site_id": "brasil", "profiles": []}
    ClimateIndices.model_validate({**base, "metrics": [metric()]})
    ClimateIndices.model_validate({**base, "metrics": [metric(index_key="heat_days")]})
    with pytest.raises(ValidationError):
        ClimateIndices.model_validate({**base, "metrics": [metric(index_key="hot_days")]})


def test_v1_1_new_variable_keys_and_method_parameters():
    for key in ("evap_land_modeled", "soil_wetness_profile_modeled", "water_deficit"):
        TimeSeries.model_validate(series(variable_key=key))
    method = {
        "name": "heat days",
        "ref": {"label": "x"},
        "doc_anchor": "heat-days",
        "parameters": {"tmax_threshold_degC": 35.0, "comparison": ">"},
    }
    rec = Provenance.model_validate(prov_computed(method=method))
    assert rec.method.parameters == {"tmax_threshold_degC": 35.0, "comparison": ">"}
    Provenance.model_validate(prov_computed())  # 1.0.0 record without `parameters`


# --- Evidence / Confidence (VL3, VL4) --------------------------------------------------------


def test_evidence_requires_provenance():
    Evidence.model_validate(evidence())
    with pytest.raises(ValidationError):
        Evidence.model_validate(evidence(provenance_ids=[]))


def test_high_confidence_needs_two_sources():
    Confidence.model_validate(confidence("high", 2))
    with pytest.raises(ValidationError, match="VL4"):
        Confidence.model_validate(confidence("high", 1))


# --- Rotation (FR21) -------------------------------------------------------------------------


def test_rotation_file_is_valid():
    RotationFile.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "site_id": "brasil",
            "rotation": rotation(),
            "timeline": timeline(),
        }
    )


def test_rotation_segment_year_index_within_cycle():
    with pytest.raises(ValidationError, match="year_index"):
        Rotation.model_validate(rotation(segments=[segment(end={"year_index": 1, "month": 2})]))
    Rotation.model_validate(
        rotation(cycle_years=2, segments=[segment(end={"year_index": 1, "month": 2})])
    )


def test_rotation_needs_segments():
    with pytest.raises(ValidationError):
        Rotation.model_validate(rotation(segments=[]))


def test_fallow_has_no_crop():
    Rotation.model_validate(rotation(segments=[segment(role="fallow", crop_id=None)]))


def test_rotation_file_timeline_length_matches_cycle():
    with pytest.raises(ValidationError, match="cycle_years"):
        RotationFile.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "site_id": "brasil",
                "rotation": rotation(),
                "timeline": timeline(n=11),
            }
        )


def test_rotation_file_timeline_must_reference_rotation():
    with pytest.raises(ValidationError, match="rotation_id"):
        RotationFile.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "site_id": "brasil",
                "rotation": rotation(),
                "timeline": timeline(rotation_id="other"),
            }
        )


# --- Strategy (FR5, FR6, VL2) ----------------------------------------------------------------


def test_strategy_set_is_valid():
    StrategySet.model_validate(strategy_set([strategy("a", True), strategy("b"), strategy("c")]))


def test_strategy_set_needs_three():
    with pytest.raises(ValidationError):
        StrategySet.model_validate(strategy_set([strategy("a", True), strategy("b")]))


@pytest.mark.parametrize("currents", [0, 2])
def test_strategy_set_exactly_one_current(currents):
    items = [strategy(s, i < currents) for i, s in enumerate("abc")]
    with pytest.raises(ValidationError, match="is_current"):
        StrategySet.model_validate(strategy_set(items))


def test_strategy_rotation_must_exist_in_set():
    items = [strategy("a", True), strategy("b"), strategy("c")]
    items[2]["rotation_id"] = "missing"
    with pytest.raises(ValidationError, match="rotation_id"):
        StrategySet.model_validate(strategy_set(items))


@pytest.mark.parametrize("block", ["why", "evidence", "benefits", "gaps", "local_review"])
def test_strategy_blocks_never_empty(block):
    items = [strategy("a", True), strategy("b"), strategy("c")]
    items[1] = copy.deepcopy(items[1])
    items[1]["blocks"][block] = []
    with pytest.raises(ValidationError):
        StrategySet.model_validate(strategy_set(items))


# --- SiteManifest ----------------------------------------------------------------------------


def test_manifest_is_valid():
    SiteManifest.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "site_id": "brasil",
            "generated_at": "2026-11-14T13:05:00Z",
            "pipeline": {
                "git_sha": "56d9285",
                "command": "fieldshift build --site brasil",
                "package_version": "0.1.0",
            },
            "contracts": {"site": "1.0.0", "provenance": "1.0.0"},
            "files": [
                {"path": "site.json", "contract": "site", "sha256": "0" * 64, "required": True}
            ],
            "layers": [
                {"id": "power", "status": "available", "series_ids": []},
                {
                    "id": "openet",
                    "status": "not_applicable",
                    "reason": {"code": "OUT_OF_REGION", "message": LT},
                    "series_ids": [],
                },
            ],
        }
    )


def test_manifest_rejects_unknown_layer():
    with pytest.raises(ValidationError):
        SiteManifest.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "site_id": "brasil",
                "generated_at": "2026-11-14T13:05:00Z",
                "pipeline": {"git_sha": "x", "command": "x", "package_version": "x"},
                "contracts": {},
                "files": [],
                "layers": [{"id": "sentinel", "status": "available", "series_ids": []}],
            }
        )


def test_generated_at_needs_timezone():
    with pytest.raises(ValidationError):
        SiteManifest.model_validate(
            {
                "schema_version": SCHEMA_VERSION,
                "site_id": "brasil",
                "generated_at": "2026-11-14T13:05:00",
                "pipeline": {"git_sha": "x", "command": "x", "package_version": "x"},
                "contracts": {},
                "files": [],
                "layers": [],
            }
        )


# --- RetrospectiveCheck (FR24) ---------------------------------------------------------------


def test_validation_file_is_valid():
    ValidationFile.model_validate(
        {
            "schema_version": SCHEMA_VERSION,
            "site_id": "brasil",
            "checks": [
                {
                    "id": "drought-2024",
                    "site_id": "brasil",
                    "event": {"name": LT, "period": PERIOD, "source": {"label": "news"}},
                    "observed": [evidence()],
                    "result": "does_not_confirm",
                    "discussion": LT,
                    "limitations": [],
                    "checked_by": "Agronomist",
                }
            ],
        }
    )


def test_copy_does_not_leak_between_tests():
    # deepcopy dos builders: nenhum teste muta o dict de outro
    a, b = site(), site()
    a["field"]["coordinates"][0][0][0] = 0
    assert b["field"]["coordinates"][0][0][0] == -55.7
