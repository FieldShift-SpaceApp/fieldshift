# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Season replay (winter 2023): measured events from input/replay-2023.yaml, plus the wheat
failure count computed here from the IBGE PAM files of the 18 Planalto Médio municipalities.

Failure rule (team analysis and its independent verification): yield below 75% of the
municipality's linear trend, fitted by least squares on 1981-2025 (years with a positive yield,
the year itself included, at least 10 years).
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import yaml

from fieldshift.complements import provenance as cp
from fieldshift.contracts import SCHEMA_VERSION, LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.provenance import (
    Attribution,
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)
from fieldshift.contracts.replay import EventTimeline, ReplayEvent, ReplayValue
from fieldshift.errors import PipelineError

INPUT = "replay-2023.yaml"
WHEAT_DIR = "ibge-wheat"
WHEAT_PRODUCT = "2716"
TREND_YEARS = (1981, 2025)
TARGET_YEAR = 2023
THRESHOLD = 0.75
SENSITIVITY = (0.70, 0.80)
MIN_YEARS = 10
HOME_MUNICIPALITY = "4306106"  # Cruz Alta
# The 18 Planalto Médio municipalities of the team analysis (IBGE codes), Cruz Alta included.
MUNICIPALITIES = frozenset(
    {
        "4300208", "4302220", "4304705", "4305702", "4306106", "4308458",
        "4310009", "4310207", "4311205", "4312658", "4313706", "4313904",
        "4314100", "4314308", "4316436", "4316709", "4317509", "4322202",
    }
)  # fmt: skip
DOC_ANCHOR = "season-replay"
SIDRA = "https://apisidra.ibge.gov.br/values/t/1612/n6/{code}/v/112/p/all/c81/2716"


def _yield_cell(path: Path, year: str, cell: str) -> float | None:
    """None = empty cell (SIDRA '..', '...', 'X': not available); 0.0 = SIDRA '-' (no harvest)."""
    if cell == "":
        return None
    try:
        return float(cell)
    except ValueError:
        raise PipelineError(f"{path}: year {year}: yield {cell!r} is not a number") from None


def load_yields(folder: Path) -> dict[str, dict[int, float]]:
    """Positive yields per municipality and year, for exactly the MUNICIPALITIES.

    Fails (with the file path) when a municipality file is missing or unexpected, when a year
    repeats, when the TARGET_YEAR yield is empty or zero, or when fewer than MIN_YEARS positive
    yields fall in TREND_YEARS: the failure count must never be taken on a smaller set.
    """
    files = {
        f.stem.split("_")[2]: f for f in sorted(folder.glob(f"pam_1612_*_{WHEAT_PRODUCT}.csv"))
    }
    if not files:
        raise PipelineError(f"no IBGE PAM wheat files in {folder}")
    missing, extra = sorted(MUNICIPALITIES - set(files)), sorted(set(files) - MUNICIPALITIES)
    if missing or extra:
        raise PipelineError(
            f"{folder}: IBGE PAM wheat files must be the {len(MUNICIPALITIES)} Planalto Médio "
            f"municipalities; missing {missing}, unexpected {extra}"
        )
    out: dict[str, dict[int, float]] = {}
    for code, f in sorted(files.items()):
        cells: dict[int, float | None] = {}
        with f.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                year = int(r["year"])
                if year in cells:
                    raise PipelineError(f"{f}: year {year} appears twice")
                cells[year] = _yield_cell(f, r["year"], r["yield_kg_ha"])
        target = cells.get(TARGET_YEAR)
        if target is None:
            raise PipelineError(f"{f}: no {TARGET_YEAR} wheat yield (row absent or empty cell)")
        if target <= 0:
            raise PipelineError(
                f"{f}: {TARGET_YEAR} wheat yield is {target:g} (SIDRA '-' = no harvest); the "
                "failure rule needs a yield"
            )
        positive = {y: v for y, v in cells.items() if v is not None and v > 0}
        history = sum(1 for y in positive if TREND_YEARS[0] <= y <= TREND_YEARS[1])
        if history < MIN_YEARS:
            raise PipelineError(
                f"{f}: {history} positive yields in {TREND_YEARS[0]}-{TREND_YEARS[1]}, the trend "
                f"needs at least {MIN_YEARS}"
            )
        out[code] = positive
    return out


def trend_ratio(series: dict[int, float], year: int) -> tuple[float, float] | None:
    """(trend value, yield / trend) for `year`, or None when the fit is not possible."""
    pts = [(y, v) for y, v in series.items() if TREND_YEARS[0] <= y <= TREND_YEARS[1]]
    if len(pts) < MIN_YEARS or year not in series:
        return None
    n = len(pts)
    mx = sum(y for y, _ in pts) / n
    my = sum(v for _, v in pts) / n
    slope = sum((y - mx) * (v - my) for y, v in pts) / sum((y - mx) ** 2 for y, _ in pts)
    trend = my + slope * (year - mx)
    return trend, series[year] / trend


def wheat_failures(yields: dict[str, dict[int, float]]) -> dict[str, float]:
    if set(yields) != MUNICIPALITIES:
        raise PipelineError(f"wheat yields must cover the {len(MUNICIPALITIES)} municipalities")
    ratios = {c: trend_ratio(s, TARGET_YEAR) for c, s in yields.items()}
    if any(r is None for r in ratios.values()):  # load_yields already checked each member
        raise PipelineError(
            f"no {TARGET_YEAR} trend for {sorted(c for c, r in ratios.items() if r is None)}"
        )
    out: dict[str, float] = {"municipalities": float(len(ratios))}
    for thr in (THRESHOLD, *SENSITIVITY):
        out[f"below_{round(thr * 100)}"] = float(sum(1 for _, q in ratios.values() if q < thr))
    trend, _ = ratios[HOME_MUNICIPALITY]
    out["home_yield"] = yields[HOME_MUNICIPALITY][TARGET_YEAR]
    out["home_trend"] = round(trend)
    return out


def _attribution(items: list[dict[str, str]]) -> list[Attribution]:
    return [Attribution(**a) for a in items]


def _event_record(site_id: str, ev: dict[str, Any], period: Period) -> Provenance:
    src = ev["source"]
    return Provenance(
        id=f"prov:user:{site_id}:replay-2023:{ev['id']}",
        data_type="user_provided",
        title=cp.t(ev["title"]),
        variable=ProvenanceVariable(
            code=ev["id"].replace("-", "_"), name=cp.t(ev["title"]), unit="1"
        ),
        spatial=ProvenanceSpatial(resolution="municipality / region", support="regional"),
        temporal=ProvenanceTemporal(
            resolution="static" if "date" in ev else "annual", period=period
        ),
        aggregation=cp.t("Transcribed from the primary source named in refs; no computation."),
        authored_by=src["authored_by"],
        refs=[Ref(**r) for r in src["refs"]],
        limitations=[cp.t(x) for x in src.get("limitations", [])],
        attribution=_attribution(src["attribution"]),
    )


def build_replay(site_id: str, input_dir: Path) -> tuple[EventTimeline, list[Provenance]]:
    path = input_dir / INPUT
    if not path.is_file():
        raise PipelineError(f"replay input missing: {path}")
    spec = yaml.safe_load(path.read_text(encoding="utf-8"))
    yields = load_yields(input_dir / WHEAT_DIR)
    records: list[Provenance] = []
    events: list[ReplayEvent] = []
    for ev in spec["events"]:
        when: dict[str, Any] = {"date": ev["date"]} if "date" in ev else {"period": ev["period"]}
        period = (
            Period(start=ev["date"], end=ev["date"]) if "date" in ev else Period(**ev["period"])
        )
        if ev.get("computed") == "wheat_failures":
            ev = {**ev, **_failures_event(site_id, yields, records)}
        else:
            records.append(_event_record(site_id, ev, period))
            ev = {**ev, "provenance_id": records[-1].id, "refs": ev["source"]["refs"]}
        events.append(
            ReplayEvent(
                id=ev["id"],
                kind=ev["kind"],
                **when,
                title=LocalizedText(en=ev["title"]),
                detail=LocalizedText(en=" ".join(str(ev["detail"]).split())),
                values=[
                    ReplayValue(
                        id=v["id"],
                        label=LocalizedText(en=v["label"]),
                        value=v["value"],
                        unit=v["unit"],
                    )
                    for v in ev.get("values", [])
                ],
                provenance_id=ev["provenance_id"],
                refs=[Ref(**r) for r in ev["refs"]],
            )
        )
    timeline = EventTimeline(
        schema_version=SCHEMA_VERSION,
        site_id=site_id,
        id=spec["id"],
        title=LocalizedText(en=spec["title"]),
        period=Period(**spec["period"]),
        events=events,
    )
    return timeline, records


def _failures_event(
    site_id: str, yields: dict[str, dict[int, float]], records: list[Provenance]
) -> dict[str, Any]:
    f = wheat_failures(yields)
    ibge_id = f"prov:user:{site_id}:ibge-pam-wheat-planalto"
    refs = [
        {"label": f"IBGE SIDRA 1612, wheat yield, municipality {c}", "url": SIDRA.format(code=c)}
        for c in sorted(yields)
    ]
    records.append(
        Provenance(
            id=ibge_id,
            data_type="user_provided",
            title=cp.t("IBGE PAM wheat yield, 18 municipalities of the Planalto Médio (RS)"),
            variable=ProvenanceVariable(
                code="yield_kg_ha", name=cp.t("Wheat yield (kg/ha)"), unit="1"
            ),
            spatial=ProvenanceSpatial(resolution="municipality", support="regional"),
            temporal=ProvenanceTemporal(
                resolution="annual", period=Period(start="1974-01-01", end="2025-12-31")
            ),
            aggregation=cp.t(
                "Annual municipal yield as published (SIDRA '-' = 0, '..', '...', 'X' = "
                "empty), downloaded by `fieldshift fetch ibge-pam --product 2716`; raw "
                "responses in data/cache/ibge/cruz-alta/."
            ),
            authored_by="IBGE, Produção Agrícola Municipal (official statistics)",
            refs=[Ref(**r) for r in refs],
            limitations=[
                cp.t(
                    "Official statistics, recorded as user_provided: the contracts have no "
                    "data type for them. Municipal averages, not field yields."
                )
            ],
            attribution=[cp.IBGE],
        )
    )
    rid = f"prov:computed:{site_id}:replay-2023:wheat-failures"
    records.append(
        cp.computed(
            rid=rid,
            title="Wheat failures in 2023 (yield below 75% of the linear trend)",
            code="wheat_failures_2023",
            name="Municipalities with yield below 75% of trend",
            unit="count",
            period=Period(start="1981-01-01", end="2025-12-31"),
            resolution="municipality",
            support="regional",
            temporal="annual",
            aggregation="Per municipality: least-squares linear trend of yield on 1981-2025 (years "
            "with a positive yield, 2023 included); 2023 yield divided by the trend value.",
            method="wheat-failure-count v1",
            doc_anchor=DOC_ANCHOR,
            ref=Ref(
                label="Team analysis of wheat and ENSO in the Planalto Médio and its independent "
                "verification (14/11/2026): 75% of the linear trend, 1981-2025"
            ),
            parameters={
                "threshold": THRESHOLD,
                "sensitivity": "0.70, 0.80",
                "trend_years": "1981-2025",
                "min_years": MIN_YEARS,
                "target_year": TARGET_YEAR,
            },
            inputs=[ibge_id],
            limitations=[
                "The count depends on the threshold: it is given at 70%, 75% and 80%.",
                "Neighbouring municipalities share the weather; 18 municipalities are one "
                "regional event, not 18 independent cases.",
            ],
            attribution=[cp.IBGE],
        )
    )
    n = int(f["municipalities"])
    return {
        "title": f"Wheat failed in {int(f['below_75'])} of {n} Planalto Médio municipalities",
        "detail": f"2023 wheat yield (IBGE PAM) below 75% of each municipality's 1981-2025 linear "
        f"trend in {int(f['below_75'])} of {n} municipalities ({int(f['below_70'])} at 70%, "
        f"{int(f['below_80'])} at 80%). Cruz Alta: {f['home_yield']:,.0f} kg/ha against a trend "
        f"of {f['home_trend']:,.0f} kg/ha.",
        "values": [
            {
                "id": "municipalities_below_75pct",
                "label": "Municipalities below 75% of trend",
                "value": f["below_75"],
                "unit": "count",
            },
            {
                "id": "municipalities_below_70pct",
                "label": "Municipalities below 70% of trend",
                "value": f["below_70"],
                "unit": "count",
            },
            {
                "id": "municipalities_below_80pct",
                "label": "Municipalities below 80% of trend",
                "value": f["below_80"],
                "unit": "count",
            },
            {
                "id": "municipalities",
                "label": "Municipalities with a 2023 wheat yield",
                "value": f["municipalities"],
                "unit": "count",
            },
            {
                "id": "cruz_alta_yield",
                "label": "Cruz Alta wheat yield 2023",
                "value": f["home_yield"],
                "unit": "kg/ha",
            },
            {
                "id": "cruz_alta_trend",
                "label": "Cruz Alta linear-trend yield for 2023",
                "value": f["home_trend"],
                "unit": "kg/ha",
            },
        ],
        "provenance_id": rid,
        "refs": [
            {
                "label": "IBGE SIDRA 1612, wheat yield (municipality 4306106)",
                "url": SIDRA.format(code=HOME_MUNICIPALITY),
            }
        ],
    }
