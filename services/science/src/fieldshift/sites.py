# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Where a site is: the point the source fetchers query.

Real sites come from `data/sites/<id>/input/site.yaml` (SURGEON, issue #8): the pipeline uses
`point` when the file has it, otherwise the centroid of `field`. No coordinates are invented here.

Development points are listed in `DEV_SITES`. Their id starts with `dev-`, their outputs go to
`data/dev/<id>/output/` (never to `data/sites/`, which `scripts/sync-data.mjs` publishes to the
app), and every provenance record they produce carries a "DEV ONLY" limitation.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from fieldshift.contracts.site import GeoJSONPolygon, GeoPoint
from fieldshift.errors import PipelineError

SITE_ID = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
DEV_PREFIX = "dev-"


@dataclass(frozen=True)
class SitePoint:
    id: str
    lat: float
    lon: float
    label: str
    dev: bool

    def __post_init__(self) -> None:
        if not SITE_ID.match(self.id):
            raise PipelineError(f"invalid site id {self.id!r} (expected {SITE_ID.pattern})")
        if self.dev != self.id.startswith(DEV_PREFIX):
            raise PipelineError(f"{self.id}: development sites, and only them, start with 'dev-'")
        GeoPoint(lat=self.lat, lon=self.lon)  # range check

    def output_dir(self, data_dir: Path) -> Path:
        base = data_dir / "dev" if self.dev else data_dir / "sites"
        return base / self.id / "output"


DEV_SITES: dict[str, SitePoint] = {
    # Development point only (coordination brief, issue #11). NOT a demo site.
    "dev-floripa": SitePoint(
        id="dev-floripa",
        lat=-27.6,
        lon=-48.5,
        label="DEV ONLY: Florianópolis development point (not a demo site)",
        dev=True,
    ),
    # CANDIDATE location under study (issue #26), NOT a demo site (that is D-001/#8). Point: the
    # centroid IBGE publishes for municipality 4306106 (Cruz Alta, RS), malhas API v3, 2022 mesh
    # (-28.703, -53.5626), rounded to the 3 decimals POWER echoes back; see
    # data/dev/dev-cruz-alta/README.md.
    "dev-cruz-alta": SitePoint(
        id="dev-cruz-alta",
        lat=-28.703,
        lon=-53.563,
        label="DEV ONLY: Cruz Alta (RS) municipal centroid, candidate (not a demo site)",
        dev=True,
    ),
}


def polygon_centroid(polygon: GeoJSONPolygon) -> tuple[float, float]:
    """Planar centroid (lat, lon) of the outer ring. Fine for a field of a few km²."""
    ring = polygon.coordinates[0]
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(ring[:-1], ring[1:], strict=True):
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if a == 0:
        raise PipelineError("field polygon has zero area")
    a *= 0.5
    return cy / (6 * a), cx / (6 * a)


def resolve_site(
    site_id: str, data_dir: Path, *, lat: float | None = None, lon: float | None = None
) -> SitePoint:
    """Explicit --lat/--lon win; then the DEV list; then the site's input YAML."""
    if (lat is None) != (lon is None):
        raise PipelineError("pass both --lat and --lon, or neither")
    dev = site_id.startswith(DEV_PREFIX)
    if lat is not None and lon is not None:
        label = f"{'DEV ONLY: ' if dev else ''}point {lat}, {lon} given on the command line"
        return SitePoint(site_id, lat, lon, label, dev)
    if site_id in DEV_SITES:
        return DEV_SITES[site_id]

    path = data_dir / "sites" / site_id / "input" / "site.yaml"
    if not path.is_file():
        raise PipelineError(
            f"{path} not found. Real sites come from SURGEON (issue #8); "
            "for an ad-hoc point pass --lat and --lon."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if raw.get("id", site_id) != site_id:
        raise PipelineError(f"{path}: id {raw.get('id')!r} != {site_id!r}")
    if "point" in raw:
        point = GeoPoint.model_validate(raw["point"])
        p_lat, p_lon = point.lat, point.lon
    elif "field" in raw:
        p_lat, p_lon = polygon_centroid(GeoJSONPolygon.model_validate(raw["field"]))
    else:
        raise PipelineError(f"{path}: needs `point` or `field` to locate the site")
    name = (raw.get("name") or {}).get("en", site_id)
    return SitePoint(site_id, p_lat, p_lon, name, dev)
