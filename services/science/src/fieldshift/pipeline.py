# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Stage orchestration. Today: the NASA POWER layer (Story 2.2), concept-agnostic and site-agnostic.

fetch (cache) -> daily ET0 -> monthly series (ADR-3) -> FR19 provenance -> validated JSON.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fieldshift.contracts import (
    SCHEMA_VERSION,
    LocalizedText,
    ProvenanceRegistry,
    SeriesBundle,
    TimeSeries,
)
from fieldshift.contracts.timeseries import KnownGap, SeriesAggregation, SeriesCoverage, SeriesPoint
from fieldshift.harmonize.monthly import MonthValue, gap_runs, to_monthly
from fieldshift.indices.et0 import actual_vapour_pressure_from_dewpoint, et0_fao56_daily
from fieldshift.io.rounding import round_value
from fieldshift.io.store import write_model
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
    bundle: SeriesBundle
    registry: ProvenanceRegistry


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


def build_power(site: SitePoint, raw: power.PowerRaw) -> tuple[SeriesBundle, ProvenanceRegistry]:
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
            months=to_monthly(daily_et0(raw, site.lat), "sum"),
        )
    )
    bundle = SeriesBundle(schema_version=SCHEMA_VERSION, site_id=site.id, series=series)
    registry = ProvenanceRegistry(schema_version=SCHEMA_VERSION, site_id=site.id, records=records)
    missing = {s.provenance_id for s in series} - set(registry.records)
    if missing:  # VL1, data layer: every series points to an existing record
        raise ValueError(f"series without provenance record: {sorted(missing)}")
    return bundle, registry


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
    bundle, registry = build_power(site, raw)
    out = site.output_dir(data_dir)
    return PowerOutputs(
        series_path=write_model(bundle, out / "series.json"),
        provenance_path=write_model(registry, out / "provenance.json"),
        bundle=bundle,
        registry=registry,
    )
