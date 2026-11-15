---
anchor: rotation-fingerprint
title: Every field's winter, from space - the rotation fingerprint in NASA HLS
order: 66
refs:
  - label: "Analysis folder with scripts, results, maps, GIF and the full write-up (analysis/rotation-fingerprint)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/rotation-fingerprint
  - label: "HLS Landsat 30 m v2.0, HLSL30 (NASA LP DAAC)"
    url: https://doi.org/10.5067/HLS/HLSL30.002
  - label: "HLS Sentinel-2 30 m v2.0, HLSS30 (NASA LP DAAC)"
    url: https://doi.org/10.5067/HLS/HLSS30.002
  - label: "Claverie et al. (2018), the Harmonized Landsat and Sentinel-2 data set, RSE 219"
    url: https://doi.org/10.1016/j.rse.2018.09.002
  - label: "Microsoft Planetary Computer, HLS collections (anonymous access)"
    url: https://planetarycomputer.microsoft.com/dataset/hls2-s30
  - label: "IBGE PAM, SIDRA table 1612 (planted area)"
    url: https://sidra.ibge.gov.br/tabela/1612
  - label: "ESA WorldCover 2021 v200 (cropland mask, partner data, CC BY 4.0)"
    url: https://esa-worldcover.org/en/data-access
limitations:
  - "Classes are phenological hypotheses from NDVI dates, not field labels: T is any winter cereal sown in June-July (wheat, barley, triticale, rye and white oat look alike), C is any autumn-sown canopy gone by early November (black oat, ryegrass, mixes, grazed oat, volunteer or weeds, or a cereal sown early). A black oat cover and an early oat or wheat crop are confusable."
  - "The only independent check is a municipal total (IBGE PAM, 2020-2025, n = 6): T matches the PAM winter grains on average (39.9% against 40.7%) but not year by year (Pearson 0.41, mean difference 8.2 points). A pixel confusion matrix is impossible; the area agreement is only bounded (at most 81-99%, at least 5-50%)."
  - "The wheat/cover split (half a month) and the composite (median or maximum) are the most sensitive choices: they change 8-12% of the pixel-years and up to 14 points of T in a year. The median composite was chosen after a first look at 2020 with both."
  - "The diversity level counts one soybean per summer (summers are not classified), assumes winter crops are grasses, and cannot count species, so level 4 is never assigned; it is a pre-check of one of six ZARC-NM indicators, and item 2.2 forbids a level without all of them."
  - "No April-November 2019 granule of tile T22JBP on the Planetary Computer; 2026 is provisional (last granule 2 November, harvest not over, no PAM value yet). Pixels are classified one by one, without field boundaries; dates and durations have half-month resolution."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the scripts and results in analysis/rotation-fingerprint (run of 2026-11-15 BRT); origin: the team generated the starting ideas at a human ideation meeting; at the team lead's request, SI helped compare and synthesize options from those ideas and verified data; the team chose the direction (D-001); human review pending (see SI-USAGE.md). -->

**Why this analysis.** The winter decision the app is about (wheat, cover crop or fallow after soybean) leaves a signature in the green of each field, and the ZARC-NM rule (IN SPA/MAPA 2/2025) asks for exactly that history, from Landsat, Sentinel-2 or NASA HLS at 30 m, to score the diversity of crops in the last three agricultural years (Table 1, indicator 6). This analysis reads the winter of every 30 m cropland pixel of Cruz Alta in every year 2020-2026 from the NASA HLS NDVI series and treats each pixel's sequence as its rotation fingerprint. Every number comes from [`analysis/rotation-fingerprint/`](../../analysis/rotation-fingerprint/README.md), rerun with one command.

**Method.**

- **Data:** NASA HLS v2.0 L30 + S30, tile T22JBP, 1 April - 30 November 2020-2026 (584 granules read through the Microsoft Planetary Computer), red, NIR and Fmask on the native 30 m grid; ESA WorldCover 2021 cropland inside the IBGE municipal polygon (1,165,531 pixels, 104,898 ha).
- **Series:** per pixel and year, the median NDVI of the clear observations in each half-month (16 half-months), gaps filled linearly when at least 10 are clear.
- **Rules:** the green-up (first half-month at NDVI >= 0.50 after the last half-month without canopy), the peak and the canopy end (first half-month below 0.40 after the peak) give one class: **T** wheat-like winter cereal (green-up July-1 to August-2, peak from August-2, canopy end from October-1; ZARC wheat window 1 June - 20 July), **C** winter cover crop (green by June-2, canopy end August-1 to November-1), **P** fallow (never 0.50 from June to September), **O** other.
- **Fingerprint and diversity:** the 2020-2026 sequence of each pixel (e.g. `CTCTCTC`), and for the winters 2023-2025 the satellite-visible part of indicator 6: 3 soybean summers plus the winter crops, cover-crop durations over 45 days and over 4 months.
- **Checks:** IBGE PAM planted area of all winter grains and of wheat (2020-2025), aggregate area-agreement bounds, a 12-run sensitivity grid.

**What we found.**

- T covers **25.6-53.3%** of the cropland in 2020-2025 (mean 39.9%), the PAM winter grains 27.8-47.8% of the soybean area (mean 40.7%); the level agrees on average, the year-by-year agreement is weak (Pearson 0.41, n = 6).
- Fallow with no green winter is **0.3-0.6%** of the cropland in every year 2020-2025; cover crops (C) 31-66%.
- Only **5.2%** of the pixels took the same winter path in all seven years; 93% took two or three paths; 97.3% were never fallow. The most common fingerprint, `CCCCCCC`, is 4.0% of the cropland.
- Winters 2023-2025: **66.5%** of the cropland meets the satellite-visible part of diversity level 3 and 33.5% level 2; level 4 needs four species, which NDVI cannot count (42.3% meet its cover-duration conditions).
- Three 9 ha example quadrats show the rule at work: cover every year (`CCCCCCC`) reaches level 3, wheat-like every year (`TTTTTTC`) stays at level 2 for lack of a cover crop.

**How to read it.** A map of what each field probably did in winter, and a pre-check of one ZARC-NM indicator from public NASA data, not a record of what was sown; the farmer's declaration (item 4.1 I) and the other five indicators are still needed.
