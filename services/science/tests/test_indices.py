# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Climate indices (issue #22): reference values, daily-before-monthly (ADR-3), parameters, FR19."""

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from fieldshift.contracts import ClimateIndices, ProvenanceRegistry, SeriesBundle
from fieldshift.errors import PipelineError
from fieldshift.harmonize.monthly import to_monthly
from fieldshift.indices import climate as ix
from fieldshift.pipeline import build_all
from fieldshift.sites import DEV_SITES
from fieldshift.sources import power

DEV = DEV_SITES["dev-floripa"]
FIXTURE = Path(__file__).parent / "fixtures" / "power" / "dev-floripa_daily_20240101_20240229.json"


# --- reference values -------------------------------------------------------------------------


def test_percentile_type7_matches_published_reference_values():
    # Hyndman & Fan (1996) type 7 = R quantile() default = numpy.percentile default
    assert ix.percentile_linear(range(1, 101), 95) == pytest.approx(95.05)
    assert ix.percentile_linear([1, 2, 3, 4], 50) == pytest.approx(2.5)
    assert ix.percentile_linear([15, 20, 35, 40, 50], 40) == pytest.approx(29.0)
    assert ix.percentile_linear([7.0], 95) == 7.0
    with pytest.raises(ValueError):
        ix.percentile_linear([], 95)


def test_growing_degree_days_simple_average_method():
    # McMaster & Wilhelm (1997), method 1: ((30 + 14) / 2) - 10 = 12
    assert ix.growing_degree_days(30.0, 14.0, 10.0) == pytest.approx(12.0)
    assert ix.growing_degree_days(12.0, 4.0, 10.0) == 0.0  # mean 8 < base: no negative GDD
    assert ix.growing_degree_days(30.0, None, 10.0) is None
    assert ix.growing_degree_days(30.0, 14.0, 8.0) == pytest.approx(14.0)  # base is a parameter


def test_heat_and_frost_thresholds_and_comparisons():
    assert ix.heat_day(35.0, 35.0) == 0.0 and ix.heat_day(35.1, 35.0) == 1.0  # strict >
    assert ix.frost_day(0.0, 0.0) == 1.0 and ix.frost_day(0.1, 0.0) == 0.0  # <=
    assert ix.heat_day(None, 35.0) is None and ix.frost_day(None, 0.0) is None
    assert ix.heat_day(31.0, 30.0) == 1.0  # threshold is a parameter


def test_water_deficit_is_et0_minus_precip():
    assert ix.water_deficit(5.0, 2.0) == pytest.approx(3.0)
    assert ix.water_deficit(2.0, 12.5) == pytest.approx(-10.5)  # surplus stays negative
    assert ix.water_deficit(None, 1.0) is None and ix.water_deficit(1.0, None) is None


def _year(y: int, fn) -> dict[date, float | None]:
    d, out = date(y, 1, 1), {}
    while d.year == y:
        out[d] = fn(d)
        d += timedelta(days=1)
    return out


def test_wet_day_percentile_uses_wet_days_of_complete_baseline_only():
    rain = _year(2001, lambda d: float(d.timetuple().tm_yday % 21))  # 0..20 mm
    wet = [v for v in rain.values() if v >= 1.0]
    p95 = ix.wet_day_percentile(rain, range(2001, 2002), 1.0, 95.0)
    assert p95 == pytest.approx(ix.percentile_linear(wet, 95.0))
    assert 0.0 not in wet  # dry days are excluded from the sample
    rain[date(2001, 6, 1)] = None
    assert ix.wet_day_percentile(rain, range(2001, 2002), 1.0, 95.0) is None  # partial baseline
    assert ix.wet_day_percentile(rain, range(2001, 2003), 1.0, 95.0) is None  # missing year


def test_climatology_requires_every_year_of_the_baseline():
    daily = {**_year(2001, lambda d: 1.0), **_year(2002, lambda d: 2.0)}
    months = to_monthly(daily, "sum")
    clim = ix.monthly_climatology(months, range(2001, 2003))
    assert clim[0] == pytest.approx((31 + 62) / 2) and clim[1] == pytest.approx((28 + 56) / 2)
    assert ix.annual_mean_of_totals(months, range(2001, 2003)) == pytest.approx((365 + 730) / 2)
    assert ix.monthly_climatology(months, range(2001, 2004)) == [None] * 12
    assert ix.annual_mean_of_totals(months, range(2000, 2003)) is None


# --- parameters from site.yaml ----------------------------------------------------------------


def test_index_params_from_site_yaml(tmp_path):
    f = tmp_path / "site.yaml"
    assert ix.load_index_params(f) == (ix.IndexParams(), frozenset())  # no file: defaults
    f.write_text("id: x\nindices:\n  heat_tmax_c: 32\n  gdd_base_c: 8.5\n", encoding="utf-8")
    params, site_set = ix.load_index_params(f)
    assert (params.heat_tmax_c, params.gdd_base_c, params.frost_tmin_c) == (32.0, 8.5, 0.0)
    assert site_set == {"heat_tmax_c", "gdd_base_c"}
    f.write_text("indices:\n  heat_threshold: 32\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="unknown"):
        ix.load_index_params(f)
    f.write_text("indices:\n  heat_tmax_c: true\n", encoding="utf-8")
    with pytest.raises(PipelineError, match="number"):
        ix.load_index_params(f)
    with pytest.raises(PipelineError):
        ix.IndexParams(extreme_percentile=100)


# --- pipeline: daily before monthly, provenance, climatology ---------------------------------


def synthetic_raw(years: range) -> power.PowerRaw:
    """Two full years, constant weather except rain; every input of ET0 present."""
    days = [d for y in years for d in _year(y, lambda d: None)]
    const = {"T2M": 22.0, "T2M_MAX": 30.0, "T2M_MIN": 14.0, "T2MDEW": 15.0, "RH2M": 70.0,
             "WS2M": 2.0, "ALLSKY_SFC_SW_DWN": 20.0, "PS": 101.3, "GWETTOP": 0.5,
             "GWETROOT": 0.6, "GWETPROF": 0.55, "EVLAND": 3.0}  # fmt: skip
    daily = {code: dict.fromkeys(days, v) for code, v in const.items()}
    daily["PRECTOTCORR"] = {d: float(d.timetuple().tm_yday % 21) for d in days}
    p = power.PARAMS_BY_CODE
    return power.PowerRaw(
        lat=DEV.lat, lon=DEV.lon, elevation_m=10.0, api_name="POWER Daily API",
        api_version="v2.10.3", upstream_sources=("MERRA2",), time_standard="LST",
        url=power.POWER_URL + "?community=AG", accessed_at="2026-11-14T14:00:00-03:00",
        native_units={c: p[c].native_unit for c in p}, longnames={c: c for c in p}, daily=daily,
    )  # fmt: skip


@pytest.fixture
def full():
    params = ix.IndexParams(heat_tmax_c=29.0, baseline_start_year=2001, baseline_end_year=2002)
    raw = synthetic_raw(range(2001, 2003))
    return raw, params, build_all(DEV, raw, params)


def test_indices_are_counted_daily_then_aggregated(full):
    raw, params, (bundle, registry, indices) = full
    s = {x.variable_key: x for x in bundle.series}
    assert s["heat_days"].points[0].v == 31.0  # Tmax 30 > 29 every day of January
    assert s["heat_days"].aggregation.temporal == "count" and s["heat_days"].unit == "days"
    assert s["frost_days"].points[0].v == 0.0
    assert s["growing_degree_days"].points[1].v == pytest.approx(12.0 * 28)
    assert s["growing_degree_days"].unit == "degC_d"
    wet = [v for v in raw.daily["PRECTOTCORR"].values() if v >= 1.0]
    p95 = ix.percentile_linear(wet, 95.0)
    jan = [v for d, v in raw.daily["PRECTOTCORR"].items() if (d.year, d.month) == (2001, 1)]
    assert s["extreme_precip_days"].points[0].v == sum(1 for v in jan if v > p95)
    assert s["extreme_precip_total"].points[0].v == pytest.approx(
        round(sum(v for v in jan if v > p95), 1)
    )
    et0, rain = s["et0"].points[0].v, s["precip"].points[0].v
    assert s["water_deficit"].points[0].v == pytest.approx(et0 - rain, abs=0.11)
    for key in ("evap_land_modeled", "soil_wetness_profile_modeled"):
        assert s[key].data_type == "modeled"
    assert s["evap_land_modeled"].points[0].v == pytest.approx(93.0)  # 3 mm/d x 31 d, sum


def test_index_provenance_is_computed_with_parameters_and_lineage(full):
    _, params, (bundle, registry, indices) = full
    for s in bundle.series:
        rec = registry.records[s.provenance_id]
        assert rec.data_type == s.data_type
        if s.variable_key in ("heat_days", "frost_days", "growing_degree_days", "water_deficit",
                              "extreme_precip_days", "extreme_precip_total"):  # fmt: skip
            assert rec.data_type == "computed" and rec.method.doc_anchor and rec.inputs
            assert set(rec.inputs) <= set(registry.records)
    heat = registry.records["prov:computed:dev-floripa:heat_days:daily"]
    assert heat.method.parameters == {"tmax_threshold_degC": 29.0, "comparison": ">"}
    assert any("generic default" in lim.en for lim in heat.limitations)  # not set by the site
    ext = registry.records["prov:computed:dev-floripa:extreme_precip_days:daily"]
    assert "prov:computed:dev-floripa:precip_p95:2001_2002" in ext.inputs
    deficit = registry.records["prov:computed:dev-floripa:water_deficit:daily"]
    assert "prov:computed:dev-floripa:et0:daily" in deficit.inputs


def test_climate_indices_document(full):
    _, params, (bundle, registry, indices) = full
    ClimateIndices.model_validate(indices.model_dump(mode="json"))
    metrics = {m.id: m for m in indices.metrics}
    heat = metrics["heat_days_gt29c.annual_mean.2001_2002"]
    assert heat.value == 365.0 and heat.unit == "days" and heat.index_key == "heat_days"
    assert metrics["gdd_base10c.annual_mean.2001_2002"].value == pytest.approx(12.0 * 365)
    assert "precip_p95_wet_days.2001_2002" in metrics
    prof = {p.id: p for p in indices.profiles}["heat_days_gt29c.by_month.2001_2002"]
    assert prof.values[:2] == [31.0, 28.0] and len(prof.values) == 12
    assert prof.period.start == "2001-01-01" and prof.period.end == "2002-12-31"
    for item in [*indices.metrics, *indices.profiles]:
        rec = registry.records[item.provenance_id]
        assert rec.data_type == "computed" and set(rec.inputs) <= set(registry.records)


def test_site_set_threshold_drops_placeholder_limitation():
    params = ix.IndexParams(heat_tmax_c=29.0, baseline_start_year=2001, baseline_end_year=2002)
    _, registry, _ = build_all(DEV, synthetic_raw(range(2001, 2003)), params,
                               frozenset({"heat_tmax_c"}))  # fmt: skip
    heat = registry.records["prov:computed:dev-floripa:heat_days:daily"]
    assert not any("generic default" in lim.en for lim in heat.limitations)


def test_short_record_without_baseline_has_no_extremes_and_no_climatology():
    raw = power.parse(json.loads(FIXTURE.read_text(encoding="utf-8")), lat=DEV.lat, lon=DEV.lon)
    bundle, registry, indices = build_all(DEV, raw)  # 2024 only; baseline 1991-2020 absent
    keys = {s.variable_key for s in bundle.series}
    assert {"heat_days", "frost_days", "growing_degree_days", "water_deficit"} <= keys
    assert not keys & {"extreme_precip_days", "extreme_precip_total"}
    assert indices.metrics == [] and indices.profiles == []
    SeriesBundle.model_validate(bundle.model_dump(mode="json"))
    ProvenanceRegistry.model_validate(registry.model_dump(mode="json"))


def test_missing_input_day_makes_the_index_month_a_gap(full):
    raw, params, _ = full
    raw.daily["T2M_MAX"][date(2001, 3, 10)] = None
    bundle, _, indices = build_all(DEV, raw, params)
    s = {x.variable_key: x for x in bundle.series}
    assert s["heat_days"].points[2].v is None and s["heat_days"].points[2].q == "gap"
    assert s["growing_degree_days"].points[2].v is None
    prof = {p.id: p for p in indices.profiles}["heat_days_gt29c.by_month.2001_2002"]
    assert prof.values[2] is None  # March of 2001 is missing: no climatology for March
    assert "heat_days_gt29c.annual_mean.2001_2002" not in {m.id for m in indices.metrics}
