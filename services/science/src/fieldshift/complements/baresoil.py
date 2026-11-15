# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Observed bare-soil calendar: share of cropland without green cover (NDVI < 0.25) per fortnight,
Sentinel-2 10 m (median and range over 2019-2025) beside MODIS 250 m (median).

Inputs: one row per Sentinel-2 scene (STAC item URL per row) and one row per MODIS year-fortnight.
"""

from __future__ import annotations

import csv
import statistics
from pathlib import Path

from fieldshift.complements import provenance as cp
from fieldshift.contracts import SCHEMA_VERSION, LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.baresoil import BareSoilCalendar, FortnightCover
from fieldshift.contracts.provenance import (
    ProvenanceAccess,
    ProvenanceSource,
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)
from fieldshift.errors import PipelineError

S2_INPUT = "bare-soil-s2-scenes.csv"
MODIS_INPUT = "bare-soil-modis-fortnights.csv"
NDVI_THRESHOLD = 0.25
MIN_CLEAR = 0.5  # a scene counts when at least half of the cropland pixels are cloud-free
FIRST_YEAR, LAST_YEAR = 2019, 2025
DOC_ANCHOR = "bare-soil-calendar"
S2_ACCESSED_AT = "2026-11-14T16:41:57-03:00"  # scene list (STAC search) of the team read
MODIS_ACCESSED_AT = "2026-11-14T15:00:08-03:00"  # granule list of the team read (LP DAAC)
STRAW_CAVEAT = (
    "NDVI < 0.25 does not separate straw from bare soil: under no-till, dry straw after "
    "desiccation looks like bare ground. Read it as 'no green cover', not as 'exposed soil'."
)


def _rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PipelineError(f"bare-soil input missing: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if not r["source_url"].startswith("https://"):
            raise PipelineError(f"{path.name}: row without a source URL: {r}")
    return rows


def _pct(x: float) -> float:
    return round(100 * x, 1)


def build_bare_soil(site_id: str, input_dir: Path) -> tuple[BareSoilCalendar, list[Provenance]]:
    s2: dict[int, list[float]] = {i: [] for i in range(24)}
    for r in _rows(input_dir / S2_INPUT):
        if FIRST_YEAR <= int(r["year"]) <= LAST_YEAR and float(r["clear_fraction"]) >= MIN_CLEAR:
            s2[int(r["fortnight"])].append(float(r["fraction_ndvi_lt_0_25"]))
    modis: dict[int, list[float]] = {i: [] for i in range(24)}
    for r in _rows(input_dir / MODIS_INPUT):
        if FIRST_YEAR <= int(r["year"]) <= LAST_YEAR and int(r["n_observations"]) > 0:
            modis[int(r["fortnight"])].append(float(r["fraction_ndvi_lt_0_25"]))
    fortnights = []
    for i in range(24):
        v, m = s2[i], modis[i]
        fortnights.append(
            FortnightCover(
                index=i,
                month=i // 2 + 1,
                half=i % 2 + 1,
                s2_median_pct=_pct(statistics.median(v)) if v else None,
                s2_min_pct=_pct(min(v)) if v else None,
                s2_max_pct=_pct(max(v)) if v else None,
                s2_years=len(v),
                modis_median_pct=_pct(statistics.median(m)) if m else None,
                modis_years=len(m),
            )
        )
    period = Period(start=f"{FIRST_YEAR}-01-01", end=f"{LAST_YEAR}-12-31")
    s2_raw = Provenance(
        id=f"prov:esa:{site_id}:sentinel-2-l2a",
        data_type="satellite_observed",
        title=cp.t("Sentinel-2 L2A surface reflectance (B04, B08, SCL), tile 22JBP"),
        source=ProvenanceSource(
            dataset="Copernicus Sentinel-2",
            provider="ESA (Copernicus); COGs served by Element 84 Earth Search",
            product="sentinel-2-l2a",
            version="L2A, several processing baselines (DN offset rule in the method)",
            collection_id="sentinel-2-l2a",
        ),
        variable=ProvenanceVariable(code="NDVI", name=cp.t("NDVI from B04 and B08"), unit="1"),
        spatial=ProvenanceSpatial(resolution="10 m", resolution_m=10, support="regional"),
        temporal=ProvenanceTemporal(resolution="16-day", period=period),
        aggregation=cp.t(
            "One scene per fortnight (lowest tile cloud cover, at most 70%), cropland "
            "pixels of the ESA WorldCover 2021 class 40 inside 9 blocks of the "
            "municipality (672 km2, 64% of its cropland)."
        ),
        access=ProvenanceAccess(
            url="https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a",
            accessed_at=S2_ACCESSED_AT,
            terms_url="https://sentinels.copernicus.eu/documents/247904/690755/"
            "Sentinel_Data_Legal_Notice",
            license="Copernicus open data licence (free use with attribution)",
        ),
        limitations=[
            cp.t("Partner data (ESA Copernicus), not NASA data; credited as the licence asks.")
        ],
        attribution=[cp.ESA_S2],
    )
    modis_raw = Provenance(
        id=f"prov:nasa:{site_id}:modis-ndvi",
        data_type="satellite_observed",
        title=cp.t("MODIS Terra and Aqua 16-day NDVI (MOD13Q1, MYD13Q1 v061)"),
        source=ProvenanceSource(
            dataset="MODIS Vegetation Indices",
            provider="NASA LP DAAC",
            product="MOD13Q1 / MYD13Q1",
            version="061",
        ),
        variable=ProvenanceVariable(code="NDVI", name=cp.t("NDVI"), unit="1"),
        spatial=ProvenanceSpatial(resolution="250 m", resolution_m=250, support="regional"),
        temporal=ProvenanceTemporal(resolution="16-day", period=period),
        aggregation=cp.t(
            "Valid observations (reliability 0 or 1) of pixels with at least 80% "
            "WorldCover cropland, grouped by the fortnight of their acquisition day."
        ),
        access=ProvenanceAccess(
            url="https://lpdaac.usgs.gov/products/mod13q1v061/",
            doi="10.5067/MODIS/MOD13Q1.061",
            accessed_at=MODIS_ACCESSED_AT,
            terms_url="https://lpdaac.usgs.gov/data/data-citation-and-policies/",
        ),
        limitations=[
            cp.t(
                "16-day maximum-value composites pick the greenest day, which hides "
                "short bare spells (hypothesis, not tested)."
            )
        ],
        attribution=[cp.NASA_MODIS],
    )
    common = {
        "code": "no_green_cover_share",
        "name": "Cropland share with NDVI < 0.25",
        "unit": "%",
        "period": period,
        "support": "regional",
        "temporal": "16-day",
        "doc_anchor": DOC_ANCHOR,
        "parameters": {
            "ndvi_threshold": NDVI_THRESHOLD,
            "min_clear_fraction": MIN_CLEAR,
            "years": f"{FIRST_YEAR}-{LAST_YEAR}",
        },
        "ref": Ref(
            label="Tucker, C.J. (1979). Red and photographic infrared linear combinations "
            "for monitoring vegetation. Remote Sensing of Environment 8, 127-150.",
            doi="10.1016/0034-4257(79)90013-0",
        ),
    }
    s2_rec = cp.computed(
        rid=f"prov:computed:{site_id}:bare-soil:s2",
        title="Cropland without green cover by "
        "fortnight, Sentinel-2 10 m (median, min and max over the years)",
        resolution="10 m",
        aggregation="Per scene: share of clear cropland pixels with NDVI < 0.25; per fortnight: "
        "median, minimum and maximum over the years with a scene.",
        method="bare-soil-calendar v1",
        inputs=[s2_raw.id],
        limitations=[
            STRAW_CAVEAT,
            "One scene per fortnight, on a different day each year; 7 years give a "
            "calendar, not a trend.",
            "The 9 blocks were chosen for having the most cropland, not at random; "
            "WorldCover is a single year (2021).",
        ],
        attribution=[cp.ESA_S2],
        **common,
    )
    modis_rec = cp.computed(
        rid=f"prov:computed:{site_id}:bare-soil:modis",
        title="Cropland without green cover by fortnight, MODIS 250 m (median over the years)",
        resolution="250 m",
        aggregation="Per year and fortnight: share of valid observations with NDVI < 0.25; per "
        "fortnight: median over the years.",
        method="bare-soil-calendar v1",
        inputs=[modis_raw.id],
        limitations=[
            STRAW_CAVEAT,
            "MODIS shows far less 'no green' than Sentinel-2 in the same fortnights; "
            "Sentinel-2 aggregated to 250 m keeps its own level, so the gap is in the "
            "MODIS product, not in the pixel size.",
        ],
        attribution=[cp.NASA_MODIS],
        **common,
    )
    cal = BareSoilCalendar(
        schema_version=SCHEMA_VERSION,
        site_id=site_id,
        period=period,
        ndvi_threshold=NDVI_THRESHOLD,
        fortnights=fortnights,
        s2_provenance_id=s2_rec.id,
        modis_provenance_id=modis_rec.id,
        caveats=[
            LocalizedText(en=STRAW_CAVEAT),
            LocalizedText(en="Sentinel-2 is partner data (ESA Copernicus); MODIS is NASA data."),
        ],
    )
    return cal, [s2_raw, modis_raw, s2_rec, modis_rec]
