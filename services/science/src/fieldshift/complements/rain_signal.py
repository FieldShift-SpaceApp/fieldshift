# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""NASA causal link: heavy-rain days and rain totals in September-November (wheat harvest window
in the Planalto Médio) by ENSO phase, from NASA POWER, GPM IMERG (via POWER) and the ANA 2853015
rain gauge, side by side.

Phase of a year = NOAA CPC operational phase of the SON season of that year. A year counts for a
source only when every day of September-November has a value in that source.
"""

from __future__ import annotations

import csv
import statistics
from datetime import date, timedelta
from pathlib import Path

from fieldshift.complements import provenance as cp
from fieldshift.complements.oni import OniFile, operational_phases
from fieldshift.contracts import SCHEMA_VERSION, LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.provenance import (
    ProvenanceAccess,
    ProvenanceSource,
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)
from fieldshift.contracts.rain import EnsoRainSignal, PhaseRainStats, RainSourceSignal, RainYear
from fieldshift.errors import PipelineError
from fieldshift.provenance.power import power_prov_id
from fieldshift.sources.power_imerg import IMERG_DOI, ImergRaw

MONTHS = (9, 10, 11)
SEASON = "SON"
HEAVY_MM = 50.0
FIRST_YEAR, LAST_YEAR = 1982, 2025
GAUGE_INPUT = "ana-2853015-sep-nov-daily.csv"
GAUGE_URL = (
    "https://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica?codEstacao=2853015"
)
DOC_ANCHOR = "enso-heavy-rain"
PHASES = ("el_nino", "neutral", "la_nina")


def window_days(year: int) -> list[date]:
    d, out = date(year, MONTHS[0], 1), []
    while d.month in MONTHS and d.year == year:
        out.append(d)
        d += timedelta(days=1)
    return out


def season_years(
    daily: dict[date, float | None], years: range
) -> dict[int, tuple[float, int] | None]:
    """Per year: (total mm, days >= HEAVY_MM) when the window is complete, else None."""
    out: dict[int, tuple[float, int] | None] = {}
    for y in years:
        vals = [daily.get(d) for d in window_days(y)]
        if any(v is None for v in vals):
            out[y] = None
        else:
            out[y] = (sum(vals), sum(1 for v in vals if v >= HEAVY_MM))  # type: ignore[misc]
    return out


def load_gauge(path: Path) -> dict[date, float | None]:
    if not path.is_file():
        raise PipelineError(f"rain gauge input missing: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if not r["source_url"].startswith(GAUGE_URL):
            raise PipelineError(f"{path.name}: row without the ANA source URL: {r['date']}")
    return {
        date.fromisoformat(r["date"]): (float(r["rain_mm"]) if r["rain_mm"] else None) for r in rows
    }


def _signal(
    sid: str,
    label: str,
    seasons: dict[int, tuple[float, int] | None],
    oni: OniFile,
    phases: dict,
    prov_id: str,
) -> RainSourceSignal:
    years = []
    for y, v in sorted(seasons.items()):
        years.append(
            RainYear(
                year=y,
                oni=oni.values[(SEASON, y)],
                phase=phases[(SEASON, y)],
                total_mm=None if v is None else round(v[0], 1),
                heavy_days=None if v is None else v[1],
            )
        )
    stats = []
    for p in PHASES:
        done = [
            (seasons[y.year][0], seasons[y.year][1])
            for y in years  # type: ignore[index]
            if y.phase == p and seasons[y.year] is not None
        ]
        stats.append(
            PhaseRainStats(
                phase=p,
                n_years=len(done),
                mean_heavy_days=round(statistics.fmean(d for _, d in done), 2) if done else None,
                mean_total_mm=round(statistics.fmean(t for t, _ in done), 1) if done else None,
                median_total_mm=round(statistics.median(t for t, _ in done), 1) if done else None,
                years_with_heavy_day=sum(1 for _, d in done if d > 0),
            )
        )
    return RainSourceSignal(
        id=sid,
        label=LocalizedText(en=label),
        first_year=years[0].year,
        last_year=years[-1].year,
        years=years,
        by_phase=stats,
        provenance_id=prov_id,
    )


def imerg_record(site_id: str, raw: ImergRaw, period: Period) -> Provenance:
    return Provenance(
        id=f"prov:imerg:{site_id}:imerg_prectot:daily",
        data_type="satellite_observed",
        title=cp.t("GPM IMERG daily precipitation at the site point (served by NASA POWER)"),
        source=ProvenanceSource(
            dataset="GPM IMERG",
            provider="NASA GES DISC, via NASA LaRC POWER",
            product="POWER Daily API, parameter IMERG_PRECTOT (UTC days)",
            version=f"POWER {raw.api_version}; IMERG run/version not stated",
        ),
        variable=ProvenanceVariable(
            code="IMERG_PRECTOT",
            name=cp.t("Precipitation"),
            unit="mm/d",
            native_unit=raw.native_unit,
        ),
        spatial=ProvenanceSpatial(
            resolution="0.1° (IMERG grid)", resolution_m=11000, support="containing_pixel"
        ),
        temporal=ProvenanceTemporal(resolution="daily", period=period),
        aggregation=cp.t("Daily values as served; -999 is read as missing."),
        access=ProvenanceAccess(
            url=raw.url,
            doi=IMERG_DOI,
            accessed_at=raw.accessed_at,
            terms_url="https://power.larc.nasa.gov/docs/referencing/",
        ),
        limitations=[
            cp.t(
                "POWER serves IMERG only in UTC days and does not say which run (Early, Late, "
                "Final) or version it is; the DOI given is the IMERG Final half-hourly V07."
            ),
            cp.t(
                "How IMERG and NASA POWER compare with ground stations at Cruz Alta is on the "
                "satellite-vs-ground method page."
            ),
        ],
        attribution=[cp.NASA_IMERG],
    )


def gauge_record(site_id: str, period: Period) -> Provenance:
    return Provenance(
        id=f"prov:user:{site_id}:ana-2853015",
        data_type="user_provided",
        title=cp.t("ANA rain gauge 2853015 (Três Capões, 14.9 km from the site point), daily rain"),
        variable=ProvenanceVariable(code="rain_gauge", name=cp.t("Daily rain"), unit="mm/d"),
        spatial=ProvenanceSpatial(resolution="point (rain gauge)", support="point"),
        temporal=ProvenanceTemporal(resolution="daily", period=period),
        aggregation=cp.t(
            "Daily values of the ANA historical series (consistency level 2 when "
            "present, else level 1 raw), September-November only."
        ),
        authored_by="ANA (Agência Nacional de Águas e Saneamento Básico), HidroWeb; series "
        "copied to input/ana-2853015-sep-nov-daily.csv with the service URL per row",
        refs=[
            Ref(
                label="ANA HidroWeb web service, HidroSerieHistorica, station 2853015",
                url=GAUGE_URL + "&dataInicio=&dataFim=&tipoDados=2&nivelConsistencia=",
            )
        ],
        limitations=[
            cp.t(
                "Ground observation, recorded as user_provided: the contracts have no data type "
                "for ground stations."
            ),
            cp.t(
                "Gap in 2013-2016 and a step of about +10-13% after it against neighbouring "
                "gauges (team station check); morning reading, so its day is shifted against "
                "the gridded sources."
            ),
            cp.t("A point gauge sees local storms that a 10-50 km grid cell smooths out."),
        ],
        attribution=[cp.ANA],
    )


def build_rain_signal(
    site_id: str,
    power_daily: dict[date, float | None],
    imerg: ImergRaw | None,
    gauge_daily: dict[date, float | None],
    oni: OniFile,
) -> tuple[EnsoRainSignal, list[Provenance]]:
    phases = operational_phases(oni)
    years = range(FIRST_YEAR, LAST_YEAR + 1)
    records: list[Provenance] = []
    sources: list[RainSourceSignal] = []
    notes: list[LocalizedText] = []
    base_inputs = [cp.oni_prov_id(site_id)]

    def comp(key: str, label: str, upstream: str, attribution: list) -> str:
        rid = f"prov:computed:{site_id}:enso-heavy-rain:{key}"
        records.append(
            cp.computed(
                rid=rid,
                title=f"Rain and heavy-rain days in September-November by ENSO phase, {label}",
                code="heavy_rain_days_son",
                name="Days with rain >= 50 mm; window total",
                unit="days",
                period=Period(start=f"{FIRST_YEAR}-09-01", end=f"{LAST_YEAR}-11-30"),
                resolution="site point",
                support="containing_pixel" if key != "ana-2853015" else "point",
                temporal="annual",
                aggregation="Per year: total of September-November and number of days >= 50 mm "
                "(complete windows only); per phase: mean and median over the years of that phase.",
                method="enso-heavy-rain v1",
                doc_anchor=DOC_ANCHOR,
                ref=Ref(
                    label="NOAA CPC, ENSO operational definition (ONI >= +/-0.5 for 5 consecutive "
                    "overlapping seasons)",
                    url="https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/"
                    "ONI_v5.php",
                ),
                parameters={
                    "months": "9,10,11",
                    "phase_season": SEASON,
                    "heavy_rain_mm": HEAVY_MM,
                    "phase_threshold_degC": 0.5,
                    "phase_min_seasons": 5,
                },
                inputs=[upstream, *base_inputs],
                limitations=[
                    "Few events: about 15 El Niño, 13 La Niña and 16 neutral springs in 1982-2025; "
                    "a "
                    "mean of heavy-rain days moves with one wet year.",
                    "Association, not proof of cause: ENSO phase and spring rain are compared year "
                    "by year, with no model of the wheat itself.",
                ],
                attribution=attribution,
            )
        )
        return rid

    sources.append(
        _signal(
            "nasa-power",
            "NASA POWER (MERRA-2 bias-corrected precipitation, PRECTOTCORR)",
            season_years(power_daily, years),
            oni,
            phases,
            comp(
                "nasa-power",
                "NASA POWER",
                power_prov_id(site_id, "PRECTOTCORR"),
                [cp.NASA_POWER, cp.NOAA_ONI],
            ),
        )
    )
    if imerg is not None and imerg.valid_days:
        first = min(d for d, v in imerg.daily.items() if v is not None)
        rec = imerg_record(
            site_id, imerg, Period(start=first.isoformat(), end=max(imerg.daily).isoformat())
        )
        records.append(rec)
        im_years = range(max(FIRST_YEAR, first.year), LAST_YEAR + 1)
        sources.append(
            _signal(
                "gpm-imerg",
                "GPM IMERG (via NASA POWER, UTC days)",
                season_years(imerg.daily, im_years),
                oni,
                phases,
                comp("gpm-imerg", "GPM IMERG", rec.id, [cp.NASA_IMERG, cp.NOAA_ONI]),
            )
        )
    else:
        notes.append(
            LocalizedText(
                en="GPM IMERG via NASA POWER returned only fill values (-999) "
                "for this point; only NASA POWER is shown."
            )
        )
    g_first = min(gauge_daily)
    grec = gauge_record(
        site_id, Period(start=g_first.isoformat(), end=max(gauge_daily).isoformat())
    )
    records.append(grec)
    sources.append(
        _signal(
            "ana-2853015",
            "Rain gauge ANA 2853015 (ground check)",
            season_years(gauge_daily, years),
            oni,
            phases,
            comp("ana-2853015", "ANA rain gauge 2853015", grec.id, [cp.ANA, cp.NOAA_ONI]),
        )
    )
    doc = EnsoRainSignal(
        schema_version=SCHEMA_VERSION,
        site_id=site_id,
        label=LocalizedText(
            en="Heavy rain in the wheat harvest window (September-November) by ENSO phase"
        ),
        months=list(MONTHS),
        phase_season=SEASON,
        heavy_rain_mm=HEAVY_MM,
        oni_provenance_id=cp.oni_prov_id(site_id),
        sources=sources,
        notes=notes,
    )
    return doc, records
