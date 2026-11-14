# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Stage orchestration. Today: the NASA POWER layer (Story 2.2) and the climate indices (#22),
concept-agnostic and site-agnostic.

fetch (cache) -> daily ET0 and daily indices -> monthly series (ADR-3) -> baseline climatology
-> FR19 provenance -> validated JSON (series.json, provenance.json, indices.json).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fieldshift.contracts import (
    SCHEMA_VERSION,
    ClimateIndices,
    LocalizedText,
    Metric,
    MonthlyProfile,
    Period,
    Provenance,
    ProvenanceRegistry,
    SeriesBundle,
    TimeSeries,
)
from fieldshift.contracts.timeseries import KnownGap, SeriesAggregation, SeriesCoverage, SeriesPoint
from fieldshift.harmonize.monthly import MonthValue, gap_runs, to_monthly
from fieldshift.indices import climate as ix
from fieldshift.indices.et0 import actual_vapour_pressure_from_dewpoint, et0_fao56_daily
from fieldshift.io.rounding import round_value
from fieldshift.io.store import write_model
from fieldshift.provenance import indices as pix
from fieldshift.provenance.power import et0_prov_id, et0_record, power_prov_id, power_record
from fieldshift.sites import SitePoint
from fieldshift.sources import power

GAP_PARTIAL = LocalizedText(
    en="At least one day of the month is missing in the NASA POWER record (or in an input of a "
    "computed series); the month is left null."
)
GAP_EMPTY = LocalizedText(
    en="No daily values in the NASA POWER record for these months (or in an input of a computed "
    "series)."
)


def _gap_reason(months: list[MonthValue], start: str, end: str) -> LocalizedText:
    run = [m for m in months if start <= m.month <= end]
    return GAP_EMPTY if all(m.valid_days == 0 for m in run) else GAP_PARTIAL


@dataclass(frozen=True)
class PowerOutputs:
    series_path: Path
    provenance_path: Path
    indices_path: Path
    bundle: SeriesBundle
    registry: ProvenanceRegistry
    indices: ClimateIndices


def daily_et0(raw: power.PowerRaw, lat: float) -> dict[date, float | None]:
    """FAO-56 ET0 per day; a day missing any input stays `None` (never filled)."""
    d = raw.daily
    out: dict[date, float | None] = {}
    for day in sorted(d["T2M_MAX"]):
        tmax, tmin, tdew = d["T2M_MAX"][day], d["T2M_MIN"].get(day), d["T2MDEW"].get(day)
        u2, rs, ps = d["WS2M"].get(day), d["ALLSKY_SFC_SW_DWN"].get(day), d["PS"].get(day)
        if None in (tmax, tmin, tdew, u2, rs, ps):
            out[day] = None
            continue
        out[day] = et0_fao56_daily(
            tmin_c=tmin, tmax_c=tmax, ea_kpa=actual_vapour_pressure_from_dewpoint(tdew),
            wind_2m=u2, rs=rs, pressure_kpa=ps, lat_deg=lat, elevation_m=raw.elevation_m, day=day,
        )  # fmt: skip
    return out


def monthly_series(
    *,
    site_id: str,
    series_id: str,
    variable_key: str,
    label: str,
    unit: str,
    how: str,
    data_type: str,
    provenance_id: str,
    months: list[MonthValue],
) -> TimeSeries:
    points = [
        SeriesPoint(t=m.month, v=round_value(m.value, unit), q="ok" if m.complete else "gap")
        for m in months
    ]
    ok = sum(1 for m in months if m.complete)
    return TimeSeries(
        id=series_id,
        site_id=site_id,
        variable_key=variable_key,
        label=LocalizedText(en=label),
        unit=unit,
        frequency="monthly",
        aggregation=SeriesAggregation(temporal=how, spatial="containing_pixel"),
        data_type=data_type,
        provenance_id=provenance_id,
        points=points,
        coverage=SeriesCoverage(
            first=months[0].month,
            last=months[-1].month,
            valid_pct=round(100 * ok / len(months), 1),
            known_gaps=[
                KnownGap(start=a, end=b, reason=_gap_reason(months, a, b))
                for a, b in gap_runs(months)
            ],
        ),
    )


def build_power(
    site: SitePoint, raw: power.PowerRaw, et0_daily: dict[date, float | None] | None = None
) -> tuple[SeriesBundle, ProvenanceRegistry]:
    """Pure step: parsed POWER response -> validated contracts (no I/O)."""
    series: list[TimeSeries] = []
    records = {}
    for p in power.PARAMS:
        rec = power_record(site, raw, p)
        records[rec.id] = rec
        series.append(
            monthly_series(
                site_id=site.id,
                series_id=f"power.{p.variable_key}.monthly_{p.aggregator}",
                variable_key=p.variable_key,
                label=p.label,
                unit=p.monthly_unit,
                how=p.aggregator,
                data_type="modeled",
                provenance_id=power_prov_id(site.id, p.code),
                months=to_monthly(raw.daily[p.code], p.aggregator),
            )
        )
    et0 = et0_record(site, raw)
    records[et0.id] = et0
    series.append(
        monthly_series(
            site_id=site.id,
            series_id="fao56.et0.monthly_sum",
            variable_key="et0",
            label="Reference evapotranspiration ET0 (FAO-56), monthly total",
            unit="mm",
            how="sum",
            data_type="computed",
            provenance_id=et0_prov_id(site.id),
            months=to_monthly(daily_et0(raw, site.lat) if et0_daily is None else et0_daily, "sum"),
        )
    )
    bundle = SeriesBundle(schema_version=SCHEMA_VERSION, site_id=site.id, series=series)
    registry = ProvenanceRegistry(schema_version=SCHEMA_VERSION, site_id=site.id, records=records)
    missing = {s.provenance_id for s in series} - set(registry.records)
    if missing:  # VL1, data layer: every series points to an existing record
        raise ValueError(f"series without provenance record: {sorted(missing)}")
    return bundle, registry


def _check_lineage(refs: set[str], records: dict[str, Provenance]) -> None:
    """VL1, data layer: every reference and every computed input points to an existing record."""
    missing = refs - set(records)
    for rec in records.values():
        missing |= set(rec.inputs) - set(records)
    if missing:
        raise ValueError(f"references without provenance record: {sorted(missing)}")


def daily_indices(
    raw: power.PowerRaw, et0_daily: dict[date, float | None], params: ix.IndexParams
) -> tuple[dict[str, dict[date, float | None]], float | None]:
    """Daily values of every index (ADR-3: on daily data, before aggregation) + the P95 threshold.

    The extreme-precipitation indices are absent when the baseline is not fully covered.
    """
    d, p = raw.daily, params
    tmax, tmin, rain = d["T2M_MAX"], d["T2M_MIN"], d["PRECTOTCORR"]
    out = {
        "heat_days": ix.daily_map(tmax, fn=lambda t: ix.heat_day(t, p.heat_tmax_c)),
        "frost_days": ix.daily_map(tmin, fn=lambda t: ix.frost_day(t, p.frost_tmin_c)),
        "growing_degree_days": ix.daily_map(
            tmax, tmin, fn=lambda a, b: ix.growing_degree_days(a, b, p.gdd_base_c)
        ),
        "water_deficit": ix.daily_map(et0_daily, rain, fn=ix.water_deficit),
    }
    p95 = ix.wet_day_percentile(rain, p.baseline_years, p.wet_day_mm, p.extreme_percentile)
    if p95 is not None:
        out["extreme_precip_days"] = ix.daily_map(
            rain, fn=lambda r: None if r is None else float(r > p95)
        )
        out["extreme_precip_total"] = ix.daily_map(
            rain, fn=lambda r: None if r is None else (r if r > p95 else 0.0)
        )
    return out, p95


def _id_base(key: str, p: ix.IndexParams) -> str:
    return {
        "heat_days": f"heat_days_gt{pix.tag(p.heat_tmax_c)}c",
        "frost_days": f"frost_days_le{pix.tag(p.frost_tmin_c)}c",
        "growing_degree_days": f"gdd_base{pix.tag(p.gdd_base_c)}c",
        "extreme_precip_days": f"extreme_precip_days_gt_p{pix.tag(p.extreme_percentile)}",
        "extreme_precip_total": f"extreme_precip_total_gt_p{pix.tag(p.extreme_percentile)}",
    }.get(key, key)


def build_indices(
    site: SitePoint,
    raw: power.PowerRaw,
    et0_daily: dict[date, float | None],
    params: ix.IndexParams,
    site_set: frozenset[str] = frozenset(),
) -> tuple[list[TimeSeries], dict[str, Provenance], list[Metric], list[MonthlyProfile]]:
    """Pure step: monthly index series, their records, and the baseline climatology."""
    p = params
    daily, p95 = daily_indices(raw, et0_daily, p)
    specs = pix.daily_indices(p)
    series: list[TimeSeries] = []
    records: dict[str, Provenance] = {}
    # (key, title, unit of the monthly value, monthly values, source record) for climatology
    clim_inputs: list[tuple[str, str, str, list[MonthValue], Provenance]] = []

    if p95 is not None:
        rec = pix.p95_record(site, raw, p)
        records[rec.id] = rec
    for key, values in daily.items():
        spec = specs[key]
        rec = pix.daily_index_record(site, raw, spec, p, site_set)
        records[rec.id] = rec
        months = to_monthly(values, "sum")  # counts and totals: monthly sum of daily values
        kind = "count" if spec.temporal == "count" else "total"
        series.append(
            monthly_series(
                site_id=site.id,
                series_id=f"indices.{key}.monthly_{spec.temporal}",
                variable_key=key,
                label=f"{spec.title}, monthly {kind}",
                unit=spec.monthly_unit,
                how=spec.temporal,
                data_type="computed",
                provenance_id=rec.id,
                months=months,
            )
        )
        clim_inputs.append((key, spec.title, spec.monthly_unit, months, rec))

    et0_rec = et0_record(site, raw)
    et0_title = "Reference evapotranspiration ET0 (FAO-56)"
    clim_inputs.append(("et0", et0_title, "mm", to_monthly(et0_daily, "sum"), et0_rec))

    period = Period(start=f"{p.baseline_start_year}-01-01", end=f"{p.baseline_end_year}-12-31")
    span = f"{p.baseline_start_year}–{p.baseline_end_year}"
    metrics: list[Metric] = []
    profiles: list[MonthlyProfile] = []
    for key, title, unit, months, src in clim_inputs:
        common = dict(
            site=site, raw=raw, key=key, title=title, code=src.variable.code, unit=unit,
            source_id=src.id, source_period_unit=unit, method=src.method, refs=list(src.refs),
            resolution=src.spatial.resolution, params=p,
            extra_limitations=pix.placeholder_limitations(key, p, site_set),
        )  # fmt: skip
        values = [round_value(v, unit) for v in ix.monthly_climatology(months, p.baseline_years)]
        if any(v is not None for v in values):
            rec = pix.clim_record(kind="by_month", **common)
            records[rec.id] = rec
            profiles.append(
                MonthlyProfile(
                    id=f"{_id_base(key, p)}.by_month.{p.baseline_tag}",
                    label=LocalizedText(en=f"{title}, mean by calendar month {span}"),
                    unit=unit,
                    values=values,
                    period=period,
                    data_type="computed",
                    provenance_id=rec.id,
                    index_key=key,
                )  # fmt: skip
            )
        annual = ix.annual_mean_of_totals(months, p.baseline_years)
        if annual is not None:
            rec = pix.clim_record(kind="annual_mean", **common)
            records[rec.id] = rec
            metrics.append(
                Metric(
                    id=f"{_id_base(key, p)}.annual_mean.{p.baseline_tag}",
                    label=LocalizedText(en=f"{title}, annual mean {span}"),
                    value=round_value(annual, unit),
                    unit=unit,
                    period=period,
                    data_type="computed",
                    provenance_id=rec.id,
                    index_key=key,
                )  # fmt: skip
            )
    if p95 is not None:
        metrics.append(
            Metric(
                id=f"precip_p{pix.tag(p.extreme_percentile)}_wet_days.{p.baseline_tag}",
                label=LocalizedText(
                    en=f"P{pix.num(p.extreme_percentile)} of daily precipitation on wet days "
                    f"(>= {pix.num(p.wet_day_mm)} mm), {span}"
                ),
                value=round_value(p95, "mm/d"),
                unit="mm/d",
                period=period,
                data_type="computed",
                provenance_id=pix.p95_prov_id(site.id, p),
                index_key="extreme_precip_threshold",
            )  # fmt: skip
        )
    return series, records, metrics, profiles


def build_all(
    site: SitePoint,
    raw: power.PowerRaw,
    params: ix.IndexParams | None = None,
    site_set: frozenset[str] = frozenset(),
) -> tuple[SeriesBundle, ProvenanceRegistry, ClimateIndices]:
    """Pure step: POWER layer + climate indices, cross-checked (VL1, data layer)."""
    params = params or ix.IndexParams()
    et0_daily = daily_et0(raw, site.lat)
    bundle, registry = build_power(site, raw, et0_daily)
    series, records, metrics, profiles = build_indices(site, raw, et0_daily, params, site_set)
    bundle = SeriesBundle(
        schema_version=SCHEMA_VERSION, site_id=site.id, series=[*bundle.series, *series]
    )
    registry = ProvenanceRegistry(
        schema_version=SCHEMA_VERSION, site_id=site.id, records={**registry.records, **records}
    )
    indices = ClimateIndices(
        schema_version=SCHEMA_VERSION, site_id=site.id, metrics=metrics, profiles=profiles
    )
    refs = {s.provenance_id for s in bundle.series}
    refs |= {m.provenance_id for m in metrics} | {pr.provenance_id for pr in profiles}
    _check_lineage(refs, registry.records)
    return bundle, registry, indices


def site_yaml_path(site: SitePoint, data_dir: Path) -> Path | None:
    """Real sites read their index thresholds from site.yaml; DEV points use the defaults."""
    return None if site.dev else data_dir / "sites" / site.id / "input" / "site.yaml"


def run_power(
    site: SitePoint,
    *,
    data_dir: Path,
    start: date,
    end: date,
    offline: bool = False,
    refresh: bool = False,
) -> PowerOutputs:
    raw = power.fetch(
        site.id, site.lat, site.lon, start, end,
        cache_root=data_dir / "cache", offline=offline, refresh=refresh,
    )  # fmt: skip
    params, site_set = ix.load_index_params(site_yaml_path(site, data_dir))
    bundle, registry, indices = build_all(site, raw, params, site_set)
    out = site.output_dir(data_dir)
    return PowerOutputs(
        series_path=write_model(bundle, out / "series.json"),
        provenance_path=write_model(registry, out / "provenance.json"),
        indices_path=write_model(indices, out / "indices.json"),
        bundle=bundle,
        registry=registry,
        indices=indices,
    )
