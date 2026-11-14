# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""FR19 provenance records for NASA POWER series and for ET0 computed from them."""

from __future__ import annotations

from fieldshift.contracts import LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.provenance import (
    ProvenanceAccess,
    ProvenanceMethod,
    ProvenanceSource,
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)
from fieldshift.sites import SitePoint
from fieldshift.sources.power import COMMUNITY, TERMS_URL, PowerParam, PowerRaw

ET0_INPUTS = ("T2M_MAX", "T2M_MIN", "T2MDEW", "WS2M", "ALLSKY_SFC_SW_DWN", "PS")
ET0_DOC_ANCHOR = "et0-fao56"  # content/methods must define it (VL6); see the PR description
FAO56_REF = Ref(
    label="Allen et al. (1998), FAO Irrigation and Drainage Paper 56",
    url="https://www.fao.org/4/x0490e/x0490e00.htm",
    citation=(
        "Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). Crop evapotranspiration - "
        "Guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56. "
        "FAO, Rome."
    ),
)

COMPLETE_MONTH_RULE = (
    "A month is reported only when every day of it has a valid daily value; otherwise it is "
    "null (no interpolation, ADR-3)."
)


def power_prov_id(site_id: str, code: str) -> str:
    return f"prov:power:{site_id}:{code.lower()}:daily"


def et0_prov_id(site_id: str) -> str:
    return f"prov:computed:{site_id}:et0:daily"


def _text(en: str) -> LocalizedText:
    return LocalizedText(en=en)


def _period(raw: PowerRaw) -> Period:
    return Period(start=raw.first_day.isoformat(), end=raw.last_day.isoformat())


def _common_limitations(site: SitePoint, raw: PowerRaw) -> list[LocalizedText]:
    items = [
        _text(
            "Regional signal: value of the grid cell that contains the site point "
            "(about 50-100 km), not a field measurement; no downscaling (ADR-3)."
        ),
        _text(
            "Daily values follow the time standard reported by the API "
            f"({raw.time_standard or 'n/a'})."
        ),
    ]
    if site.dev:
        items.insert(0, _text("DEV ONLY: development point, not a demo site."))
    return items


def power_record(site: SitePoint, raw: PowerRaw, p: PowerParam) -> Provenance:
    accessed_day = raw.accessed_at[:10].replace("-", "/")
    if p.aggregator == "sum":
        aggregation = (
            f"Calendar-month sum of daily values ({p.monthly_unit}). {COMPLETE_MONTH_RULE}"
        )
    else:
        aggregation = f"Calendar-month mean of daily values. {COMPLETE_MONTH_RULE}"
    limitations = [
        _text("Modeled (reanalysis-based) data, labeled 'modeled' (FR9)."),
        *_common_limitations(site, raw),
    ]
    if p.code.startswith("GWET"):
        limitations.append(
            _text(
                "Soil wetness is a 0-1 fraction of saturation from a land-surface model, not "
                "volumetric soil moisture (m3/m3) and not a satellite observation."
            )
        )
    return Provenance(
        id=power_prov_id(site.id, p.code),
        data_type="modeled",
        title=_text(f"NASA POWER · {raw.longnames[p.code]}"),
        source=ProvenanceSource(
            dataset="NASA POWER",
            provider="NASA Langley Research Center (LaRC)",
            product=f"{raw.api_name} (point), community {COMMUNITY}; upstream {p.upstream}",
            version=raw.api_version,
        ),
        variable=ProvenanceVariable(
            code=p.code, name=_text(p.label), unit=p.unit, native_unit=raw.native_units[p.code]
        ),
        spatial=ProvenanceSpatial(resolution=p.resolution, support="containing_pixel"),
        temporal=ProvenanceTemporal(resolution="daily", period=_period(raw)),
        aggregation=_text(aggregation),
        refs=[
            Ref(
                label="NASA POWER Referencing Guide",
                url=TERMS_URL,
                citation=(
                    "The data was obtained from National Aeronautics and Space Administration "
                    "(NASA) Langley Research Center's Prediction Of Worldwide Energy Resources "
                    "(POWER) project funded through the NASA Earth Science Division. "
                    f"{raw.api_name} {raw.api_version}, accessed {accessed_day}."
                ),
            )
        ],
        access=ProvenanceAccess(
            url=raw.url,
            accessed_at=raw.accessed_at,
            terms_url=TERMS_URL,
            license="NASA open data; cite as in the POWER Referencing Guide",
        ),
        limitations=limitations,
    )


def et0_record(site: SitePoint, raw: PowerRaw) -> Provenance:
    return Provenance(
        id=et0_prov_id(site.id),
        data_type="computed",
        title=_text("Reference evapotranspiration ET0 (FAO-56 Penman-Monteith) from NASA POWER"),
        variable=ProvenanceVariable(
            code="ET0", name=_text("Reference evapotranspiration"), unit="mm/d"
        ),  # fmt: skip
        spatial=ProvenanceSpatial(
            resolution="0.5° × 0.625° (meteorology) and 1° × 1° (radiation)",
            support="containing_pixel",
        ),
        temporal=ProvenanceTemporal(resolution="daily", period=_period(raw)),
        aggregation=_text(
            "ET0 computed for each day (FAO-56 eq. 6, G = 0), then summed per calendar month (mm). "
            "A day without every input is missing. " + COMPLETE_MONTH_RULE
        ),
        method=ProvenanceMethod(
            name="FAO-56 Penman-Monteith reference evapotranspiration, daily step",
            ref=FAO56_REF,
            doc_anchor=ET0_DOC_ANCHOR,
        ),
        inputs=[power_prov_id(site.id, code) for code in ET0_INPUTS],
        refs=[FAO56_REF],
        limitations=[
            *_common_limitations(site, raw),
            _text(
                "Inputs: actual vapour pressure from POWER dewpoint (FAO-56 eq. 14), solar "
                "radiation from POWER all-sky shortwave, pressure from POWER surface pressure, "
                f"elevation of the POWER grid cell ({raw.elevation_m:.0f} m) for clear-sky "
                "radiation."
            ),
            _text(
                "ET0 is the demand of a hypothetical grass reference surface, not the actual "
                "evapotranspiration of the crop."
            ),
        ],
    )
