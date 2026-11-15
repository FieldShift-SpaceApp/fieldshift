---
anchor: seven-cities
title: Seven cities - the method run without tuning in six municipalities around Cruz Alta
order: 71
refs:
  - label: "Analysis folder with criteria, scripts, inputs and results (analysis/seven-cities)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/seven-cities
  - label: "GPM IMERG Final V07 (Huffman et al. 2023), daily, via SERVIR ClimateSERV"
    url: https://doi.org/10.5067/GPM/IMERG/3B-HH/07
  - label: "NASA POWER Daily API"
    url: https://power.larc.nasa.gov/
  - label: "MODIS MOD13Q1 v061 and MCD43A4 v061"
    url: https://doi.org/10.5067/MODIS/MOD13Q1.061
  - label: "NOAA CPC Oceanic Niño Index"
    url: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
  - label: "IBGE PAM, SIDRA table 1612"
    url: https://sidra.ibge.gov.br/tabela/1612
limitations:
  - "Same region, same crops, same assumed crop calendar (to be validated by an agronomist), Cruz Alta altitude and one CONAB cost region for all seven; another climate or production system has not been tested."
  - "Only 4 El Niño years (June–August ONI) in 2000–2024; the satellite criterion and the straw signal are read from the team's tables (the straw extraction requires a Google Earth Engine account), and the margins are not re-run (CONAB costs are not redistributed)."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from analysis/seven-cities (FieldShift team research, test of 15 November 2026; public re-run of 2026-11-15); human review pending (see SI-USAGE.md). -->

**What it is.** A portability test from the FieldShift team research: the rotation-risk checks built in Cruz Alta were run, unchanged, in Cruz Alta and six neighbouring municipalities (Ijuí, Jóia, São Miguel das Missões, São Luiz Gonzaga, Espumoso, Júlio de Castilhos), against four criteria written before running: (C1) the FAO-56 soil water model, driven by NASA POWER and GPM IMERG, tracks the municipality's IBGE soybean yield (r ≥ 0.60); (C2) a winter crop does not change the water of the next soybean (≤ 0.5 years in 10); (C3) the MODIS pattern of cover repeats (a green winter covers July–September and leaves October–November more exposed, under straw); (C4) El Niño years have more September–November days with ≥ 50 mm.

**Result.** Five municipalities pass all four criteria; Ijuí and São Luiz Gonzaga pass three (C2 fails: wheat changes soybean water by −1.3 and +0.8 years in 10). The method travels; the conclusions do not, so every new place needs its own run.

**Reproducibility.** C1, C2, C4 and the climate and yield columns were re-run from the committed public inputs and match the team's tables exactly; the ENSO phases match NOAA's file.

**ENSO phase.** Here the phase is the June–August ONI and El Niño is compared with all other years (Cruz Alta: 7.5 against 2.2 days ≥ 50 mm). The heavy-rain signal of the app uses the September–November ONI phase and compares El Niño with La Niña (4.4 against 1.4 days), so the two numbers answer different questions.
