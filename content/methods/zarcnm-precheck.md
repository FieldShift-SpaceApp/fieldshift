---
anchor: zarcnm-precheck
title: ZarcNM pre-check - how each winter path scores on Brazil's soil-management rule
order: 65
refs:
  - label: "Analysis folder with the rules module, tests and results (analysis/zarcnm-precheck)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/zarcnm-precheck
  - label: "Portaria SPA/MAPA 209/2026, ZarcNM soybean, Rio Grande do Sul 2026/27 (MAPA)"
    url: https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/portarias/safra-vigente/rio-grande-do-sul
  - label: "Resolução CGSR 111/2026, ZarcNM pilot subsidy (Legismap transcription)"
    url: https://legismap.com.br/leis-e-normas/resolucao-cgsr-n-111-de-28-04-2026
  - label: "McCool et al. (2006), residue mass-to-cover coefficients, quoting Gregory (1982)"
    url: https://topsoil.nserl.purdue.edu/isco/isco14/5%20Erosion%20Process%20&%20Control/Oral/T5-McCool-Residue%20Characteristics%20for%20Windl-USA.pdf
limitations:
  - "Pre-check, not a certificate: the official management level is produced only by Embrapa's SINM from registered field data (IN SPA/MAPA 2/2025, items 3 and 4)."
  - "3 of the 6 indicators (base saturation, calcium and aluminium saturation) need a soil test and are not observable from satellite; every NM range is conditional on them."
  - "Contour sowing on slopes of 3% or more and the useful soil depth are assumed compliant; either can force NM1."
  - "Straw cover is arithmetic (straw clock converted with US wheat mass-to-cover coefficients); no NDTI threshold was calibrated against field cover. Years without tillage is an assumption (8+ years of no-till)."
  - "The ZarcNM soybean subsidy has R$ 1 million in 2026 for four states (Resolução CGSR 111/2026), read on a transcription, not the DOU PDF. No soybean premium per hectare for Rio Grande do Sul was found, so no R$/ha is given."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the norm texts and analysis/zarcnm-precheck (run of 2026-11-15 BRT); the idea was synthesized with AI at the team lead's request and is confirmed by the team in D-001; human review pending (see SI-USAGE.md). -->

**Why this check.** Since 2026/27, Rio Grande do Sul soybean has a ZarcNM zoning: each field falls in a management level NM1-NM4, and in the 2026 pilot the federal premium subsidy for soybean is 20, 30, 35 or 40% for NM1 to NM4. The rule (IN SPA/MAPA 2/2025) scores six indicators; three of them (years without tillage T, straw cover C, crop diversity D) depend on what the farmer does in winter, and the norm names Landsat, Sentinel-2/HLS and NASADEM as the data to read them. This page shows how each winter path scores on those three. Every number comes from [`analysis/zarcnm-precheck/`](../../analysis/zarcnm-precheck/README.md).

**Method.**

- **Rules:** Table 1 of the IN (levels 1-4 for each indicator), the mean of the six levels (NM1 ≤ 1.75 < NM2 ≤ 2.75 < NM3 ≤ 3.50 < NM4), and the overriding locks of item 3.2.1 (no contour on slopes ≥ 3% → NM1; soybean on soybean → NM1; legume-only succession → NM2 at most; two indicators at level 1 → NM1; two at level 2 → NM2; aluminium saturation), plus the soil-depth limit of Portaria 209/2026 item 2.4. Each rule is tested with cases from the text.
- **T:** assumed 8+ years of no-till (level 4), to be checked against the Landsat series.
- **C:** November straw from the [straw clock](#storms-bare-soil), converted to % cover with Gregory's relation, cover = 1 − exp(−Am × kg/ha), Am 0.00024-0.00054 ha/kg.
- **D:** the norm's diversity rule applied to each path's 3-year calendar.
- **Soil tests:** not observable from satellite; ranges are given for each soil level.

**What we found** (soil tests at level 4, contour confirmed):

| Path | C | D | NM range | Subsidy |
|---|---|---|---|---|
| Soybean-wheat | 2-3 | 2 | NM2-NM3 | 30-35% |
| Soybean-cover (black oat + vetch) | 2-4 | 3 | NM3-NM4 | 35-40% |
| Soybean-fallow | 1-2 | 1 | NM1-NM2 | 20-30% |

- Each path: "pre-check: 3 of 6 indicators observable; contour to confirm".
- Fallow has diversity at level 1 whatever the straw, and read literally it is "soybean on soybean", which the rule sets to NM1.
- With soil tests at level 1, every path is NM1: the winter path cannot make up for the soil.
