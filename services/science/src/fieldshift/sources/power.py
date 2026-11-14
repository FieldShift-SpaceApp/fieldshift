# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""NASA POWER daily point API (ADR-2): fetch with retry/backoff, raw cache, parsing.

The CI never calls this module's network path: tests use recorded responses and the pipeline
reads `data/cache/` with `--offline`.
"""

from __future__ import annotations

import json
import logging
import math
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

import httpx

from fieldshift.config import LOCAL_UTC_OFFSET_HOURS
from fieldshift.errors import LayerError, PipelineError

log = logging.getLogger(__name__)

POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
COMMUNITY = "AG"
POWER_START = date(1981, 1, 1)
TERMS_URL = "https://power.larc.nasa.gov/docs/referencing/"
DOCS_URL = "https://power.larc.nasa.gov/docs/services/api/temporal/daily/"

# Grid of the upstream products (POWER Methodology page, 2026-11-14): meteorology ½° × ⅝°
# (MERRA-2), radiation 1° × 1° (CERES SYN1deg).
RES_METEO = "0.5° lat × 0.625° lon (MERRA-2 grid)"
RES_SOLAR = "1° × 1° (CERES SYN1deg grid)"

MAX_ATTEMPTS = 4
TIMEOUT_S = 180.0
RETRY_STATUS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class PowerParam:
    code: str
    variable_key: str  # TimeSeries.VariableKey
    label: str  # English label of the monthly series
    native_unit: str  # as the API reports it for community AG
    unit: str  # canonical unit of the daily value (ADR-7)
    aggregator: Literal["mean", "sum"]  # ADR-3
    monthly_unit: str  # canonical unit of the monthly value
    resolution: str
    upstream: str


# Codes confirmed against the live API (2026-11-14, Florianópolis dev point): names and units below
# are the ones the response header returned. EVPTRNS is deliberately absent (see README).
PARAMS: tuple[PowerParam, ...] = (
    PowerParam("T2M", "air_temp_mean", "Mean air temperature at 2 m", "C", "degC", "mean",
               "degC", RES_METEO, "MERRA-2"),
    PowerParam("T2M_MAX", "air_temp_max", "Daily maximum air temperature at 2 m", "C", "degC",
               "mean", "degC", RES_METEO, "MERRA-2"),
    PowerParam("T2M_MIN", "air_temp_min", "Daily minimum air temperature at 2 m", "C", "degC",
               "mean", "degC", RES_METEO, "MERRA-2"),
    PowerParam("T2MDEW", "dewpoint", "Dew/frost point at 2 m", "C", "degC", "mean", "degC",
               RES_METEO, "MERRA-2"),
    PowerParam("RH2M", "rel_humidity", "Relative humidity at 2 m", "%", "%", "mean", "%",
               RES_METEO, "MERRA-2"),
    PowerParam("WS2M", "wind_2m", "Wind speed at 2 m", "m/s", "m/s", "mean", "m/s", RES_METEO,
               "MERRA-2"),
    PowerParam("ALLSKY_SFC_SW_DWN", "solar_rad", "All-sky surface shortwave downward irradiance",
               "MJ/m^2/day", "MJ/m2/d", "mean", "MJ/m2/d", RES_SOLAR, "CERES SYN1deg"),
    PowerParam("PRECTOTCORR", "precip", "Precipitation (bias-corrected)", "mm/day", "mm/d",
               "sum", "mm", RES_METEO, "MERRA-2"),
    PowerParam("PS", "surface_pressure", "Surface pressure", "kPa", "kPa", "mean", "kPa",
               RES_METEO, "MERRA-2"),
    PowerParam("GWETTOP", "soil_wetness_top_modeled", "Surface soil wetness (modeled)", "1", "1",
               "mean", "1", RES_METEO, "MERRA-2"),
    PowerParam("GWETROOT", "soil_wetness_root_modeled", "Root zone soil wetness (modeled)", "1",
               "1", "mean", "1", RES_METEO, "MERRA-2"),
)  # fmt: skip

PARAMS_BY_CODE = {p.code: p for p in PARAMS}


@dataclass(frozen=True)
class PowerRaw:
    """Parsed POWER response. Daily values are `None` where the API sent its fill value."""

    lat: float
    lon: float
    elevation_m: float
    api_name: str
    api_version: str
    upstream_sources: tuple[str, ...]
    time_standard: str
    url: str
    accessed_at: str  # RFC 3339 with the local offset
    native_units: dict[str, str]
    longnames: dict[str, str]
    daily: dict[str, dict[date, float | None]] = field(repr=False)

    @property
    def first_day(self) -> date:
        return min(min(s) for s in self.daily.values())

    @property
    def last_day(self) -> date:
        return max(max(s) for s in self.daily.values())


def local_now() -> datetime:
    return datetime.now(UTC).astimezone(timezone(timedelta(hours=LOCAL_UTC_OFFSET_HOURS)))


def default_end(today: date | None = None) -> date:
    """Last day of the previous calendar month: complete months only (POWER has a few days' lag)."""
    today = today or local_now().date()
    return today.replace(day=1) - timedelta(days=1)


def build_query(lat: float, lon: float, start: date, end: date) -> dict[str, str]:
    return {
        "parameters": ",".join(p.code for p in PARAMS),
        "community": COMMUNITY,
        "longitude": f"{lon:.4f}",
        "latitude": f"{lat:.4f}",
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }


def request_url(query: dict[str, str]) -> str:
    return str(httpx.URL(POWER_URL, params=query))


def cache_path(cache_root: Path, site_id: str, start: date, end: date) -> Path:
    return cache_root / "power" / site_id / f"daily_{start:%Y%m%d}_{end:%Y%m%d}.json"


def download(
    query: dict[str, str],
    *,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """GET with retry and exponential backoff on network errors, 429 and 5xx."""
    own = client is None
    client = client or httpx.Client(timeout=TIMEOUT_S)
    try:
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = client.get(POWER_URL, params=query)
            except httpx.TransportError as exc:
                reason = f"{type(exc).__name__}: {exc}"
            else:
                if response.status_code == 200:
                    return response.json()
                if response.status_code not in RETRY_STATUS:
                    # 4xx: the request itself is wrong; retrying will not help
                    raise PipelineError(
                        f"NASA POWER rejected the request ({response.status_code}): "
                        f"{response.text[:500]}"
                    )
                reason = f"HTTP {response.status_code}"
            if attempt == MAX_ATTEMPTS:
                break
            wait = 2.0**attempt
            log.warning("POWER attempt %s/%s failed (%s); retry in %.0fs", attempt,
                        MAX_ATTEMPTS, reason, wait)  # fmt: skip
            sleep(wait)
    finally:
        if own:
            client.close()
    raise LayerError("SOURCE_TIMEOUT", f"NASA POWER did not respond after {MAX_ATTEMPTS} attempts")


def fetch(
    site_id: str,
    lat: float,
    lon: float,
    start: date,
    end: date,
    *,
    cache_root: Path,
    offline: bool = False,
    refresh: bool = False,
    client: httpx.Client | None = None,
    sleep: Callable[[float], None] = time.sleep,
    now: Callable[[], datetime] = local_now,
) -> PowerRaw:
    """Return the POWER daily series for a point. Idempotent: an existing cache file wins."""
    query = build_query(lat, lon, start, end)
    path = cache_path(cache_root, site_id, start, end)
    if path.exists() and not refresh:
        log.info("POWER: using cache %s", path)
        return parse(json.loads(path.read_text(encoding="utf-8")), lat=lat, lon=lon)
    if offline:
        raise LayerError("NOT_EXTRACTED_YET", f"no NASA POWER cache for {site_id} at {path.name}")

    payload = download(query, client=client, sleep=sleep)
    wrapped = {
        "fieldshift_request": {
            "url": request_url(query),
            "accessed_at": now().isoformat(timespec="seconds"),
        },
        "response": payload,
    }
    raw = parse(wrapped, lat=lat, lon=lon)  # validate before caching: never cache a bad payload
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(wrapped, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n"
    )
    log.info("POWER: cached %s", path)
    return raw


def parse(wrapped: dict[str, Any], *, lat: float, lon: float) -> PowerRaw:
    """Check the payload (point, parameters, native units) and turn fill values into `None`."""
    meta = wrapped["fieldshift_request"]
    payload = wrapped["response"]
    header = payload.get("header", {})
    if "properties" not in payload:
        raise PipelineError(f"NASA POWER returned no data: {payload.get('messages')}")

    p_lon, p_lat, elevation = payload["geometry"]["coordinates"]
    if not (math.isclose(p_lat, lat, abs_tol=1e-4) and math.isclose(p_lon, lon, abs_tol=1e-4)):
        raise PipelineError(f"cached POWER point ({p_lat}, {p_lon}) != requested ({lat}, {lon})")

    fill = float(header.get("fill_value", -999.0))
    meta_params = payload["parameters"]
    series = payload["properties"]["parameter"]
    daily: dict[str, dict[date, float | None]] = {}
    for p in PARAMS:
        if p.code not in series:
            raise PipelineError(f"NASA POWER response lacks {p.code}")
        unit = meta_params[p.code]["units"]
        if unit != p.native_unit:  # unit drift would silently corrupt every number
            raise PipelineError(f"{p.code}: native unit {unit!r}, expected {p.native_unit!r}")
        daily[p.code] = {
            datetime.strptime(k, "%Y%m%d").date(): _clean(v, fill)
            for k, v in series[p.code].items()
        }

    return PowerRaw(
        lat=lat,
        lon=lon,
        elevation_m=float(elevation),
        api_name=header["api"]["name"],
        api_version=header["api"]["version"],
        upstream_sources=tuple(header.get("sources", [])),
        time_standard=header.get("time_standard", ""),
        url=meta["url"],
        accessed_at=meta["accessed_at"],
        native_units={p.code: meta_params[p.code]["units"] for p in PARAMS},
        longnames={p.code: meta_params[p.code]["longname"] for p in PARAMS},
        daily=daily,
    )


def _clean(value: float | None, fill: float) -> float | None:
    """The fill value (-999) means missing: never a number (architecture, External APIs)."""
    if value is None:
        return None
    v = float(value)
    if math.isnan(v) or math.isclose(v, fill):
        return None
    return v
