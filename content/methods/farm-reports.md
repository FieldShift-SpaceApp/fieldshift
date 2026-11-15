---
anchor: farm-reports
title: Every farm, one free soil report - ZarcNM pre-check for each rural property from NASA data
order: 67
refs:
  - label: "Analysis folder with the scripts, tests and results (analysis/farm-reports)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/farm-reports
  - label: "SICAR public GeoServer (CAR property outlines, Serviço Florestal Brasileiro)"
    url: https://geoserver.car.gov.br/geoserver/sicar/wfs?service=WFS&request=GetCapabilities
  - label: "Embrapa Soja, Documentos 454 (2023): satellite method for the ZarcNM indicators"
    url: https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1156802/1/DOC-454.pdf
  - label: "Portaria SPA/MAPA 209/2026, ZarcNM soybean, Rio Grande do Sul 2026/27 (MAPA)"
    url: https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/portarias/safra-vigente/rio-grande-do-sul
limitations:
  - "Pre-check, not a certificate: the official management level comes only from Embrapa's SINM (IN SPA/MAPA 2/2025, items 3 and 4); every range here is conditional on three soil tests (V%, Ca, m%) that no satellite can read."
  - "CAR outlines are self-declared, mostly not yet analysed by the state agency, and overlap; area totals are sums over properties, not municipal hectares."
  - "No field calibration: the NDTI bare-soil threshold and the Embrapa straw ruler were not calibrated in Cruz Alta; the ruler saturates near 80% cover (straw levels 3 and 4 cannot be told apart) and kaolinite-rich soils can make bare soil read as straw."
  - "Contour sowing on slopes of 3% or more is never seen from space and is assumed confirmed; a missing contour forces NM1."
  - "Indicators are property-level medians over a 2021 cropland mask, read in calendar windows; the norm classifies each field in the month before its sowing."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from analysis/farm-reports (run of 2026-11-15 BRT); origin: the team generated the starting ideas at a human ideation meeting; at the team lead's request, SI helped compare and synthesize options from those ideas and verified data; the team chose the direction (D-001); human review pending (see SI-USAGE.md). -->

**Why.** The ZarcNM rule (IN SPA/MAPA 2/2025) places each soybean field of Rio Grande do Sul in a management level NM1-NM4, and in the 2026 pilot the premium subsidy is 20, 30, 35 or 40% for NM1 to NM4. Three of its six indicators (years without tillage T, straw cover C, crop diversity D) and the slope rule can be read from satellite data: the norm recommends Landsat, Sentinel-2 or HLS imagery (item 6.4; MODIS is accepted above 100 ha, item 6.4-I) and an elevation model "such as NASADEM or equivalent" for slope (item 6.3). This page runs that pre-check for **every rural property of Cruz Alta** in the public rural-property registry (CAR). Every number comes from [`analysis/farm-reports/`](../../analysis/farm-reports/README.md).

**Method.**

- **Properties:** CAR outlines from the public SICAR GeoServer (Serviço Florestal Brasileiro), active records only. The layer has no owner name, CPF or CNPJ; the CAR code stays outside the repository; only aggregates and one rounded anonymous example are published.
- **C:** NASA HLS and NASA/USGS Landsat 8/9, 1 Oct - 15 Nov 2026 (fallback 2025), 30 m; median NDTI of the cropland seen without green canopy, converted to % straw cover with the Embrapa Documentos 454 ruler; Table 1 band at cover ± 8.3 points; "level 3 or 4" above the ruler's 80% plateau.
- **T:** NASA/USGS Landsat 4-9 and HLS, 20 Oct - 20 Nov of every year since 1984; complete years since the last spring with ≥ 25% of the property's clear cropland probable bare soil (NDVI < 0.30, NDTI < 0.06).
- **D:** NASA HLS, April-November 2020-2026; the winter path of each 30 m pixel (wheat-like cereal, cover crop, fallow) from the [rotation fingerprint](#rotation-fingerprint) rules, and Table 1 row 6 on the 2023-2025 winters, summer assumed soybean.
- **Slope:** NASADEM; a mean cropland slope ≥ 3% means contour sowing must be confirmed (item 3.2.1-I).
- **Range:** the [ZarcNM rules](#zarcnm-precheck) applied to every combination of the observed levels with the three soil indicators at level 4 (or 3).

**What we found** (Cruz Alta, 15 November 2026):

| | Properties | Cropland (ha) |
|---|---|---|
| Active CAR records | 1,554 | — |
| With cropland in the mask | 1,509 | 108,574 |
| All three satellite indicators read | 1,286 | 104,100 |
| Upper end NM4 (soil tests at level 4) | 1,217 | 100,894 |
| Upper end NM3 | 53 | 2,118 |
| Upper end NM2 | 16 | 1,089 |
| Whole range NM3+ if soil tests at level 4 ("satellite-ready") | 1,263 | 102,774 |
| Whole range NM3+ if soil tests at level 3 | 1,223 | 100,953 |

- In the municipality that led no-till adoption, the satellite side is almost never the bottleneck: 98% of the assessed properties are "satellite-ready for NM3+". What stands between them and a level is the **soil test** (3 indicators) and **contour sowing**, which 1,284 of the 1,286 must confirm (mean slope ≥ 3%).
- Small properties (≤ 4 fiscal modules) are 1,139 of the 1,554 records but 24,061 ha of the cropland; they hold almost all the gaps (209 of the 223 properties not assessed), because a few 60 m pixels are not enough for the 40-year series.
- The years-without-tillage result depends on the bare-soil threshold: properties with a signature since 2019 go from 96 (NDTI 0.06) to 578 (NDTI 0.10).
- Each property's one-page report says, in plain words, which indicators the satellite read, which need a soil test, and what is still needed before Embrapa's SINM can issue the official level.

**How to scale.** The same code runs for any municipality the SICAR service covers; Cruz Alta took about 75 minutes on a home connection, all of it reading 1,039 scene windows. The time follows the scenes, not the properties, and neighbouring municipalities share scenes.
