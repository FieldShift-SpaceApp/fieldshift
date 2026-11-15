# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""`fieldshift complements --site <id>`: the four complement documents of a site.

Reads data/sites/<id>/input/ (forecast table, replay YAML, IBGE wheat files, rain gauge, satellite
summaries), data/cache/noaa/ (ONI), data/cache/power/<id>/ (NASA POWER) and
data/cache/power-imerg/<id>/ (GPM IMERG via POWER) and data/cache/now-2026/ (POWER and IMERG for the
current season); writes forecast-scorecard.json, replay.json, bare-soil-calendar.json,
enso-rain-signal.json and now-2026.json, and merges their provenance records into
output/provenance.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from fieldshift.complements import now as now_mod
from fieldshift.complements import provenance as cp
from fieldshift.complements.baresoil import build_bare_soil
from fieldshift.complements.oni import SEASONS, OniFile, load_oni
from fieldshift.complements.rain_signal import (
    FIRST_YEAR,
    GAUGE_INPUT,
    LAST_YEAR,
    build_rain_signal,
    load_gauge,
    window_days,
)
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
    "now": now_mod.FILE,
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


def history_days() -> list[date]:
    """Every day the rain documents read from the POWER history: September-November of
    FIRST_YEAR..LAST_YEAR of the heavy-rain signal (the now-2026 climatology is inside it)."""
    return [d for y in range(FIRST_YEAR, LAST_YEAR + 1) for d in window_days(y)]


def power_rain(data_dir: Path, site_id: str, lat: float, lon: float) -> dict:
    """PRECTOTCORR of the main POWER cache (`fetch power`), the history of every rain document.

    The cache is chosen by what each file holds, never by its name: a cache counts only when
    PRECTOTCORR has a value on every day of `history_days()`. Among those, the one with the most
    valid days wins; two equally large caches must agree on every needed day, else it fails.
    """
    folder = data_dir / "cache" / "power" / site_id
    caches = sorted(folder.glob("daily_*.json"))
    if not caches:
        raise PipelineError(f"no NASA POWER cache in {folder}; run `fieldshift fetch power`")
    need = history_days()
    full: list[tuple[int, Path, dict]] = []
    short: list[str] = []
    for path in caches:
        rain = power.parse(json.loads(path.read_text(encoding="utf-8")), lat=lat, lon=lon).daily[
            "PRECTOTCORR"
        ]
        missing = [d for d in need if rain.get(d) is None]
        if missing:
            short.append(f"{path} ({len(missing)} days missing, first {missing[0]})")
        else:
            full.append((sum(1 for v in rain.values() if v is not None), path, rain))
    if not full:
        raise PipelineError(
            f"no NASA POWER cache covers September-November {FIRST_YEAR}-{LAST_YEAR} for "
            f"{site_id}: {'; '.join(short)}"
        )
    best = max(n for n, _, _ in full)
    top = [(p, r) for n, p, r in full if n == best]
    for p, r in top[1:]:
        if any(r[d] != top[0][1][d] for d in need):
            raise PipelineError(
                f"NASA POWER caches {top[0][0]} and {p} cover the same days with different "
                "PRECTOTCORR values; keep one of them"
            )
    return top[0][1]


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
    history = power_rain(data_dir, site_id, site.lat, site.lon)
    rain, recs = build_rain_signal(
        site_id,
        history,
        imerg,
        load_gauge(inp / GAUGE_INPUT),
        oni,
    )
    records.update({r.id: r for r in recs})
    now_cache = data_dir / "cache" / "now-2026"
    now_args = (site_id, site.lat, site.lon, now_mod.START, now_mod.CUTOFF)
    now_doc, recs = now_mod.build_now(
        site,
        power.fetch(*now_args, cache_root=now_cache, offline=offline),
        history,
        power_imerg.fetch(*now_args, cache_root=now_cache, offline=offline),
        imerg,
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
        "now": write_model(now_doc, out / FILES["now"]),
    }
    return ComplementOutputs(
        paths=paths, provenance_path=write_model(merged, provenance_path), records=len(records)
    )
