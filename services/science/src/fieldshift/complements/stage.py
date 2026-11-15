# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""`fieldshift complements --site <id>`: the four complement documents of a site.

Reads data/sites/<id>/input/ (forecast table, replay YAML, IBGE wheat files, rain gauge, satellite
summaries), data/cache/noaa/ (ONI), data/cache/power/<id>/ (NASA POWER) and
data/cache/power-imerg/<id>/ (GPM IMERG via POWER); writes forecast-scorecard.json, replay.json,
bare-soil-calendar.json and enso-rain-signal.json, and merges their provenance records into
output/provenance.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fieldshift.complements import provenance as cp
from fieldshift.complements.baresoil import build_bare_soil
from fieldshift.complements.oni import SEASONS, OniFile, load_oni
from fieldshift.complements.rain_signal import GAUGE_INPUT, build_rain_signal, load_gauge
from fieldshift.complements.replay import build_replay
from fieldshift.complements.scorecard import INPUT as FORECASTS
from fieldshift.complements.scorecard import build_scorecard, load_forecasts
from fieldshift.contracts import SCHEMA_VERSION, Period, ProvenanceRegistry
from fieldshift.errors import PipelineError
from fieldshift.io.store import write_model
from fieldshift.rotation.stage import merge_registry, site_dir
from fieldshift.sites import resolve_site
from fieldshift.sources import power, power_imerg

FILES = {
    "scorecard": "forecast-scorecard.json",
    "replay": "replay.json",
    "bare_soil": "bare-soil-calendar.json",
    "rain": "enso-rain-signal.json",
}
IMERG_END = date(2025, 12, 31)
FORECAST_ACCESSED_AT = "2026-11-14T19:46:32-03:00"  # start of the archive download (script log)


@dataclass(frozen=True)
class ComplementOutputs:
    paths: dict[str, Path]
    provenance_path: Path
    records: int


def oni_period(oni: OniFile) -> Period:
    def bounds(key: tuple[str, int]) -> tuple[date, date]:
        k, y = SEASONS.index(key[0]), key[1]
        first = date(y - 1, 12, 1) if k == 0 else date(y, k, 1)
        last_month, last_year = (k + 2, y) if k + 2 <= 12 else (k + 2 - 12, y + 1)
        nxt = date(last_year + (last_month == 12), last_month % 12 + 1, 1)
        return first, date.fromordinal(nxt.toordinal() - 1)

    keys = sorted(oni.values, key=lambda k: (k[1], SEASONS.index(k[0])))
    return Period(start=bounds(keys[0])[0].isoformat(), end=bounds(keys[-1])[1].isoformat())


def power_rain(data_dir: Path, site_id: str, lat: float, lon: float) -> dict:
    caches = sorted((data_dir / "cache" / "power" / site_id).glob("daily_*.json"))
    if not caches:
        raise PipelineError(f"no NASA POWER cache for {site_id}; run `fieldshift fetch power`")
    raw = power.parse(json.loads(caches[-1].read_text(encoding="utf-8")), lat=lat, lon=lon)
    return raw.daily["PRECTOTCORR"]


def run_complements(site_id: str, *, data_dir: Path, offline: bool = False) -> ComplementOutputs:
    site = resolve_site(site_id, data_dir)
    base = site_dir(data_dir, site_id)
    inp, out = base / "input", base / "output"
    oni = load_oni(data_dir / "cache" / "noaa")
    records = {
        cp.oni_prov_id(site_id): cp.oni_record(site_id, oni.url, oni.accessed_at, oni_period(oni))
    }

    card, recs = build_scorecard(
        site_id, load_forecasts(inp / FORECASTS), oni, FORECAST_ACCESSED_AT
    )
    records.update({r.id: r for r in recs})
    replay, recs = build_replay(site_id, inp)
    records.update({r.id: r for r in recs})
    calendar, recs = build_bare_soil(site_id, inp)
    records.update({r.id: r for r in recs})
    imerg = power_imerg.fetch(
        site_id,
        site.lat,
        site.lon,
        power_imerg.IMERG_START,
        IMERG_END,
        cache_root=data_dir / "cache",
        offline=offline,
    )
    rain, recs = build_rain_signal(
        site_id,
        power_rain(data_dir, site_id, site.lat, site.lon),
        imerg,
        load_gauge(inp / GAUGE_INPUT),
        oni,
    )
    records.update({r.id: r for r in recs})

    registry = ProvenanceRegistry(schema_version=SCHEMA_VERSION, site_id=site_id, records=records)
    provenance_path = out / "provenance.json"
    merged = merge_registry(provenance_path, registry)
    missing = {i for r in merged.records.values() for i in r.inputs} - set(merged.records)
    if missing:  # VL1: every computed input exists (e.g. the POWER records of `fetch power`)
        raise PipelineError(f"provenance inputs without a record: {sorted(missing)}")
    paths = {
        "scorecard": write_model(card, out / FILES["scorecard"]),
        "replay": write_model(replay, out / FILES["replay"]),
        "bare_soil": write_model(calendar, out / FILES["bare_soil"]),
        "rain": write_model(rain, out / FILES["rain"]),
    }
    return ComplementOutputs(
        paths=paths, provenance_path=write_model(merged, provenance_path), records=len(records)
    )
