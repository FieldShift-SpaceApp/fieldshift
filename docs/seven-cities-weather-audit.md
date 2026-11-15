# Seven-city rainfall and temperature validation audit

> **SI-assisted:** compiled with ChatGPT (OpenAI) from the team's public seven-city analysis, station comparison, source inventory and provider documentation; review pending (see `SI-USAGE.md`). This audit adds a 2024 station-to-grid spot check and a missing-data audit. It does not rerun the full 2000–2025 city analysis or establish multi-year forecast skill.

## Confirmed study locations

The existing public analysis already names the seven municipalities and provides the point used for daily weather. This confirms the current study list; it does not confirm that those municipality points are farm fields.

| Municipality | IBGE code | Weather point (lat, lon) |
|---|---:|---:|
| Cruz Alta | 4306106 | −28.70, −53.56 |
| Ijuí | 4310207 | −28.32, −53.89 |
| Jóia | 4311155 | −28.77, −54.15 |
| São Miguel das Missões | 4319158 | −28.67, −54.52 |
| São Luiz Gonzaga | 4318903 | −28.42, −54.89 |
| Espumoso | 4307500 | −28.86, −52.83 |
| Júlio de Castilhos | 4311205 | −29.26, −53.65 |

Source: [analysis/seven-cities](../analysis/seven-cities/README.md), “Question” and “Reproducibility”.

## What the current data audit supports

The team's seven-city input covers **1 July 2000–30 June 2025**. It contains daily NASA POWER Tmax, Tmin, mean temperature, relative humidity, wind and radiation, plus daily GPM IMERG precipitation. On 15 November 2026 the team re-downloaded both feeds: POWER returned 9,131 days per point and matched the committed input; IMERG had 9,091 common daily values per point (about 0.4% missing) and also matched the committed input exactly.

That verifies repeatability of the downloaded inputs. It does **not** validate accuracy against ground observations. The existing station comparison checks one municipality (Cruz Alta); the method explicitly says other grid cells have not been checked against stations.

## Rainfall across the seven municipalities

The existing study reports annual rainfall from IMERG and the count of September–November days with at least 50 mm by ENSO group. It classified ENSO using JJA ONI and compared four El Niño years (2002, 2009, 2015, 2023) with all other years from 2000–2024.

| Municipality | Annual rain reported (mm, IMERG; 2000–2025 study period) | SON days ≥ 50 mm: El Niño | SON days ≥ 50 mm: other years | Ground rain comparison in the earlier multi-year method? |
|---|---:|---:|---:|---|
| Cruz Alta | 2,047 | 7.5 | 2.2 | Yes: INMET A853 and ANA 2853015, with limitations |
| Ijuí | 2,084 | 7.8 | 2.8 | No station comparison in the published method |
| Jóia | 2,091 | 7.8 | 2.6 | No station comparison in the published method |
| São Miguel das Missões | 2,142 | 8.0 | 3.0 | No station comparison in the published method |
| São Luiz Gonzaga | 2,125 | 6.5 | 3.2 | No station comparison in the published method |
| Espumoso | 1,999 | 8.8 | 1.9 | No station comparison in the published method |
| Júlio de Castilhos | 1,988 | 6.5 | 2.4 | No station comparison in the published method |

**Interpretation:** The same satellite-based heavy-rain contrast appears in all seven municipalities in the team's analysis. That is useful regional evidence for investigating the signal. It is not seven independent gauge validations, a causal estimate of crop loss, or a forecast for the next season. There are only four El Niño seasons in the stated comparison; the means can move substantially when one event is added or removed. The phase definition is JJA ONI, whereas the live app's rain signal uses SON ONI; those statistics answer different questions.

The local ground check at Cruz Alta found daily rain correlation (r=0.85) between INMET A853 and IMERG, versus (r=0.78) for A853 and POWER. Monthly correlations were 0.93 and 0.92, respectively. This result applies to that station, overlap and processing. It does not establish that IMERG is more accurate in the other six municipalities. The ANA gauge 2853015 is about 15 km away, has a 2013–2016 gap and a probable level shift after the gap.

## Temperature across the seven municipalities

POWER supplies daily air-temperature estimates at all seven weather points in the existing input. The earlier public method has a multi-year direct station comparison only for Cruz Alta: INMET A853 for 2007–2025. It reports daily r=0.94 for Tmax and r=0.96 for Tmin, and a POWER Tmax shift around 2019 (+0.41 °C vs. A853 in January–February 2008–2018; +1.84 °C in 2019–2025). The new 2024 spot check below adds candidate-station comparisons at all seven municipal points, but several stations are 38–53 km away and some stations serve more than one point.

Therefore:
- temperature data are repeatable across seven POWER points; the earlier multi-year ground check covers Cruz Alta, while this audit's 2024 spot check is one year and uses nearby station proxies;
- no multi-year, locally representative ground-accuracy claim is supported for the other six municipalities;
- a POWER trend in hot days must be treated cautiously, including in Cruz Alta; and
- the seven-city analysis period starts in July 2000, so its results do not cover a full 1995–2025 common station/satellite window.

## 2024 station-to-grid spot check

This is a preliminary same-year comparison, separate from the team's multi-year Cruz Alta analysis. It pairs daily values from the 2024 INMET automatic-station archive with the NASA POWER and GPM IMERG daily series at each municipality's existing weather point.

Rainfall comes from INMET hourly precipitation summed for a UTC day only when all 24 hourly values are present; the station day is excluded otherwise. Station Tmax/Tmin are the daily maximum/minimum of INMET's hourly interval extremes, requiring at least 22 valid values out of 24. POWER Tmax/Tmin are the committed daily series. POWER rainfall (`PRECTOTCORR`) was re-requested at each municipal weather point. IMERG is the committed ClimateSERV daily input. Bias is product minus station; MAE is in mm/day for rain and °C for temperature; r is Pearson correlation. The CSV includes wet-day counts at a 1 mm threshold for each pairwise matched sample.

| Municipality | INMET candidate (distance) | Complete station rain days / year | IMERG pairs; r / MAE | POWER rain pairs; r / MAE | Tmax pairs; r / bias / MAE | Tmin pairs; r / bias / MAE |
|---|---|---:|---|---|---|---|
| Cruz Alta | A853 Cruz Alta (15.4 km) | 268 / 366 | 237; 0.750 / 3.324 | 268; 0.832 / 3.272 | 355; 0.942 / +0.425 / 1.681 | 355; 0.972 / −0.075 / 0.982 |
| Ijuí | A853 Cruz Alta (38.0 km) | 268 / 366 | 237; 0.609 / 3.816 | 268; 0.832 / 3.272 | 355; 0.942 / +0.425 / 1.681 | 355; 0.972 / −0.075 / 0.982 |
| Jóia | A886 Tupanciretã (47.4 km) | 365 / 366 | 333; 0.542 / 5.174 | 365; 0.812 / 3.442 | 366; 0.939 / +0.600 / 1.759 | 366; 0.965 / −0.718 / 1.281 |
| São Miguel das Missões | A852 São Luiz Gonzaga (51.6 km) | 256 / 366 | 224; 0.765 / 2.941 | 256; 0.632 / 3.581 | 337; 0.932 / −1.038 / 1.985 | 337; 0.955 / −1.738 / 1.977 |
| São Luiz Gonzaga | A852 São Luiz Gonzaga (7.1 km) | 256 / 366 | 224; 0.785 / 2.937 | 256; 0.746 / 2.619 | 337; 0.931 / −0.075 / 1.826 | 337; 0.956 / −1.228 / 1.689 |
| Espumoso | A837 Soledade (28.0 km) | 366 / 366 | 334; 0.662 / 3.618 | 366; 0.808 / 3.415 | 366; 0.936 / +0.780 / 1.723 | 366; 0.955 / +0.591 / 1.307 |
| Júlio de Castilhos | A886 Tupanciretã (25.6 km) | 365 / 366 | 333; 0.808 / 3.445 | 365; 0.786 / 3.924 | 366; 0.948 / −0.296 / 1.532 | 366; 0.963 / −0.952 / 1.382 |

The full table, including alternative stations for Ijuí, Jóia and Espumoso and wet-day hit/false-alarm/miss counts, is in [`inmet_power_imerg_validation_2024.csv`](../analysis/seven-cities/results/inmet_power_imerg_validation_2024.csv). The automatic-station catalog also lists newer candidates such as B843 Ajuricaba, B833 Cruz Alta Centro and B835 Jóia; they were not used for this 2024 comparison because those codes have no 2024 daily file in the official archive. The alternative A-series candidates show station-location sensitivity: for example, Ijuí's A805 comparison is weaker for POWER rain (r=0.487 at 52.7 km) than the A853 proxy (r=0.832 at 38 km). The same INMET stations are reused for multiple municipality points, so these are not seven independent ground validations.

The 2024 spot check gives daily temperature correlations of 0.932–0.948 for Tmax and 0.955–0.972 for Tmin. Rain correlations range from 0.487–0.832 for POWER and 0.542–0.808 for IMERG across the tested station-point pairs. Rain coverage is uneven: only 256 complete station-rain days at A852 and 268 at A853, against 366 calendar days. The results describe same-date agreement in this one year; they do not establish forecast skill, a correction factor, or performance in other years. Do not apply one city's bias correction to another.

### A critical IMERG gap during May 2024

The committed daily input has exactly 40 missing IMERG dates per municipality (9,091 valid of 9,131 days): 1–7 June 2014, 31 December 2023, 1 January 2024, and **every day from 1–31 May 2024**. The missing dates are identical at all seven points. A fresh ClimateSERV query using dataset 226 and the Cruz Alta polygon for 1–31 May 2024 completed but returned an empty `data` array. This verifies a gap in the provider response for that request; it does not show that the satellite instrument itself had no observations.

This is a serious blind spot for event review: the state's COPAAERGS described the late-April/May 2024 rainfall as the state's greatest climate disaster, while the app's committed IMERG series is blank for the full month ([official COPAAERGS bulletin](https://admin.estado.rs.gov.br/upload/arquivos/202406/boletim-copaaergs-extraordinario-maio-2024-final.pdf)). The 2024 INMET archive has complete hourly rainfall for 28–31 days in May at the six candidate stations used here: A805 30, A837 31, A852 31, A853 30, A883 28, A886 31 days. That gives the app a plausible ground-data contingency for the period, with station distance and missing-hour status visible.

**Data handling decision:** a blank IMERG day must stay missing, never become 0 mm. When a local gauge or POWER is used as a fallback, retain the source, dates, spatial distance and quality label; do not silently splice it into the IMERG series. If no suitable fallback is available, show the gap and lower confidence rather than inventing a value.

## Validation status by variable

| Variable | Seven-city input check | Ground accuracy check | Current status |
|---|---|---|---|
| Daily rainfall | POWER and IMERG inputs re-downloaded; the audit adds a 2024 check against available station candidates at all seven points | Earlier multi-year comparison covers Cruz Alta; 2024 check uses stations 7–53 km away, with uneven rain-day coverage | Preliminary same-year comparison only; not a multi-year local validation |
| Heavy-rain frequency | IMERG SON days ≥ 50 mm compared across ENSO groups in all seven; the 2024 daily input has a full May gap | The spot check does not independently validate heavy-rain event timing or totals at every town | Regional signal only; May 2024 is unavailable in the committed IMERG feed |
| Tmax / Tmin | POWER daily series re-downloaded; the audit adds a 2024 check against available station candidates at all seven points | Earlier multi-year comparison covers Cruz Alta; 2024 check is single-year and uses nearby stations | Preliminary same-year comparison only; no regional multi-year validation |
| Temperature/rainfall forecast skill | ENSO phase forecasts evaluated in a separate scorecard | The scorecard target is ENSO JJA phase, not local rain or temperature | Use only as dated climate context; not local forecast skill |

## Next work needed for a full seven-city validation

1. Complete the station/gauge inventory in the [INMET automatic-station catalog](https://portal.inmet.gov.br/paginas/catalogoaut) and [ANA HidroWeb](https://www.snirh.gov.br/hidroweb/). This audit records the first INMET candidates and distances for 2024; add ANA gauges, conventional stations, full record windows and quality/consistency metadata.
2. Select reference stations based on record quality and distance, not just the closest name. Preserve the fact that station observations are point measurements while POWER/IMERG are area estimates.
3. Reproduce the 2024 comparison from the official station archive and extend it across the common historical years. Declare UTC/local-day alignment and test ±1-day sensitivity. For rain, report paired-day completeness, bias, MAE, correlation, wet-day detection, heavy-rain performance and longest dry-spell differences. For temperature, report paired-day completeness, mean bias, MAE, hot-day counts and change-point sensitivity, especially around 2019.
4. Publish each municipality's validation window and unsupported variables. Do not copy the Cruz Alta skill metrics to the other six.
5. Only then decide which series can be displayed as locally checked evidence in the app. Until then, label the other six as satellite/reanalysis estimates at municipal weather points.

## References

- [Seven-city analysis and reproducibility notes](../analysis/seven-cities/README.md)
- [Seven-city summary results](../analysis/seven-cities/results/team_summary_by_city.csv)
- [Seven-city rainfall/temperature inputs](../analysis/seven-cities/inputs/daily_imerg_power_seven_cities.csv)
- [Cruz Alta satellite vs. ground method](../content/methods/satellite-vs-ground.md)
- [ENSO heavy-rain method and phase definition](../content/methods/enso-heavy-rain.md)
- [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/)
- [NASA GPM IMERG](https://gpm.nasa.gov/data/directory)
- [INMET 2024 automatic-station archive](https://portal.inmet.gov.br/uploads/dadoshistoricos/2024.zip)
- [SERVIR ClimateSERV API](https://climateserv.servirglobal.net/)
- [2024 INMET vs. POWER and IMERG results](../analysis/seven-cities/results/inmet_power_imerg_validation_2024.csv)
- [INMET automatic station catalog](https://portal.inmet.gov.br/paginas/catalogoaut)
- [ANA HidroWeb](https://www.snirh.gov.br/hidroweb/)
