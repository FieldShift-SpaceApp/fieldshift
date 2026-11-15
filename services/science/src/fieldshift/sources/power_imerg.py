# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""GPM IMERG daily precipitation at a point, served by the NASA POWER API (`IMERG_PRECTOT`).

POWER returns IMERG only with `time-standard=UTC` (in local solar time the API gives -999 only).
The fill value -999 is read as missing. POWER does not say which IMERG run (Early, Late, Final)
or version it serves; the provenance says so.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx

from fieldshift.errors import LayerError, PipelineError
from fieldshift.sources import power

PARAM = "IMERG_PRECTOT"
IMERG_START = date(1998, 1, 1)
IMERG_DOI = "10.5067/GPM/IMERG/3B-HH/07"


@dataclass(frozen=True)
class ImergRaw:
    lat: float
    lon: float
    url: str
    accessed_at: str
    api_version: str
    native_unit: str
    daily: dict[date, float | None]

    @property
    def valid_days(self) -> int:
        return sum(1 for v in self.daily.values() if v is not None)


def build_query(lat: float, lon: float, start: date, end: date) -> dict[str, str]:
    return {
        "parameters": PARAM,
        "community": power.COMMUNITY,
        "longitude": f"{lon:.4f}",
        "latitude": f"{lat:.4f}",
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "UTC",
    }


def cache_path(cache_root: Path, site_id: str, start: date, end: date) -> Path:
    return cache_root / "power-imerg" / site_id / f"daily_{start:%Y%m%d}_{end:%Y%m%d}.json"


def parse(wrapped: dict[str, Any], *, lat: float, lon: float) -> ImergRaw:
    meta, payload = wrapped["fieldshift_request"], wrapped["response"]
    if "properties" not in payload:
        raise PipelineError(f"NASA POWER returned no IMERG data: {payload.get('messages')}")
    p_lon, p_lat, _ = payload["geometry"]["coordinates"]
    if not (math.isclose(p_lat, lat, abs_tol=1e-4) and math.isclose(p_lon, lon, abs_tol=1e-4)):
        raise PipelineError(f"cached IMERG point ({p_lat}, {p_lon}) != requested ({lat}, {lon})")
    header = payload.get("header", {})
    fill = float(header.get("fill_value", -999.0))
    unit = payload["parameters"][PARAM]["units"]
    if unit != "mm/day":
        raise PipelineError(f"{PARAM}: native unit {unit!r}, expected 'mm/day'")
    daily = {
        datetime.strptime(k, "%Y%m%d").date(): (None if v is None or v == fill else float(v))
        for k, v in payload["properties"]["parameter"][PARAM].items()
    }
    return ImergRaw(
        lat=lat,
        lon=lon,
        url=meta["url"],
        accessed_at=meta["accessed_at"],
        api_version=header.get("api", {}).get("version", ""),
        native_unit=unit,
        daily=daily,
    )


def fetch(
    site_id: str,
    lat: float,
    lon: float,
    start: date,
    end: date,
    *,
    cache_root: Path,
    offline: bool = False,
    client: httpx.Client | None = None,
    now: Callable[[], datetime] = power.local_now,
) -> ImergRaw:
    """Idempotent: an existing cache file wins."""
    path = cache_path(cache_root, site_id, start, end)
    if path.exists():
        return parse(json.loads(path.read_text(encoding="utf-8")), lat=lat, lon=lon)
    if offline:
        raise LayerError("NOT_EXTRACTED_YET", f"no IMERG cache for {site_id} at {path.name}")
    query = build_query(lat, lon, start, end)
    own = client is None
    client = client or httpx.Client(timeout=power.TIMEOUT_S)
    try:
        response = client.get(power.POWER_URL, params=query)
    except httpx.TransportError as exc:
        raise LayerError("SOURCE_TIMEOUT", f"NASA POWER (IMERG) did not respond: {exc}") from exc
    finally:
        if own:
            client.close()
    if response.status_code != 200:
        raise PipelineError(f"NASA POWER rejected the IMERG request ({response.status_code})")
    wrapped = {
        "fieldshift_request": {
            "url": str(httpx.URL(power.POWER_URL, params=query)),
            "accessed_at": now().isoformat(timespec="seconds"),
        },
        "response": response.json(),
    }
    raw = parse(wrapped, lat=lat, lon=lon)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(wrapped, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n"
    )
    return raw
