---
anchor: storms-bare-soil
title: Storms meet soil - heavy rain on cropland with no green, and the straw clock
order: 64
refs:
  - label: "Analysis folder with scripts, results, figure and the full write-up (analysis/storms-bare-soil)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/storms-bare-soil
  - label: "GPM IMERG Final Precipitation L3 Half Hourly V07 (NASA GES DISC), served daily by NASA POWER"
    url: https://doi.org/10.5067/GPM/IMERG/3B-HH/07
  - label: "NASA POWER daily point API"
    url: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
  - label: "ANA HidroWeb web service, HidroSerieHistorica, rain gauge 2853015"
    url: https://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica?codEstacao=2853015&dataInicio=&dataFim=&tipoDados=2&nivelConsistencia=
  - label: "Campos et al. (2011b), straw half-lives in the Cruz Alta long-term trial, RBCS 35(3)"
    url: https://doi.org/10.1590/S0100-06832011000300017
  - label: "Aita & Giacomini (2003), black oat dry matter, RBCS 27(4)"
    url: https://www.redalyc.org/pdf/1802/180214026004.pdf
  - label: "Santos et al. (ed.) (2019), Sistemas de produção para cereais de inverno, Embrapa (wheat and oat straw)"
    url: https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1111855/1/ID446652019LVSistemasdeproducao.pdf
limitations:
  - "NDVI < 0.25 does not separate straw from bare soil, so the exposure index ranks when storms fall on ground without a growing crop, not on unprotected ground. The straw clock is there to fill that gap with literature, not with a measurement."
  - "The straw clock is arithmetic from measured half-lives, not a field measurement: one long-term trial (Cruz Alta, no-till), a single exponential assumed, initial straw from other sites, management windows taken as scenarios, and no source that turns t/ha of straw into % of soil covered."
  - "Sentinel-2 (ESA partner data) covers 7 years (2019-2025) with one scene per half-month; the rain covers 25 years (2001-2025). The two curves describe different periods."
  - "Rain is a single point (IMERG 0.1-degree cell, POWER 0.5 x 0.625-degree cell, one gauge 14.9 km away) and cover a municipal share; neither is the field. POWER shows far fewer heavy-rain days than IMERG and the gauge, and IMERG and the gauge differ by up to about 20 points in some half-months."
  - "With 25 years, the 95% interval of a heavy-rain frequency is about plus or minus 18 points; only 5 observed heavy-rain days (2019-2025) fell when at least half of the cropland had no green."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the scripts and results in analysis/storms-bare-soil (run of 2026-11-14 BRT); the idea was synthesized with AI at the team lead's request and chosen by the team; human review pending (see SI-USAGE.md). -->

**Why this analysis.** Farmers fear a bare winter, but the team's Sentinel-2 calendar shows that cropland in Cruz Alta has the least green cover in April and November, not in winter. This analysis asks what the heavy rain measured by NASA's GPM IMERG falls on, half-month by half-month, and, because a satellite cannot tell dry straw from bare soil, how much winter straw a rotation still leaves on the ground when the November storms arrive. Every number comes from [`analysis/storms-bare-soil/`](../../analysis/storms-bare-soil/README.md), rerun with one command.

**Method.**

- **Heavy rain:** a day with ≥ 50 mm. Per half-month (days 1–15 and 16–end), share of the years 2001–2025 with at least one such day, from **GPM IMERG via NASA POWER** (main), NASA POWER `PRECTOTCORR` and the ANA rain gauge 2853015 (checks).
- **No green:** share of cropland with NDVI < 0.25 per half-month, Sentinel-2 10 m (median and range 2019–2025) beside MODIS 250 m, from the published [bare-soil calendar](#bare-soil-calendar).
- **Exposure index:** heavy-rain frequency × median no-green share. A ranking aid, not an erosion amount.
- **Straw clock:** `straw = initial × 2^(−days since management / half-life)`, half-lives from the Cruz Alta no-till trial (black oat 124 days, wheat 139 days; Campos et al. 2011b), initial straw from the literature (black oat 4.39–8.2 t/ha, wheat 3.0–4.12 t/ha), from scenario windows (wheat harvest 1 Oct – 30 Nov, oat desiccation 1 Sep – 31 Oct) to 1, 16 and 30 November.
- **Checks:** the September–November heavy-rain days recomputed here match the published [ENSO heavy-rain signal](#enso-heavy-rain) in every year for all three sources.

**What we found.**

| Half-month | Years with a day ≥ 50 mm, IMERG (95% interval) | Rain gauge | Cropland with no green, Sentinel-2 median (range) | Exposure rank |
|---|---|---|---|---|
| 1–15 Nov | 44% (27–63%) | 26% | 67.6% (27–79%) | 1 |
| 16–30 Apr | 40% (23–59%) | 29% | 46.5% (26–70%) | 2 |
| 16–30 Nov | 24% (12–43%) | 26% | 75.6% (49–84%) | 3 |

- Heavy rain happens all year (IMERG: 4–56% of the years per half-month); the half-months with the most heavy-rain years (16–30 September, 56%; 16–30 June, 52%) fall on green cropland.
- In 2019–2025, 5 of the 57 IMERG heavy-rain days with a Sentinel-2 scene in the same half-month fell when at least half of the cropland had no green, all in November.
- **Straw on 1 November (arithmetic, not measured):** black oat desiccated in September–October 3.1–8.2 t/ha; wheat harvested by then 2.6–4.1 t/ha; winter fallow, no winter straw.
