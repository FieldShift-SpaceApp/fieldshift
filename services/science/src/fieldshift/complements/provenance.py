# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""FR19 provenance records of the complements, each with its attribution group (v1.2.0):
NASA data, partner data (ESA Copernicus) and other public sources (NOAA, IRI, IBGE, ANA, BCB, MAPA,
CONAB, Embrapa) are kept apart."""

from __future__ import annotations

from fieldshift.contracts import LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.provenance import (
    Attribution,
    ProvenanceAccess,
    ProvenanceMethod,
    ProvenanceSource,
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)


def t(en: str) -> LocalizedText:
    return LocalizedText(en=en)


NASA_POWER = Attribution(
    group="nasa",
    name="NASA POWER (MERRA-2 bias-corrected precipitation)",
    credit="These data were obtained from the NASA Langley Research Center (LaRC) POWER Project "
    "funded through the NASA Earth Science/Applied Science Program.",
)
NASA_IMERG = Attribution(group="nasa", name="NASA GPM IMERG daily precipitation, served by POWER")
NASA_GMAO = Attribution(group="nasa", name="NASA GMAO GEOS-S2S seasonal forecast")
NASA_MODIS = Attribution(group="nasa", name="NASA MODIS MOD13Q1/MYD13Q1 v061 NDVI (LP DAAC)")
ESA_S2 = Attribution(
    group="partner",
    name="ESA Copernicus Sentinel-2 L2A and ESA WorldCover 2021",
    credit="Contains modified Copernicus Sentinel data [2019-2025]; ESA WorldCover project 2021 "
    "/ Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium.",
)
NOAA_ONI = Attribution(group="other_public", name="NOAA Climate Prediction Center (ONI, ERSSTv5)")
NOAA_NMME = Attribution(group="other_public", name="NOAA CPC North American Multi-Model Ensemble")
IRI = Attribution(group="other_public", name="IRI, Columbia University, ENSO forecast archive")
CPC_IRI = Attribution(group="other_public", name="NOAA CPC / IRI official ENSO consensus")
IBGE = Attribution(group="other_public", name="IBGE Produção Agrícola Municipal (SIDRA 1612)")
ANA = Attribution(group="other_public", name="ANA (Brazil), HidroWeb rain gauge 2853015")
BCB = Attribution(group="other_public", name="Banco Central do Brasil, SICOR rural credit")
MAPA = Attribution(group="other_public", name="MAPA (Brazil), ZARC agricultural risk zoning")
CONAB = Attribution(group="other_public", name="CONAB production cost series")
EMBRAPA = Attribution(group="other_public", name="Embrapa Trigo, Comunicado Técnico 207")
NOAA_CPC_DISC = Attribution(group="other_public", name="NOAA CPC ENSO Diagnostic Discussion")

TERMS_NOAA = "https://www.weather.gov/disclaimer"
TERMS_IRI = "https://iri.columbia.edu/resources/data-library/"


def oni_prov_id(site_id: str) -> str:
    return f"prov:noaa:{site_id}:oni"


def oni_record(site_id: str, url: str, accessed_at: str, period: Period) -> Provenance:
    return Provenance(
        id=oni_prov_id(site_id),
        data_type="modeled",
        title=t("Oceanic Niño Index (ONI), 3-month running mean of Niño-3.4 SST anomalies"),
        source=ProvenanceSource(
            dataset="Oceanic Niño Index",
            provider="NOAA Climate Prediction Center",
            product="oni.ascii.txt (ERSSTv5, centered 30-year base periods)",
            version="ERSSTv5",
        ),
        variable=ProvenanceVariable(code="ONI", name=t("ONI"), unit="delta_degC"),
        spatial=ProvenanceSpatial(
            resolution="Niño-3.4 region (5N-5S, 170W-120W)", support="regional"
        ),
        temporal=ProvenanceTemporal(resolution="monthly", period=period),
        aggregation=t("Read as published: one value per overlapping 3-month season."),
        access=ProvenanceAccess(
            url=url,
            accessed_at=accessed_at,
            terms_url=TERMS_NOAA,
            license="US Government work, public domain",
        ),
        limitations=[
            t(
                "ONI is an index of the tropical Pacific, not a local measurement; NOAA revises "
                "past "
                "values when the ERSST base period changes (2009 JJA is exactly +0.50)."
            ),
            t(
                "Since 2026 NOAA CPC verifies its official outlooks with the relative ONI (RONI); "
                "this dataset uses ONI, so a few borderline years may change phase under RONI."
            ),
        ],
        attribution=[NOAA_ONI],
    )


# ------------------------------------------------------------------ forecast sources

FORECAST_SOURCES = {
    # id: (label, kind, provider, product, version, access url, terms, real_time_from, attribution)
    "nmme-nasa-geos": (
        "NASA GMAO GEOS-S2S (NMME member NASA_GEOS5v2), ensemble-mean Niño-3.4",
        "nino34_anomaly",
        "NASA GMAO via NOAA CPC NMME",
        "NMME ENSO files, NASA_GEOS5v2/020100 (February starts)",
        "NASA_GEOS5v2",
        "https://ftp.cpc.ncep.noaa.gov/NMME/ENSO/NASA_GEOS5v2/020100/",
        TERMS_NOAA,
        2011,
        [NASA_GMAO, NOAA_NMME],
    ),
    "iri-plume-nasa-gmao": (
        "NASA GMAO model line in the IRI ENSO plume",
        "nino34_anomaly",
        "NASA GMAO via IRI",
        "IRI ENSO forecast archive, figure 4 (model plume), line 'NASA GMAO'",
        "archive",
        "https://ensoforecast.iri.columbia.edu/",
        TERMS_IRI,
        None,
        [NASA_GMAO, IRI],
    ),
    "iri-plume-mean": (
        "IRI ENSO plume, average of all models",
        "nino34_anomaly",
        "IRI, Columbia University",
        "IRI ENSO forecast archive, figure 4 (model plume), line 'COMBINED AVG'",
        "archive",
        "https://ensoforecast.iri.columbia.edu/",
        TERMS_IRI,
        None,
        [IRI],
    ),
    "iri-objective": (
        "IRI objective probabilistic ENSO forecast",
        "probability",
        "IRI, Columbia University",
        "IRI ENSO forecast archive, figure 3 (objective probabilities)",
        "archive",
        "https://ensoforecast.iri.columbia.edu/",
        TERMS_IRI,
        None,
        [IRI],
    ),
    "cpc-iri-official": (
        "NOAA CPC / IRI official ENSO consensus (early-month)",
        "probability",
        "NOAA CPC and IRI",
        "Early-month official consensus table, IRI ENSO quick look page",
        "quick look archive",
        "https://iri.columbia.edu/our-expertise/climate/forecasts/enso/",
        TERMS_IRI,
        None,
        [CPC_IRI],
    ),
}


def forecast_prov_id(site_id: str, source_id: str) -> str:
    return f"prov:forecast:{site_id}:{source_id}"


def forecast_record(site_id: str, source_id: str, accessed_at: str, period: Period) -> Provenance:
    label, kind, provider, product, version, url, terms, rt_from, attribution = FORECAST_SOURCES[
        source_id
    ]
    limitations = [
        t(
            "Forecast issued in February for the June-August (JJA) mean of the same year; one "
            "value "
            "per year, so a single winter moves every rate by several points."
        ),
    ]
    if kind == "nino34_anomaly":
        limitations.append(
            t(
                "Only the ensemble mean is used; the predicted phase applies the "
                "+/-0.5 degC threshold to it, which understates strong phases."
            )
        )
    if source_id.startswith("iri-"):
        limitations.append(
            t(
                "Values read from the archive figures that the IRI server draws "
                "today (SVG coordinates, about 0.01 degC or 1 point of precision); the "
                "objective probabilities can differ from the text published at the "
                "time by up to 4 points."
            )
        )
    if source_id == "iri-objective":
        limitations.append(
            t(
                "The 2009 bars are 25/50/25 in all three issues, which may be the "
                "climatology rather than a forecast."
            )
        )
    if rt_from is not None:
        limitations.append(
            t(
                f"Years before {rt_from} are hindcasts (run later with the current "
                "model), not forecasts available at the time; the exact GEOS version "
                "behind each year was not checked."
            )
        )
    if source_id == "cpc-iri-official":
        limitations.append(
            t(
                "The archive has tables only from 2014; 2026 is left out (only the "
                "favored category is published, and JJA 2026 is still preliminary)."
            )
        )
    return Provenance(
        id=forecast_prov_id(site_id, source_id),
        data_type="modeled",
        title=t(f"{label}, February issue, target JJA"),
        source=ProvenanceSource(dataset=label, provider=provider, product=product, version=version),
        variable=ProvenanceVariable(
            code="P_ENSO" if kind == "probability" else "NINO34_JJA",
            name=t(
                "Probability of each ENSO phase"
                if kind == "probability"
                else "Forecast Niño-3.4 anomaly, JJA mean"
            ),
            unit="probability" if kind == "probability" else "delta_degC",
        ),
        spatial=ProvenanceSpatial(resolution="Niño-3.4 region", support="regional"),
        temporal=ProvenanceTemporal(resolution="annual", period=period),
        aggregation=t(
            "One forecast per year: the February issue, read for the JJA season. The "
            "URL of the file each value was read from is kept per row."
        ),
        access=ProvenanceAccess(url=url, accessed_at=accessed_at, terms_url=terms),
        limitations=limitations,
        attribution=attribution,
    )


def computed(
    *,
    rid: str,
    title: str,
    code: str,
    name: str,
    unit: str,
    period: Period,
    resolution: str,
    support: str,
    temporal: str,
    aggregation: str,
    method: str,
    doc_anchor: str,
    ref: Ref,
    parameters: dict[str, float | str],
    inputs: list[str],
    limitations: list[str],
    attribution: list[Attribution],
) -> Provenance:
    return Provenance(
        id=rid,
        data_type="computed",
        title=t(title),
        variable=ProvenanceVariable(code=code, name=t(name), unit=unit),
        spatial=ProvenanceSpatial(resolution=resolution, support=support),
        temporal=ProvenanceTemporal(resolution=temporal, period=period),
        aggregation=t(aggregation),
        method=ProvenanceMethod(name=method, ref=ref, doc_anchor=doc_anchor, parameters=parameters),
        inputs=inputs,
        limitations=[t(x) for x in limitations],
        attribution=attribution,
    )
