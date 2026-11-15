---
anchor: residue-landsat
title: Straw, not bare soil - 40 years of Cruz Alta cropland in NASA/USGS Landsat and NASA HLS
order: 65
refs:
  - label: "Analysis folder with scripts, results, figure and the full write-up (analysis/residue-landsat)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/residue-landsat
  - label: "Landsat Collection 2 Level-2 Science Products (USGS / NASA)"
    url: https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products
  - label: "HLS v2.0 L30 (NASA LP DAAC), doi:10.5067/HLS/HLSL30.002"
    url: https://doi.org/10.5067/HLS/HLSL30.002
  - label: "HLS v2.0 S30 (NASA LP DAAC), doi:10.5067/HLS/HLSS30.002"
    url: https://doi.org/10.5067/HLS/HLSS30.002
  - label: "Microsoft Planetary Computer STAC (collections landsat-c2-l2, hls2-l30, hls2-s30, esa-worldcover; anonymous access)"
    url: https://planetarycomputer.microsoft.com/api/stac/v1
  - label: "Hively et al. (2021), Evaluation of SWIR crop residue bands for the Landsat Next mission, Remote Sensing 13:3718 (its ref. 25 is the NDTI origin: Van Deventer et al. 1997, Photogrammetric Engineering & Remote Sensing 63:87-93, no DOI)"
    url: https://doi.org/10.3390/rs13183718
  - label: "Zheng et al. (2014), Remote sensing of crop residue and tillage practices, Soil & Tillage Research 138:26-34"
    url: https://doi.org/10.1016/j.still.2013.12.009
  - label: "Quemada & Daughtry (2016), crop residue indices under varying moisture, Remote Sensing 8:660"
    url: https://doi.org/10.3390/rs8080660
  - label: "Roy et al. (2016), Landsat-7 to Landsat-8 reflectance continuity, Remote Sensing of Environment 185:57-70"
    url: https://doi.org/10.1016/j.rse.2015.12.024
  - label: "IBGE Censo Agropecuário 2006 (SIDRA table 849) and 2017 (table 6855), no-till area"
    url: https://sidra.ibge.gov.br/tabela/6855
limitations:
  - "No field calibration: 'probable bare soil' is NDVI < 0.30 and NDTI < 0.06, a spectral inference with a threshold chosen by the team (no published NDTI threshold transfers to these soils); the series shows when the bare-soil signature was common and when it became rare, not hectares of ploughed land or % residue cover."
  - "The level of the early years depends on the threshold and the sensor transform (1984-1994 median 2.2% to 19.9% across NDTI 0.04-0.12; 2.6% after the Roy et al. 2016 TM/ETM+ to OLI transform); the direction of the change does not."
  - "No Landsat 5 TM and Landsat 8 OLI scenes overlap in time; the sensor pairs (within about 2 points) all fall in 1999-2026, when bare soil is rare, so the sensor effect at the 1980s-90s level is not measured."
  - "Wet soil narrows the NDTI gap between soil and straw (Quemada & Daughtry 2016): scenes with 10 mm or more of rain in the 3 days before show less probable bare soil (1984-1999: 2.4% against 9.7%, 7 against 7 scenes). Rain is read at one point, not at each field."
  - "NDTI can mistake kaolinite-rich soil for straw (Hively et al. 2021), and the Oxisols here are probably kaolinite-rich: that hides bare soil, so recent near-zero values are not proof of zero."
  - "One or two clear scenes a year (gaps in 1985, 1989, 1990, 1996, 1997, 2002, 2020 and 2026 for Landsat), on moving dates; one cropland mask (ESA WorldCover 2021) for 1984-2026. The year of change is uncertain by a few years, and the satellite alone does not prove that no-till caused it."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the scripts and results in analysis/residue-landsat (run of 2026-11-15 02:32 UTC); the idea was synthesized with AI at the team lead's request and adopted by the team; human review pending (see SI-USAGE.md). -->

**Why this analysis.** The team's bare-soil calendar counts cropland with NDVI < 0.25 and warns that it cannot tell dry straw from bare soil. Crop residue absorbs shortwave-infrared light near 2,100-2,300 nm (cellulose and lignin) and soil does not, so the two SWIR bands that every Landsat since 1984 and NASA HLS carry can separate them. This analysis asks how much of Cruz Alta's cropland looked like bare soil in late October to mid November, before the soybean canopy closes, in every year from 1984 to 2026. Every number comes from [`analysis/residue-landsat/`](../../analysis/residue-landsat/README.md), rerun with one command.

**Data.** All Landsat Collection 2 Level-2 scenes (Landsat 5 TM, 7 ETM+, 8 OLI, 9 OLI-2; WRS-2 223/080 and 222/080) and NASA HLS v2.0 L30/S30 granules (tiles T22JBP and T22JBN) from 20 October to 20 November and from 1 April to 31 May, read anonymously through the Microsoft Planetary Computer. Clouds, shadows, water and fill are masked (`QA_PIXEL`, `Fmask`); cropland is ESA WorldCover 2021 class 40 inside the IBGE municipal polygon, read at about 60 m. A scene counts when at least half of the cropland is clear: 317 of 739 (185 Landsat, 132 HLS).

**Classes.** Green: NDVI >= 0.30 (the mask "many agricultural studies" use before reading residue, Hively et al. 2021). Of the rest, straw if NDTI = (SWIR1 - SWIR2)/(SWIR1 + SWIR2) (Van Deventer et al. 1997) is 0.06 or more, probable bare soil if lower. The literature defines tillage classes in residue cover (conservation tillage above 30% after planting), and turning NDTI into residue cover needs a field-calibrated regression per region (Zheng et al. 2014) that does not exist for Cruz Alta, so 0.06 is a stated choice with 0.04 to 0.12 shown. The cellulose absorption index (Daughtry et al. 2005) needs narrow bands no Landsat or HLS sensor has.

**Result.** In late October to mid November, probable bare soil was **5.7% of the cropland in the median year of 1984-1994** (22.1% in 1991) and has been **at or below 2.2% every year since 1995, 0.3% in the median year since 2005, and 0.3% in 2026** (HLS S30, 20 October). What is not green in November is now mostly straw. A before/after map of the same cropland (4 November 1991 against 20 October 2026) shows 20.0% against 0.3% probable bare soil; 1991 is the series maximum, not a typical early year.

**Independent check.** The IBGE Censo Agropecuário reports no-till on straw on 74,003 ha of Cruz Alta in 2006 and 105,036 ha in 2017, about 84% and 108% of the soybean + maize planted area of those years (IBGE PAM): no-till was near-universal by then, which matches the satellite's near-zero bare soil around both census years. The census does not date the adoption.

**Checks.** Wet scenes show less bare soil, so rain does not explain the fall. Near-simultaneous sensor pairs (Landsat 5/7, 7/8, 8/9, HLS L30 against Landsat, HLS S30 against L30) agree within about 2 points. The Roy et al. (2016) ETM+ to OLI transform lowers the early years (1984-1994 median 2.6%) but keeps them about ten times the recent ones. Results, per-scene values and every variant are in `analysis/residue-landsat/results/`.
