---
anchor: satellite-vs-ground-check
title: Satellite and reanalysis vs. ground stations (Cruz Alta check)
order: 15
refs:
  - label: "INMET (Brazil's National Institute of Meteorology), historical data of automatic stations (yearly ZIP files)"
    url: https://portal.inmet.gov.br/dadoshistoricos
  - label: "ANA (Brazil's National Water and Sanitation Agency), HidroWeb legacy web service (HidroSerieHistorica)"
    url: https://telemetriaws1.ana.gov.br/ServiceANA.asmx
  - label: "NASA POWER Daily API, parameter catalog for the AG community (T2M_MAX, T2M_MIN, PRECTOTCORR, IMERG_PRECTOT)"
    url: https://power.larc.nasa.gov/api/system/manager/parameters?community=AG&temporal=daily
  - label: "NASA GPM IMERG precipitation"
    url: https://gpm.nasa.gov/data/imerg
  - label: "SERVIR ClimateSERV API (daily CHIRPS used in this comparison)"
    url: https://climateserv.servirglobal.net/
  - label: "Funk, C. et al. (2026). CHIRPS v3. Scientific Data 13, 718"
    url: https://doi.org/10.1038/s41597-026-07096-4
limitations:
  - "The ground check covers one place, Cruz Alta (RS, Brazil): one NASA POWER grid cell, two main stations and their neighbours. Other grid cells were not checked."
  - "A grid cell (about 50 km for POWER, 5 to 10 km for CHIRPS and IMERG) is compared with a point. Part of every difference is point against area; the station-to-station rows give its size."
  - "Ground temperature data near Cruz Alta are open only from 2007 (INMET A853), so which source is right for 1981-2006 cannot be checked."
  - "The cause of the POWER Tmax shift around 2019 was not identified; whether the upstream meteorology changes source in some year was not verified."
  - "Rain gauge ANA 2853015 is raw data (consistency level 1), with a 2013-2016 gap and a probable level change after it."
  - "The daily CHIRPS from ClimateSERV does not declare its version and is not CHIRPS v3; CHIRPS v3 was compared monthly only. The IMERG run and version served by POWER are not reported by the API."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the team's station comparison (fieldshift-hq docs/research/estacao-vs-satelite.md and verificacao-dados.md, 2026-11-14); human review pending (see SI-USAGE.md). -->

**Why this check.** The challenge asks how satellite observations differ from ground measurements. The app's climate base is [NASA POWER](#nasa-power), a modeled (reanalysis-based) product. Before reading heat days, dry spells or heavy rain from it, the team compared it, and two satellite rain products, with weather stations at Cruz Alta (Rio Grande do Sul, Brazil), a soybean and wheat municipality. Every number on this page comes from that comparison (analysis of 2026-11-14, scripts and tables in the team's planning repository; numbers re-checked by an independent pass).

**What was compared.**

| Source | Type | What it is | Period used |
|---|---|---|---|
| INMET A853, Cruz Alta | ground (automatic station) | hourly rain and temperature, summed to days (00–23 UTC, all 24 hours required) | 2007–2025 |
| ANA 2853015, Três Capões (15 km from the town) | ground (rain gauge) | daily morning reading, as published | 1981–2025, gap 2013–2016 |
| INMET A883 and A886; ANA 2853005 and 2853014 | ground (neighbours) | used to test whether a station or a grid changed | varies |
| NASA POWER (`T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`) | modeled | grid cell that contains the station | 1981–2025 |
| GPM IMERG (`IMERG_PRECTOT`, served by the POWER API) | satellite | precipitation, daily (UTC) | 1998–2025 |
| CHIRPS, daily (ClimateSERV) and v3 monthly | satellite + stations | pixel that contains the station | 1981–2025 |

Each day was matched across sources (a lag of −1, 0 or +1 day was tested and the best kept, because the gauge reads in the morning). The same metrics were computed between two stations, to show how much two points already disagree with no satellite involved.

**Rain: what we found.**

| Comparison | Daily r | Rainy days (1 mm or more): station / grid | Monthly r |
|---|---|---|---|
| A853 vs POWER | 0.78 | 28% / 38% | 0.92 |
| A853 vs IMERG | **0.85** | 28% / 33% | 0.93 |
| A853 vs CHIRPS (daily, ClimateSERV) | 0.71 | 28% / 26% | 0.88 |
| 2853015 vs POWER | 0.65 | 24% / 41% | 0.90 |
| *Reference:* station vs station (about 20–30 km apart) | 0.54–0.76 | — | 0.87 |

- **Month by month, the grids follow the ground about as well as two stations follow each other** (monthly r 0.88 to 0.93 against A853, 0.87 between two stations).
- **Day by day, IMERG matches the station best** (r 0.85), then POWER (0.78) and the daily CHIRPS (0.71).
- **Grids rain a little on many days.** POWER marks rain on 38–41% of days against 24–28% at the gauges. So dry spells are shorter in POWER: the longest January–February dry spell averages **7.3 days in POWER against 11.7 at gauge 2853015** (41 seasons, 1981–2025 without 2013–2016). In 6 of the 7 seasons of 1982–2025 with soybean yield below 75% of trend, the POWER dry spell was shorter than the gauge's.
- **Grids smooth heavy rain.** On days when a gauge measured 60 mm or more, POWER and CHIRPS recorded 42% to 57% of that amount and IMERG 53% to 88%; a neighbouring gauge recorded 66% to 68%, so part of the gap is point against area.
- **Long-term change depends on the source.** For January–February rain, 1981–2000 against 2001–2012 (the continuous stretch of the gauge), every source falls by 14% to 22% and the gauge by 21.6%. In recent years they part ways: the January–February POWER/A853 ratio fell from 1.11 (2008–2011) to 0.83 (2017–2022), while CHIRPS stayed at 1.02–1.04. The gauge 2853015 cannot settle it alone: after its 2013–2016 gap it reads about 10–13% more than its neighbours.

**Temperature: what we found** (A853 against POWER, 6,568 days).

- **On average POWER Tmax is close to the station:** +0.51 °C, daily r 0.94; Tmin +0.03 °C, r 0.96.
- **POWER is warm on cool days and cool on hot days:** +1.23 °C when the station is below 25 °C, −0.73 °C between 32 and 35 °C.
- **POWER Tmax shifted around 2019.** In January–February it ran +0.41 °C above A853 in 2008–2018 and **+1.84 °C in 2019–2025**. The neighbouring stations A883 and A886 kept the same offset to A853 in both periods (+0.58 → +0.49 °C and +0.69 → +0.49 °C), so the change is in POWER. As a result, in 2019–2025 POWER counted **204 January–February days above 32 °C against 128 at the station**; in 2008–2018 it was 83 against 94.
- **What holds and what does not.** The link between January–February days above 32 °C and the soybean yield anomaly holds with station data (r −0.81 with A853, −0.77 with POWER, same 17 seasons). An *increase* in hot days computed from POWER alone does not: without 2019–2025 there is no increase.

**What this means for the app.**

1. POWER values are labeled **modeled**, never "observed", and no correction is applied to them.
2. The provenance record of POWER `T2M_MAX`, of the heat-day index and of its climatology states the Tmax shift; the records of POWER rain, of the extreme-rain index and of its percentile state the wet-day and heavy-rain bias (`fieldshift.provenance.ground_check`, tested in `services/science/tests/test_ground_check.py`).
3. **Recommended cross-check:** heat-day counts and trends against a local weather station; dry spells and extreme rain against a rain gauge or GPM IMERG. Monthly rain totals from POWER agree with the ground about as well as a nearby station does.
4. Other indices that read POWER Tmax (growing degree-days, [ET0](#et0-fao56)) use the same series; their size of effect was not measured.
