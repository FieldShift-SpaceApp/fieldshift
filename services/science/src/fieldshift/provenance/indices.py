# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""FR19 provenance of the climate indices (issue #22): `computed`, with method, parameters and the
input records they come from (lineage to the NASA POWER records and to ET0)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fieldshift.contracts import LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.provenance import (
    ProvenanceMethod,
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)
from fieldshift.indices.climate import IndexParams
from fieldshift.provenance.power import (
    COMPLETE_MONTH_RULE,
    ET0_DOC_ANCHOR,
    FAO56_REF,
    _common_limitations,
    _period,
    et0_prov_id,
    power_prov_id,
)
from fieldshift.sites import SitePoint
from fieldshift.sources.power import RES_METEO, RES_SOLAR, PowerRaw

ETCCDI_REF = Ref(
    label="Zhang et al. (2011), ETCCDI indices for climate extremes",
    url="https://etccdi.pacificclimate.org/list_27_indices.shtml",
    doi="10.1002/wcc.147",
    citation=(
        "Zhang, X., Alexander, L., Hegerl, G.C., Jones, P., Klein Tank, A., Peterson, T.C., "
        "Trewin, B., Zwiers, F.W. (2011). Indices for monitoring changes in extremes based on "
        "daily temperature and precipitation data. WIREs Climate Change 2, 851-870."
    ),
)
GDD_REF = Ref(
    label="McMaster and Wilhelm (1997), growing degree-days",
    doi="10.1016/S0168-1923(97)00027-0",
    citation=(
        "McMaster, G.S., Wilhelm, W.W. (1997). Growing degree-days: one equation, two "
        "interpretations. Agricultural and Forest Meteorology 87, 291-300."
    ),
)
QUANTILE_REF = Ref(
    label="Hyndman and Fan (1996), sample quantiles (type 7)",
    doi="10.1080/00031305.1996.10473566",
    citation=(
        "Hyndman, R.J., Fan, Y. (1996). Sample quantiles in statistical packages. The American "
        "Statistician 50(4), 361-365."
    ),
)

# Method pages in content/methods must define these anchors (VL6; GUIDO + SURGEON).
DOC_ANCHORS = {
    "heat_days": "heat-days",
    "frost_days": "frost-days",
    "growing_degree_days": "growing-degree-days",
    "water_deficit": "water-deficit",
    "extreme_precip": "extreme-precip-p95",
    "et0": ET0_DOC_ANCHOR,
}

PLACEHOLDER = (
    "The {what} ({value}) is a generic default, not a crop- or site-specific value; the "
    "agronomist sets it per site (site.yaml, indices.{key})."
)


def index_prov_id(site_id: str, key: str) -> str:
    return f"prov:computed:{site_id}:{key}:daily"


def p95_prov_id(site_id: str, params: IndexParams) -> str:
    return f"prov:computed:{site_id}:precip_p{params.extreme_percentile:g}:{params.baseline_tag}"


def clim_prov_id(site_id: str, key: str, kind: str, params: IndexParams) -> str:
    return f"prov:computed:{site_id}:{key}:{kind}:{params.baseline_tag}"


def num(x: float) -> str:
    """35.0 -> '35', 0.5 -> '0.5' (labels)."""
    return f"{x:g}"


def tag(x: float) -> str:
    """35.0 -> '35', 35.5 -> '35p5', -2.0 -> 'm2' (ids)."""
    return num(x).replace(".", "p").replace("-", "m")


def _text(en: str) -> LocalizedText:
    return LocalizedText(en=en)


def _baseline_period(params: IndexParams) -> Period:
    return Period(
        start=f"{params.baseline_start_year}-01-01", end=f"{params.baseline_end_year}-12-31"
    )


@dataclass(frozen=True)
class DailyIndex:
    """One daily index written as a monthly series."""

    key: str  # VariableKey and IndexKey
    title: str
    code: str
    unit: str  # unit of the daily value
    monthly_unit: str
    temporal: Literal["count", "sum"]
    method: str
    anchor: str
    refs: tuple[Ref, ...]
    resolution: str
    extra_limitations: tuple[str, ...] = ()


def daily_indices(params: IndexParams) -> dict[str, DailyIndex]:
    p = params
    return {
        "heat_days": DailyIndex(
            "heat_days", f"Heat days (daily Tmax > {num(p.heat_tmax_c)} °C)", "HEAT_DAY", "days",
            "days", "count", "Count of days with daily maximum temperature above a threshold",
            DOC_ANCHORS["heat_days"], (ETCCDI_REF,), RES_METEO,
            ("Same form as the ETCCDI 'summer days' index (Tmax > 25 °C) with a site threshold.",),
        ),
        "frost_days": DailyIndex(
            "frost_days", f"Frost days (daily Tmin ≤ {num(p.frost_tmin_c)} °C)", "FROST_DAY",
            "days", "days", "count",
            "Count of days with daily minimum air temperature (2 m) at or below a threshold",
            DOC_ANCHORS["frost_days"], (ETCCDI_REF,), RES_METEO,
            ("Air temperature at 2 m from a ~50 km grid cell: ground frost in low spots can occur "
             "on days not flagged here. ETCCDI 'frost days' uses Tmin < 0 °C (strict); this "
             "index uses ≤ (architecture definition).",),
        ),
        "growing_degree_days": DailyIndex(
            "growing_degree_days", f"Growing degree-days (base {num(p.gdd_base_c)} °C)",
            "GDD", "degC_d", "degC_d", "sum",
            "Growing degree-days, simple average method: max(0, (Tmax + Tmin) / 2 - Tbase)",
            DOC_ANCHORS["growing_degree_days"], (GDD_REF,), RES_METEO,
            ("No upper temperature cutoff (McMaster and Wilhelm 1997, method 1).",),
        ),
        "water_deficit": DailyIndex(
            "water_deficit", "Climatic water deficit (ET0 − precipitation)", "ET0_MINUS_P", "mm/d",
            "mm", "sum",
            "Climatic water deficit: FAO-56 reference evapotranspiration minus precipitation",
            DOC_ANCHORS["water_deficit"], (FAO56_REF,), f"{RES_METEO} and {RES_SOLAR} (via ET0)",
            ("Positive = atmospheric demand above rainfall (deficit); negative = surplus. It is a "
             "climate indicator, not a soil water balance: no runoff, storage or crop "
             "coefficient.",),
        ),
        "extreme_precip_days": DailyIndex(
            "extreme_precip_days",
            f"Extreme precipitation days (> P{num(p.extreme_percentile)} of wet days, "
            f"{p.baseline_start_year}–{p.baseline_end_year})",
            "R95P_DAYS", "days", "days", "count",
            "Count of days with precipitation above the baseline wet-day percentile",
            DOC_ANCHORS["extreme_precip"], (ETCCDI_REF, QUANTILE_REF), RES_METEO,
        ),
        "extreme_precip_total": DailyIndex(
            "extreme_precip_total",
            f"Precipitation on extreme days (> P{num(p.extreme_percentile)} of wet days, "
            f"{p.baseline_start_year}–{p.baseline_end_year})",
            "R95PTOT", "mm/d", "mm", "sum",
            "Precipitation total on days above the baseline wet-day percentile (ETCCDI R95pTOT)",
            DOC_ANCHORS["extreme_precip"], (ETCCDI_REF, QUANTILE_REF), RES_METEO,
        ),
    }  # fmt: skip


def method_parameters(key: str, params: IndexParams) -> dict[str, float | str]:
    p = params
    if key == "heat_days":
        return {"tmax_threshold_degC": p.heat_tmax_c, "comparison": ">"}
    if key == "frost_days":
        return {"tmin_threshold_degC": p.frost_tmin_c, "comparison": "<="}
    if key == "growing_degree_days":
        return {"base_temperature_degC": p.gdd_base_c, "upper_cutoff": "none"}
    if key.startswith("extreme_precip"):
        return {
            "percentile": p.extreme_percentile,
            "wet_day_threshold_mm": p.wet_day_mm,
            "baseline": f"{p.baseline_start_year}-{p.baseline_end_year}",
            "quantile_method": "Hyndman-Fan type 7",
            "comparison": ">",
        }
    return {}


def placeholder_limitations(
    key: str, params: IndexParams, site_set: frozenset[str]
) -> list[LocalizedText]:
    items = []
    if key == "heat_days" and "heat_tmax_c" not in site_set:
        value = f"{num(params.heat_tmax_c)} °C"
        items.append(PLACEHOLDER.format(what="heat threshold", value=value, key="heat_tmax_c"))
    if key == "growing_degree_days" and "gdd_base_c" not in site_set:
        value = f"{num(params.gdd_base_c)} °C"
        items.append(PLACEHOLDER.format(what="base temperature", value=value, key="gdd_base_c"))
    return [_text(t) for t in items]


def _inputs(site_id: str, key: str, params: IndexParams) -> list[str]:
    if key == "heat_days":
        return [power_prov_id(site_id, "T2M_MAX")]
    if key == "frost_days":
        return [power_prov_id(site_id, "T2M_MIN")]
    if key == "growing_degree_days":
        return [power_prov_id(site_id, "T2M_MAX"), power_prov_id(site_id, "T2M_MIN")]
    if key == "water_deficit":
        return [et0_prov_id(site_id), power_prov_id(site_id, "PRECTOTCORR")]
    return [power_prov_id(site_id, "PRECTOTCORR"), p95_prov_id(site_id, params)]


def daily_index_record(
    site: SitePoint, raw: PowerRaw, spec: DailyIndex, params: IndexParams, site_set: frozenset[str]
) -> Provenance:
    how = "Count of flagged days" if spec.temporal == "count" else "Sum of daily values"
    return Provenance(
        id=index_prov_id(site.id, spec.key),
        data_type="computed",
        title=_text(f"{spec.title} from NASA POWER"),
        variable=ProvenanceVariable(code=spec.code, name=_text(spec.title), unit=spec.unit),
        spatial=ProvenanceSpatial(resolution=spec.resolution, support="containing_pixel"),
        temporal=ProvenanceTemporal(resolution="daily", period=_period(raw)),
        aggregation=_text(
            f"Index computed for each day before aggregation (ADR-3). {how} per calendar month "
            f"({spec.monthly_unit}). A day without every input is missing. {COMPLETE_MONTH_RULE}"
        ),
        method=ProvenanceMethod(
            name=spec.method,
            ref=spec.refs[0],
            doc_anchor=spec.anchor,
            parameters=method_parameters(spec.key, params) or None,
        ),
        inputs=_inputs(site.id, spec.key, params),
        refs=list(spec.refs),
        limitations=[
            *_common_limitations(site, raw),
            *[_text(t) for t in spec.extra_limitations],
            *placeholder_limitations(spec.key, params, site_set),
        ],
    )


def p95_record(site: SitePoint, raw: PowerRaw, params: IndexParams) -> Provenance:
    p = params
    return Provenance(
        id=p95_prov_id(site.id, p),
        data_type="computed",
        title=_text(
            f"P{num(p.extreme_percentile)} of wet-day precipitation, "
            f"{p.baseline_start_year}–{p.baseline_end_year}, from NASA POWER"
        ),
        variable=ProvenanceVariable(
            code=f"PRECIP_P{tag(p.extreme_percentile)}",
            name=_text(f"Daily precipitation percentile P{num(p.extreme_percentile)} (wet days)"),
            unit="mm/d",
        ),
        spatial=ProvenanceSpatial(resolution=RES_METEO, support="containing_pixel"),
        temporal=ProvenanceTemporal(resolution="daily", period=_baseline_period(p)),
        aggregation=_text(
            f"Percentile P{num(p.extreme_percentile)} (linear interpolation, Hyndman-Fan type 7) "
            f"of daily precipitation on wet days (>= {num(p.wet_day_mm)} mm) of "
            f"{p.baseline_start_year}–{p.baseline_end_year}. Computed only when every day of the "
            "baseline is valid."
        ),
        method=ProvenanceMethod(
            name="Wet-day precipitation percentile (ETCCDI R95p threshold)",
            ref=ETCCDI_REF,
            doc_anchor=DOC_ANCHORS["extreme_precip"],
            parameters=method_parameters("extreme_precip_days", p),
        ),
        inputs=[power_prov_id(site.id, "PRECTOTCORR")],
        refs=[ETCCDI_REF, QUANTILE_REF],
        limitations=[
            *_common_limitations(site, raw),
            _text(
                "ETCCDI uses the 1961–1990 base period; POWER starts in 1981, so the baseline "
                f"here is {p.baseline_start_year}–{p.baseline_end_year} (ADR-3)."
            ),
            _text(
                "Grid-cell precipitation smooths local storms: the percentile is lower than at a "
                "rain gauge."
            ),
        ],
    )


def clim_record(
    site: SitePoint,
    raw: PowerRaw,
    *,
    key: str,
    kind: Literal["by_month", "annual_mean"],
    title: str,
    code: str,
    unit: str,
    source_id: str,
    source_period_unit: str,
    method: ProvenanceMethod,
    refs: list[Ref],
    resolution: str,
    params: IndexParams,
    extra_limitations: list[LocalizedText] | None = None,
) -> Provenance:
    p = params
    span = f"{p.baseline_start_year}–{p.baseline_end_year}"
    if kind == "by_month":
        agg = (
            f"Mean of the monthly values ({source_period_unit}) for each calendar month over "
            f"{span}. A calendar month is null unless every year of {span} has a value."
        )
        res = "monthly"
        full = f"{title}, mean by calendar month {span}"
    else:
        agg = (
            f"Mean over {span} of the yearly total (sum of the 12 monthly values, "
            f"{source_period_unit}). Reported only when every month of {span} has a value."
        )
        res = "annual"
        full = f"{title}, annual mean {span}"
    return Provenance(
        id=clim_prov_id(site.id, key, kind, p),
        data_type="computed",
        title=_text(f"{full} (NASA POWER)"),
        variable=ProvenanceVariable(code=code, name=_text(title), unit=unit),
        spatial=ProvenanceSpatial(resolution=resolution, support="containing_pixel"),
        temporal=ProvenanceTemporal(resolution=res, period=_baseline_period(p)),
        aggregation=_text(agg),
        method=method,
        inputs=[source_id],
        refs=refs,
        limitations=[
            *_common_limitations(site, raw),
            _text(f"Climatology of the reference period {span} (ADR-3), not a forecast."),
            *(extra_limitations or []),
        ],
    )
