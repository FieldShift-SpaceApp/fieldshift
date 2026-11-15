# Climate evidence table — Cruz Alta

> **SI-assisted:** compiled with ChatGPT (OpenAI) from FieldShift's documented station comparison, source inventory, ENSO analyses, and provider documentation; review pending (see `SI-USAGE.md`).

## How to read this table

“Observation”, “gridded estimate”, “reanalysis”, “satellite estimate” and “forecast” are different evidence types. Keep them labeled and compare them; do not merge them into a single value without a stated method. The repository's Cruz Alta coordinate is a municipal centroid. It is not a farm location, and this table does not establish farm-level conditions. This first table covers Cruz Alta; repeat the station/source audit for each of the seven intended regions after the team confirms their boundaries and station coverage.

## Evidence by climate signal

| Signal | Source, period and spatial/temporal support | Main uncertainty or limitation | What the evidence can support |
|---|---|---|---|
| **Rainfall observed at stations** | INMET A853, Cruz Alta: hourly station readings aggregated to daily totals, 2007–2025; one point. ANA gauge 2853015, Três Capões, ~15 km away: daily morning readings, 1981–2025 with a 2013–2016 gap; one point. | A station is not a field-wide average. The ANA record is raw consistency level 1 and appears to have a level shift after its gap. INMET observations also require completeness/quality checks before daily aggregation. | Describe rain actually recorded at these station locations and compare it with gridded products. Do not call either station “the farm measurement” without a field station. |
| **Daily/monthly rainfall baseline** | NASA POWER `PRECTOTCORR`: daily point series from 1981 onward; meteorology grid about 0.5° × 0.625° in the project inventory. The current app's site series is monthly aggregated. | POWER is a gridded, reanalysis-based product, not a rain gauge. In the Cruz Alta check it marks rainy days more often than the gauges and smooths heavy-rain amounts; dry spells can be shorter. | Use for long-term background and derived indicators only with the modeled label. Check daily extremes and dry spells against gauges/IMERG; monthly totals aligned better in the available comparison. |
| **Satellite precipitation** | NASA GPM IMERG: project comparison 1998–2025; about 0.1° (~10 km), daily totals derived from sub-daily estimates. The app's POWER-served `IMERG_PRECTOT` API does not report the IMERG run/version. NASA's direct IMERG V07B archive now covers Jan. 1998 onward at 0.1°; that does not mean the POWER-served field identifies the same run. | A satellite pixel is an area and can smooth point-scale extremes; daily UTC boundaries may differ from local station days. Version/run and data latency matter. | Provide an independent precipitation cross-check, not an unquestioned replacement for gauges. In the A853 comparison, daily correlation was 0.85 for IMERG and 0.78 for POWER; this is one local-period comparison, not a universal ranking. |
| **Daily maximum/minimum air temperature** | INMET A853: hourly observations aggregated to daily values, 2007–2025. NASA POWER `T2M_MAX`/`T2M_MIN`: daily gridded series from 1981 onward; the current app output is monthly aggregated. | POWER Tmax shows a documented shift around 2019 against A853; it also tends to be warm on cooler days and cool on the hottest days. Ground data do not validate 1981–2006 locally. | Use station data for observed local heat events. Use POWER for longer context with the documented discontinuity visible; do not claim a long-term hot-day trend from POWER alone. |
| **Incoming shortwave radiation** | NASA POWER `ALLSKY_SFC_SW_DWN`: daily source, radiation grid about 1° × 1° in the project inventory; the current Cruz Alta series has valid months from 1984 onward, with the app output aggregated monthly. | Much coarser support than a farm; modeled/retrieved from satellite radiation products and not locally validated against a pyranometer in the current ground check. | Describe regional radiation context or anomalies, not measured radiation over a specific field. Pair with temperature, humidity, wind and crop stage before discussing atmospheric demand. |
| **Dry spells and heavy-rain events** | Derived from station daily records, POWER daily rain and GPM IMERG; ANA gauge 2853015 provides a longer but interrupted point reference. | Results depend on threshold, day boundary, completeness rule and product. POWER rain-on-more-days bias makes its dry spells shorter; grids smooth some gauge extremes. The ANA gap/step affects comparisons. | Flag a possible event and show which source supports it. For a farmer-facing warning, state threshold, source, period and agreement; do not imply the event's crop damage has been measured. |
| **ENSO historical phase** | NOAA CPC ONI / ERSSTv5 history is used in project analyses to classify seasonal ENSO phases. It is a three-month Pacific SST index, not a Cruz Alta weather observation. NOAA now identifies RONI for operational ENSO monitoring/prediction while retaining ONI historical data. | Broad-scale ocean index; episode thresholds and index choice affect phase labels. An ENSO phase does not determine local rainfall for a particular season. | Use as climate-mode context to stratify historical seasons and explain background conditions. Keep the index and phase definition explicit; do not use it alone to forecast farm rain or crop loss. |
| **Seasonal ENSO outlook / forecast skill** | The repository's scorecard evaluates CPC/IRI official probabilities (2014–2025) and NMME ensemble forecasts (hindcast/forecast archive through 2022), against observed JJA ENSO phase. | Small numbers of El Niño/La Niña winters; some forecast phase scores were no better than an “always neutral” baseline. This measures ENSO-phase prediction skill, not local rainfall or farm outcome skill. | Show a dated probability and lead time as uncertain background only. Do not present it as a Cruz Alta precipitation forecast or a rotation recommendation. |

## Cross-source checks already documented

For INMET A853 at Cruz Alta, the team's comparison reports daily rain correlation **r = 0.78** with POWER and **r = 0.85** with IMERG; monthly correlation is **0.92** and **0.93**, respectively. POWER marked rain on 38% of days against 28% at A853; IMERG marked 33%. For ANA 2853015 versus POWER, daily r was 0.65, with rainy days on 24% versus 41% of days. The source page also reports a January–February longest dry-spell mean of 7.3 days in POWER versus 11.7 days at ANA 2853015. These values describe the repository's specific stations, processing windows and product versions; they are not regional constants. The rain comparison uses available daily overlap, with station comparisons in the method covering 2007–2025 for A853 and interrupted 1981–2025 for ANA 2853015.

For temperature, the documented check of 6,568 daily records reports POWER/A853 daily correlation r = 0.94 for Tmax and r = 0.96 for Tmin, but a POWER Tmax change around 2019. Therefore, a high correlation does not remove systematic or time-varying bias.

## What a 1995–2025 comparison can and cannot do

- A 1995–2025 rainfall chart can show POWER history, but the ground comparison is shorter/fragmented: INMET A853 starts in 2007; IMERG begins in 1998; ANA 2853015 has a 2013–2016 gap and a probable post-gap level change.
- A 1995–2025 temperature series from POWER is not locally station-validated for 1995–2006, and its documented Tmax shift around 2019 must be shown.
- Satellite/reanalysis values should be aligned to a consistent day definition before comparing daily extremes. POWER defaults to local solar time unless the request specifies UTC; the current rain comparison tests day lags because the ANA gauge reads in the morning.
- Show sample size, missing years, phase counts, source, and method beside every ENSO composite. A historical association is not proof of causation or forecast skill. NMME hindcast values were generated retrospectively; they were not all forecasts available to farmers in those historical years.
- ECOSTRESS and SMAP cannot fill the full 30-year window: their records start in 2018 and 2015, respectively. Use them for shorter-period complementary layers, not as substitutes for long climate history.

## Current project status

NASA POWER is the selected climate base in the public repository. INMET/ANA/IMERG comparisons and NOAA ENSO analyses are documented research or complement work; the resource inventory does not describe all of them as integrated live app feeds. This table is a scientific working aid, not a claim that every row is already in the farmer-facing UI.

## References

- FieldShift [satellite and ground-station comparison](../content/methods/satellite-vs-ground.md)
- FieldShift [ENSO forecast-skill method](../content/methods/enso-forecast-skill.md)
- FieldShift [heavy-rain by ENSO phase method](../content/methods/enso-heavy-rain.md)
- FieldShift [dataset inventory and app-feed status](../RESOURCES.md)
- [INMET historical meteorological data](https://portal.inmet.gov.br/dadoshistoricos)
- [ANA HidroWeb](https://www.snirh.gov.br/hidroweb/)
- NASA POWER [Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) and [data FAQ on resolution and source](https://power.larc.nasa.gov/docs/faqs/data/)
- NASA [GPM IMERG product coverage and resolution](https://gpm.nasa.gov/data/directory) and [IMERG products and latency](https://gpm.nasa.gov/data/imerg)
- NOAA CPC [historical ONI and current RONI notice](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v5/)
