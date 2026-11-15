---
anchor: enso-heavy-rain
title: Heavy rain in the wheat harvest window (September-November) by ENSO phase
order: 61
refs:
  - label: "NOAA CPC, ENSO operational definition and ONI"
    url: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php
  - label: "NASA POWER Daily API (PRECTOTCORR; IMERG_PRECTOT in UTC days)"
    url: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
  - label: "Huffman, G.J. et al. GPM IMERG Final Precipitation L3 Half Hourly 0.1° V07, NASA GES DISC"
    url: https://doi.org/10.5067/GPM/IMERG/3B-HH/07
  - label: "ANA HidroWeb web service, rain gauge 2853015 (Três Capões)"
    url: https://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica?codEstacao=2853015&dataInicio=&dataFim=&tipoDados=2&nivelConsistencia=
limitations:
  - "Few events: complete springs (El Niño / neutral / La Niña) are 15 / 16 / 13 for NASA POWER in 1982-2025, 9 / 10 / 9 for GPM IMERG in 1998-2025 and 13 / 13 / 13 for the rain gauge; a mean of heavy-rain days moves with one wet year."
  - "An association year by year, not a model of the wheat: it does not say how much harvest rain cost in yield."
  - "GPM IMERG via POWER starts in 1998, is served in UTC days, and its run (Early, Late, Final) and version are not stated by POWER."
  - "The rain gauge has a gap in 2013-2016 and a step of about +10-13% after it against neighbouring gauges; only complete September-November windows are counted."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from services/science/src/fieldshift/complements/rain_signal.py (EECOM, complements); review by GUIDO + SURGEON pending (see SI-USAGE.md). -->

**What it is.** For each year 1982-2025, the rain total of September-November (the wheat harvest window in the Planalto Médio) and the number of days with **50 mm or more**, grouped by the ENSO phase of that spring. Three rain sources side by side: **NASA POWER** (`PRECTOTCORR`, the grid cell of the site point), **GPM IMERG** (NASA, served by the POWER API as `IMERG_PRECTOT`), and the **ANA 2853015** rain gauge, 14.9 km away, as the ground check.

**Phase of a year.** NOAA CPC operational rule on the ONI: El Niño (La Niña) when the ONI is ≥ +0.5 °C (≤ −0.5 °C) for at least five consecutive overlapping seasons; the phase of the SON season of the year is used.

**How we compute it.** `fieldshift complements` reads the committed raw caches (`data/cache/power/`, `data/cache/power-imerg/`, `data/cache/noaa/`) and the gauge file `data/sites/cruz-alta/input/ana-2853015-sep-nov-daily.csv`. A year counts for a source only when every day of September-November has a value in it. Per phase: number of complete years, mean heavy-rain days, mean and median total, and years with at least one heavy-rain day. If IMERG came back as fill values only (−999), it would be declared in `notes` and only NASA POWER shown. The NASA POWER cache is chosen by what it holds, not by its file name: it must have a value on every September-November day of 1982-2025, or the run stops. Each source has one provenance record per metric (days ≥ 50 mm in days, window total in mm, complete years as a count), with the period and the number of complete years of that source.
