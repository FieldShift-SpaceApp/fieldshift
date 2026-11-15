# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Rain of the current wheat harvest window so far (contracts v1.3.0, `now-2026.json`).

Same rule as the heavy-rain signal (`rain_signal`): days >= 50 mm, phase of a past year = NOAA CPC
operational phase of its SON season. The current year is cut at the last day each source has a
value; every past year is read over the same calendar days (September 1 to that day), so the
comparison never sets a part of a season against a whole one. The current ENSO state is the latest
published ONI season (SON is not complete yet).

Third-party reports on the crop (Emater/RS-Ascar) are recorded as `reported`, apart from the
measurements: FieldShift does not measure the wheat of the current year.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import date, timedelta

from fieldshift.complements import provenance as cp
from fieldshift.complements.oni import SEASONS, OniFile, operational_phases
from fieldshift.complements.rain_signal import HEAVY_MM, PHASES, SEASON, imerg_record
from fieldshift.contracts import SCHEMA_VERSION, LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.provenance import (
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)
from fieldshift.contracts.rain import (
    CurrentEnso,
    MonthToDate,
    PhaseRainStats,
    RainYear,
    ReportedFact,
    SeasonToDate,
    SeasonToDateSource,
)
from fieldshift.errors import PipelineError
from fieldshift.provenance.power import power_prov_id, power_record
from fieldshift.sites import SitePoint
from fieldshift.sources.power import PARAMS_BY_CODE, PowerRaw
from fieldshift.sources.power_imerg import ImergRaw

YEAR = 2026
START = date(YEAR, 9, 1)
CUTOFF = date(YEAR, 11, 13)  # last day requested from the APIs (access on 2026-11-14)
CLIM_FIRST, CLIM_LAST = 1998, 2025  # first full year of GPM IMERG via POWER .. last past year
COMPARE_YEARS = (2023,)
DOC_ANCHOR = "now-2026"
FILE = "now-2026.json"

Daily = dict[date, float | None]


def last_valid_day(daily: Daily, start: date, cutoff: date) -> date:
    """Last day of the run of valid days that begins at `start` (no gap allowed inside it)."""
    d, last = start, None
    while d <= cutoff and daily.get(d) is not None:
        last, d = d, d + timedelta(days=1)
    if last is None:
        raise PipelineError(f"no value on {start}")
    return last


def same_days(year: int, start: date, end: date) -> list[date]:
    first = start.replace(year=year)
    return [first + timedelta(days=i) for i in range((end - start).days + 1)]


def window_values(daily: Daily, days: list[date]) -> list[float] | None:
    vals = [daily.get(d) for d in days]
    return None if any(v is None for v in vals) else vals  # type: ignore[return-value]


def _stats(phase: str, done: list[tuple[float, int]]) -> PhaseRainStats:
    return PhaseRainStats(
        phase=phase,  # type: ignore[arg-type]
        n_years=len(done),
        mean_heavy_days=round(statistics.fmean(d for _, d in done), 2) if done else None,
        mean_total_mm=round(statistics.fmean(t for t, _ in done), 1) if done else None,
        median_total_mm=round(statistics.median(t for t, _ in done), 1) if done else None,
        years_with_heavy_day=sum(1 for _, d in done if d > 0),
    )


def source_block(
    sid: str,
    label: str,
    current: Daily,
    history: Daily,
    oni: OniFile,
    phases: dict,
    prov_id: str,
) -> SeasonToDateSource:
    end = last_valid_day(current, START, CUTOFF)
    days = same_days(YEAR, START, end)
    vals = window_values(current, days)
    assert vals is not None
    wet = max(range(len(vals)), key=lambda i: vals[i])

    past: dict[int, list[float] | None] = {
        y: window_values(history, same_days(y, START, end))
        for y in range(CLIM_FIRST, CLIM_LAST + 1)
    }
    by_phase = []
    for p in PHASES:
        done = [
            (sum(v), sum(1 for x in v if x >= HEAVY_MM))
            for y, v in past.items()
            if v is not None and phases[(SEASON, y)] == p
        ]
        by_phase.append(_stats(p, done))
    compare = []
    for y in COMPARE_YEARS:
        v = past[y]
        compare.append(
            RainYear(
                year=y,
                oni=oni.values[(SEASON, y)],
                phase=phases[(SEASON, y)],
                total_mm=None if v is None else round(sum(v), 1),
                heavy_days=None if v is None else sum(1 for x in v if x >= HEAVY_MM),
            )
        )
    months = []
    for m in sorted({d.month for d in days}):
        idx = [i for i, d in enumerate(days) if d.month == m]
        clim = [sum(v[i] for i in idx) for v in past.values() if v is not None]
        months.append(
            MonthToDate(
                month=f"{YEAR}-{m:02d}",
                n_days=len(idx),
                total_mm=round(sum(vals[i] for i in idx), 1),
                climatology_mean_mm=round(statistics.fmean(clim), 1) if clim else None,
            )
        )
    return SeasonToDateSource(
        id=sid,
        label=LocalizedText(en=label),
        window=Period(start=START.isoformat(), end=end.isoformat()),
        n_days=len(days),
        total_mm=round(sum(vals), 1),
        heavy_days=sum(1 for x in vals if x >= HEAVY_MM),
        wettest_day=days[wet].isoformat(),
        wettest_day_mm=round(vals[wet], 1),
        months=months,
        same_days=compare,
        climatology=Period(
            start=START.replace(year=CLIM_FIRST).isoformat(),
            end=end.replace(year=CLIM_LAST).isoformat(),
        ),
        by_phase=by_phase,
        provenance_id=prov_id,
    )


def current_enso(oni: OniFile, phases: dict, site_id: str) -> CurrentEnso:
    key = max((k for k in oni.values if k[1] == YEAR), key=lambda k: SEASONS.index(k[0]))
    return CurrentEnso(
        season=key[0],
        year=YEAR,
        oni=oni.values[key],
        phase=phases[key],
        provenance_id=cp.oni_prov_id(site_id),
    )


# ------------------------------------------------------------------ provenance


def power_now_record(site: SitePoint, raw: PowerRaw) -> Provenance:
    base = power_record(site, raw, PARAMS_BY_CODE["PRECTOTCORR"])
    return base.model_copy(
        update={
            "id": power_prov_id(site.id, "PRECTOTCORR") + f":{YEAR}-son",
            "title": cp.t(
                f"NASA POWER · Precipitation Corrected, September-November {YEAR} so far"
            ),
            "aggregation": cp.t("Daily values as served; -999 is read as missing."),
            "limitations": [
                *base.limitations,
                cp.t(
                    "Near-real-time days: POWER does not say per day which upstream fed the "
                    "latest weeks (its response header lists MERRA2 and GEOSIT among the sources), "
                    "and recent values can be revised; read at the access time given."
                ),
            ],
            "attribution": [cp.NASA_POWER],
        }
    )


def imerg_now_record(site_id: str, raw: ImergRaw, end: date) -> Provenance:
    base = imerg_record(site_id, raw, Period(start=START.isoformat(), end=end.isoformat()))
    lag = (date.fromisoformat(raw.accessed_at[:10]) - end).days
    return base.model_copy(
        update={
            "id": f"{base.id}:{YEAR}-son",
            "title": cp.t(
                f"GPM IMERG daily precipitation at the site point (served by NASA POWER), "
                f"September {YEAR} so far"
            ),
            "limitations": [
                *base.limitations,
                cp.t(
                    f"At access POWER had IMERG only up to {end.isoformat()} ({lag} days before "
                    "the access date); later days came back as -999. That delay fits neither the "
                    "IMERG Early or Late runs (hours) nor the Final run (about 3.5 months), so the "
                    "run behind these days is unknown."
                ),
            ],
        }
    )


@dataclass(frozen=True)
class Report:
    rid: str
    text: str
    reported_by: str
    published: str
    url: str
    title: str


EMATER_BASE = "https://www.emater.tche.br/site/arquivos_pdf/conjuntural/"
REPORTS = (
    Report(
        "emater-ic-1942",
        "Wheat, Rio Grande do Sul, 2026 crop re-estimate (data of the first half of October): "
        "763,121 ha (34.56% less than the 1,166,163 ha of 2025, IBGE); projected yield 2,833 "
        "kg/ha against 2,968 kg/ha in 2025 (the bulletin says 5.55% less); production 2,161,922 t, "
        "37.48% less than the 3,458,083 t of 2025 (IBGE). Excess moisture and low solar radiation "
        "in key phases lowered the yield potential and raised disease pressure (Fusarium head "
        "blight, 'giberela'; wheat blast, 'brusone'). Ijuí region: the cycle nears its end with "
        "reduced yield potential; in Ibirubá (Alto Jacuí) yield and quality expectations were "
        "revised down.",
        "Emater/RS-Ascar, Informativo Conjuntural n. 1942, p. 5-6",
        "2026-10-22",
        EMATER_BASE + "conj_22102026.pdf",
        "Emater/RS-Ascar Informativo Conjuntural n. 1942 (22 Oct 2026), wheat section",
    ),
    Report(
        "emater-ic-1945",
        "Wheat, Rio Grande do Sul: 76% of the area harvested by 12 November 2026. Episodes of "
        "intense rain interrupted the harvest; in part of the fields excess moisture, low light, "
        "frosts and diseases lowered the yield potential and the commercial quality, with test "
        "weight (PH) mostly below 78 kg/hl, the Type 1 reference. Ijuí region: 72% harvested; "
        "PH between 72 and 75 in Santa Bárbara do Sul.",
        "Emater/RS-Ascar, Informativo Conjuntural n. 1945, p. 5-6",
        "2026-11-12",
        EMATER_BASE + "conj_12112026.pdf",
        "Emater/RS-Ascar Informativo Conjuntural n. 1945 (12 Nov 2026), wheat section",
    ),
)


def report_record(site_id: str, r: Report) -> Provenance:
    return Provenance(
        id=f"prov:user:{site_id}:{r.rid}",
        data_type="user_provided",
        title=cp.t(r.title),
        variable=ProvenanceVariable(
            code="crop_bulletin", name=cp.t("Reported crop condition"), unit="1"
        ),  # fmt: skip
        spatial=ProvenanceSpatial(
            resolution="State of Rio Grande do Sul and Emater regions", support="regional"
        ),  # fmt: skip
        temporal=ProvenanceTemporal(
            resolution="annual", period=Period(start=f"{YEAR}-06-01", end=r.published)
        ),
        aggregation=cp.t("Statements transcribed and translated from the bulletin (Portuguese)."),
        authored_by="Emater/RS-Ascar (Rio Grande do Sul state extension service); transcribed "
        "by FieldShift with the bulletin URL",
        refs=[Ref(label=r.reported_by, url=r.url)],
        limitations=[
            cp.t(
                "Reported, not measured by FieldShift: an extension-service estimate made during "
                "the harvest. The official municipal wheat yield of 2026 (IBGE PAM) is published "
                "only in 2027."
            ),
            cp.t(
                "Recorded as user_provided: the contracts have no data type for third-party "
                "reports."
            ),  # fmt: skip
        ],
        attribution=[cp.EMATER_RS],
    )


def build_now(
    site: SitePoint,
    power_now: PowerRaw,
    power_history: Daily,
    imerg_now: ImergRaw,
    imerg_history: ImergRaw,
    oni: OniFile,
) -> tuple[SeasonToDate, list[Provenance]]:
    site_id = site.id
    phases = operational_phases(oni)
    records: list[Provenance] = []
    sources: list[SeasonToDateSource] = []
    clim = [phases[(SEASON, y)] for y in range(CLIM_FIRST, CLIM_LAST + 1)]
    counts = {p: clim.count(p) for p in PHASES}

    def comp(key: str, label: str, upstream: list[str], attribution: list) -> str:
        rid = f"prov:computed:{site_id}:now-{YEAR}:{key}"
        records.append(
            cp.computed(
                rid=rid,
                title=f"Rain of September-November {YEAR} so far against the same days of "
                f"{CLIM_FIRST}-{CLIM_LAST} by ENSO phase, {label}",
                code="rain_season_to_date",
                name="Window total; days with rain >= 50 mm",
                unit="mm",
                period=Period(start=f"{CLIM_FIRST}-09-01", end=CUTOFF.isoformat()),
                resolution="site point",
                support="containing_pixel",
                temporal="daily",
                aggregation=f"{YEAR}: sum and count of days >= 50 mm from September 1 to the last "
                "day with a value in the source; each past year over the same calendar days "
                "(complete windows only); per phase: mean and median over the years of that "
                "phase; per month: mean of the same days over all past years.",
                method="now-2026 v1",
                doc_anchor=DOC_ANCHOR,
                ref=Ref(
                    label="NOAA CPC, ENSO operational definition (ONI >= +/-0.5 for 5 consecutive "
                    "overlapping seasons)",
                    url="https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/"
                    "ONI_v5.php",
                ),
                parameters={
                    "window_start": START.isoformat(),
                    "cutoff": CUTOFF.isoformat(),
                    "phase_season": SEASON,
                    "heavy_rain_mm": HEAVY_MM,
                    "climatology_years": f"{CLIM_FIRST}-{CLIM_LAST}",
                    "compare_years": ",".join(str(y) for y in COMPARE_YEARS),
                },
                inputs=[*upstream, cp.oni_prov_id(site_id)],
                limitations=[
                    f"{counts['el_nino']} El Niño, {counts['la_nina']} La Niña and "
                    f"{counts['neutral']} neutral springs in {CLIM_FIRST}-{CLIM_LAST}: one wet "
                    "year moves a phase mean.",
                    "A part of the season: the comparison holds only for the same calendar days; "
                    "the rest of November can still change the totals.",
                    f"Rain is measured; its effect on the {YEAR} wheat is not (see `reported`).",
                ],
                attribution=attribution,
            )
        )
        return rid

    prec = power_now_record(site, power_now)
    records.append(prec)
    sources.append(
        source_block(
            "nasa-power",
            "NASA POWER (MERRA-2 bias-corrected precipitation, PRECTOTCORR, LST days)",
            power_now.daily["PRECTOTCORR"],
            power_history,
            oni,
            phases,
            comp(
                "nasa-power",
                "NASA POWER",
                [prec.id, power_prov_id(site_id, "PRECTOTCORR")],
                [cp.NASA_POWER, cp.NOAA_ONI],
            ),
        )
    )
    im_end = last_valid_day(imerg_now.daily, START, CUTOFF)
    irec = imerg_now_record(site_id, imerg_now, im_end)
    records.append(irec)
    sources.append(
        source_block(
            "gpm-imerg",
            "GPM IMERG (via NASA POWER, UTC days)",
            imerg_now.daily,
            imerg_history.daily,
            oni,
            phases,
            comp(
                "gpm-imerg",
                "GPM IMERG",
                [irec.id, f"prov:imerg:{site_id}:imerg_prectot:daily"],
                [cp.NASA_IMERG, cp.NOAA_ONI],
            ),
        )
    )
    reported = []
    for r in REPORTS:
        rec = report_record(site_id, r)
        records.append(rec)
        reported.append(
            ReportedFact(
                id=r.rid,
                text=LocalizedText(en=r.text),
                reported_by=r.reported_by,
                published=r.published,
                url=r.url,
                provenance_id=rec.id,
            )
        )
    cur = current_enso(oni, phases, site_id)
    notes = [
        LocalizedText(
            en=f"GPM IMERG via NASA POWER ends on {im_end.isoformat()} at access, so the IMERG "
            f"block covers only September 1-{im_end.day}. The NASA GES DISC copies (Early, Late, "
            "Final) need an Earthdata login, which this pipeline does not use; the NASA POWER "
            "block is the only one that covers the window."
        ),
        LocalizedText(
            en="Ground check not possible yet: the ANA web service had no 2026 data for rain "
            "gauge 2853015 at access ('Sem dados para esta estação'), and the INMET A853 station "
            "service did not answer from the pipeline."
        ),
        LocalizedText(
            en=f"Current ENSO state: ONI {cur.season} {YEAR} = {cur.oni:+.2f} degC, operational "
            f"phase {cur.phase.replace('_', ' ')}; the SON {YEAR} season that sets the phase of "
            "the past years is not complete yet."
        ),
        LocalizedText(
            en="Arithmetic on the reported Emater figures: 2,833 / 2,968 kg/ha is 4.5% lower and "
            "763,121 / 1,166,163 ha is 34.6% lower, so most of the reported 37.48% production drop "
            "comes from the smaller planted area; the yield estimate was made mid-harvest."
        ),
    ]
    doc = SeasonToDate(
        schema_version=SCHEMA_VERSION,
        site_id=site_id,
        label=LocalizedText(
            en=f"Rain in the {YEAR} wheat harvest window so far (from September 1)"
        ),
        year=YEAR,
        cutoff=CUTOFF.isoformat(),
        heavy_rain_mm=HEAVY_MM,
        phase_season=SEASON,
        current=cur,
        oni_provenance_id=cp.oni_prov_id(site_id),
        sources=sources,
        reported=reported,
        notes=notes,
    )
    return doc, records
