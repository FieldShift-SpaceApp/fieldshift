# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""ENSO-phase skill of February forecasts for the JJA winter (forecast scorecard).

Every source is scored on the same issue month (February) and the same target (JJA), against the
observed ONI JJA phase. This is skill at the ENSO phase, not a local crop or rain outcome.
"""

from __future__ import annotations

import csv
from pathlib import Path

from fieldshift.complements import provenance as cp
from fieldshift.complements.oni import OniFile, threshold_phase
from fieldshift.contracts import SCHEMA_VERSION, LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.forecast import (
    ForecastRecord,
    ForecastScore,
    ForecastScorecard,
    ForecastSource,
    ObservedWinter,
)
from fieldshift.errors import PipelineError

INPUT = "enso-forecasts.csv"
ISSUE_MONTH = 2
FIRST_YEAR, LAST_YEAR = 1982, 2025  # JJA 2026 is still preliminary in the ONI file
DOC_ANCHOR = "enso-forecast-skill"
# Display order: NASA GMAO first (priority of the complement), then the consensus products.
SOURCE_ORDER = tuple(cp.FORECAST_SOURCES)
TIE_ORDER = ("neutral", "el_nino", "la_nina")  # a tie between the largest categories -> neutral


def scores_prov_id(site_id: str) -> str:
    return f"prov:computed:{site_id}:enso-forecast-skill"


def load_forecasts(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        raise PipelineError(f"forecast input missing: {path}")
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        if r["source_id"] not in cp.FORECAST_SOURCES:
            raise PipelineError(f"{path.name}: unknown source_id {r['source_id']!r}")
        if not r["source_url"].startswith("https://"):
            raise PipelineError(f"{path.name}: row without a source URL: {r}")
    return rows


def _predicted(probs: tuple[float, float, float]) -> str:
    by = dict(zip(("la_nina", "neutral", "el_nino"), probs, strict=True))
    top = max(by.values())
    return next(p for p in TIE_ORDER if by[p] == top)


def _score(
    source_id: str,
    recs: list[ForecastRecord],
    obs: dict[int, ObservedWinter],
    clim_el_nino: float,
    prov_id: str,
) -> ForecastScore:
    n = len(recs)
    en_obs = [r for r in recs if r.observed_phase == "el_nino"]
    en_fc = [r for r in recs if r.predicted_phase == "el_nino"]
    hits = sum(1 for r in en_fc if r.observed_phase == "el_nino")
    brier = brier_clim = brier_neutral = bss = None
    if recs[0].p_el_nino is not None:
        o = [1.0 if r.observed_phase == "el_nino" else 0.0 for r in recs]
        p = [r.p_el_nino for r in recs]
        brier = sum((a - b) ** 2 for a, b in zip(p, o, strict=True)) / n  # type: ignore[operator]
        brier_clim = sum((clim_el_nino - b) ** 2 for b in o) / n
        brier_neutral = sum(o) / n  # forecast P(El Niño) = 0 every year
        bss = round(1 - brier / brier_clim, 3) if brier_clim else None
    return ForecastScore(
        source_id=source_id,
        issue_month=ISSUE_MONTH,
        first_year=min(r.target_year for r in recs),
        last_year=max(r.target_year for r in recs),
        n=n,
        phase_hit_rate=round(sum(r.hit for r in recs) / n, 3),
        always_neutral_hit_rate=round(sum(r.observed_phase == "neutral" for r in recs) / n, 3),
        el_nino_observed=len(en_obs),
        el_nino_hits=hits,
        el_nino_forecasts=len(en_fc),
        false_alarm_ratio=round((len(en_fc) - hits) / len(en_fc), 3) if en_fc else None,
        brier_el_nino=None if brier is None else round(brier, 3),
        brier_climatology=None if brier_clim is None else round(brier_clim, 3),
        brier_always_neutral=None if brier_neutral is None else round(brier_neutral, 3),
        brier_skill_score=bss,
        provenance_id=prov_id,
    )


def build_scorecard(
    site_id: str, rows: list[dict[str, str]], oni: OniFile, accessed_at: str
) -> tuple[ForecastScorecard, list[Provenance]]:
    observed = {
        y: ObservedWinter(
            year=y, oni_jja=oni.values[("JJA", y)], phase=threshold_phase(oni.values[("JJA", y)])
        )
        for y in range(FIRST_YEAR, LAST_YEAR + 1)
    }
    clim = sum(o.phase == "el_nino" for o in observed.values()) / len(observed)
    forecasts: list[ForecastRecord] = []
    for r in rows:
        if int(r["issue_month"]) != ISSUE_MONTH:
            raise PipelineError(f"{INPUT}: only February issues are scored, got {r}")
        y = int(r["target_year"])
        if y not in observed:
            continue
        kind = cp.FORECAST_SOURCES[r["source_id"]][1]
        if kind == "probability":
            probs = (float(r["p_la_nina"]), float(r["p_neutral"]), float(r["p_el_nino"]))
            pred, extra = (
                _predicted(probs),
                dict(zip(("p_la_nina", "p_neutral", "p_el_nino"), probs, strict=True)),
            )
        else:
            anomaly = float(r["nino34_anomaly_degC"])
            pred, extra = threshold_phase(anomaly), {"nino34_anomaly": anomaly}
        forecasts.append(
            ForecastRecord(
                source_id=r["source_id"],
                issue_month=ISSUE_MONTH,
                target_year=y,
                **extra,
                predicted_phase=pred,
                observed_phase=observed[y].phase,
                hit=pred == observed[y].phase,
                source_url=r["source_url"],
            )
        )
    present = [s for s in SOURCE_ORDER if any(f.source_id == s for f in forecasts)]
    forecasts.sort(key=lambda f: (present.index(f.source_id), f.target_year))
    sid = scores_prov_id(site_id)
    records: list[Provenance] = []
    sources, scores = [], []
    for s in present:
        recs = [f for f in forecasts if f.source_id == s]
        period = Period(start=f"{recs[0].target_year}-06-01", end=f"{recs[-1].target_year}-08-31")
        rec = cp.forecast_record(site_id, s, accessed_at, period)
        records.append(rec)
        label, kind, provider, *_rest = cp.FORECAST_SOURCES[s]
        sources.append(
            ForecastSource(
                id=s,
                label=LocalizedText(en=label),
                kind=kind,
                provider=provider,
                real_time_from=cp.FORECAST_SOURCES[s][7],
                provenance_id=rec.id,
            )
        )
        scores.append(_score(s, recs, observed, clim, sid))
    card = ForecastScorecard(
        schema_version=SCHEMA_VERSION,
        site_id=site_id,
        target_season="JJA",
        observed=list(observed.values()),
        observed_provenance_id=cp.oni_prov_id(site_id),
        sources=sources,
        forecasts=forecasts,
        scores=scores,
    )
    first = min(f.target_year for f in forecasts)
    records.append(
        cp.computed(
            rid=sid,
            title="ENSO-phase skill of February forecasts for the JJA winter",
            code="enso_phase_skill",
            name="Hit rate, false-alarm ratio and Brier score",
            unit="1",
            period=Period(start=f"{first}-06-01", end=f"{LAST_YEAR}-08-31"),
            resolution="Niño-3.4 region",
            support="regional",
            temporal="annual",
            aggregation="Per source: all its February issues with an observed JJA, one per year.",
            method="enso-phase-skill v1",
            doc_anchor=DOC_ANCHOR,
            ref=Ref(
                label="Wilks, D.S. (2011). Statistical Methods in the Atmospheric Sciences, 3rd "
                "ed., ch. 8 (forecast verification).",
                doi="10.1016/C2017-0-03921-6",
            ),
            parameters={
                "issue_month": ISSUE_MONTH,
                "target_season": "JJA",
                "phase_threshold_degC": 0.5,
                "climatology_p_el_nino": round(clim, 3),
                "climatology_years": f"{FIRST_YEAR}-{LAST_YEAR}",
                "tie_rule": "largest probability; ties go to neutral",
            },
            inputs=[cp.oni_prov_id(site_id), *(r.id for r in records)],
            limitations=[
                "This is skill at the ENSO phase of the JJA winter, not a local measure of crop, "
                "rain "
                "or farm outcomes.",
                "Small samples: each source has 2 to 7 El Niño winters in its years; one winter "
                "moves the El Niño hit count by a large share. No confidence interval is given.",
                "Sources cover different years (n is given per source); compare rates with the "
                "'always neutral' rate of the same years, not across sources.",
                "Brier scores exist only for probability sources; climatology = frequency of "
                "El Niño "
                f"JJA in {FIRST_YEAR}-{LAST_YEAR} (ONI >= +0.5).",
            ],
            attribution=[cp.NASA_GMAO, cp.NOAA_ONI, cp.NOAA_NMME, cp.IRI, cp.CPC_IRI],
        )
    )
    return card, records
