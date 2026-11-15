# Seven-city rainfall and temperature validation audit

> **SI-assisted:** compiled with ChatGPT (OpenAI) from the team's public seven-city analysis, station comparison, source inventory and provider documentation; review pending (see `SI-USAGE.md`). This is an evidence audit, not a new re-run of the underlying daily analysis.

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

| Municipality | Annual rain reported (mm, IMERG; 2000–2025 study period) | SON days ≥ 50 mm: El Niño | SON days ≥ 50 mm: other years | Ground rain comparison documented? |
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

POWER supplies daily air-temperature estimates at all seven weather points in the existing input. In the public method, **only Cruz Alta** has a direct station comparison for temperature: INMET A853 for 2007–2025. The check reports daily correlation (r=0.94) for Tmax and (r=0.96) for Tmin, but also a POWER Tmax shift around 2019; in January–February POWER was +1.84 °C against A853 in 2019–2025, compared with +0.41 °C in 2008–2018.

Therefore:
- temperature data are repeatable across the seven POWER points, but only Cruz Alta has documented ground validation;
- no ground-based temperature accuracy claim is yet supported for Ijuí, Jóia, São Miguel das Missões, São Luiz Gonzaga, Espumoso or Júlio de Castilhos;
- a POWER trend in hot days must be treated cautiously, including in Cruz Alta; and
- the seven-city analysis period starts in July 2000, so its results do not cover a full 1995–2025 common station/satellite window.

## Validation status by variable

| Variable | Seven-city input check | Ground accuracy check | Current status |
|---|---|---|---|
| Daily rainfall | POWER and IMERG inputs re-downloaded identically at all seven points; IMERG has ~0.4% missing days in the common series | Published only for Cruz Alta against A853 and ANA gauge 2853015 | Reproducible at seven points; ground-validated at one location only |
| Heavy-rain frequency | IMERG SON days ≥ 50 mm compared across ENSO groups in all seven | No station event verification documented for the other six | Regional satellite signal; not validated at each municipality |
| Tmax / Tmin | POWER daily series re-downloaded identically at all seven points | Published only for Cruz Alta against INMET A853 | Reproducible at seven points; ground-validated at one location only |
| Temperature/rainfall forecast skill | ENSO phase forecasts evaluated in a separate scorecard | The scorecard target is ENSO JJA phase, not local rain or temperature | Use only as dated climate context; not local forecast skill |

## Next work needed for a full seven-city validation

1. Use the [INMET automatic-station catalog](https://portal.inmet.gov.br/paginas/catalogoaut) and [ANA HidroWeb](https://www.snirh.gov.br/hidroweb/) to inventory nearby stations/gauges for each municipality; record station code, coordinates, distance from the weather point, operating dates, measured variables, missing intervals and quality/consistency level.
2. Select reference stations based on record quality and distance, not just the closest name. Preserve the fact that station observations are point measurements while POWER/IMERG are area estimates.
3. Match station and gridded records on a declared daily boundary and common dates. For rain, report paired-day completeness, bias, MAE, correlation, wet-day detection, heavy-rain performance and longest dry-spell differences. For temperature, report paired-day completeness, mean bias, MAE, hot-day counts and change-point sensitivity, especially around 2019.
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
- [INMET automatic station catalog](https://portal.inmet.gov.br/paginas/catalogoaut)
- [ANA HidroWeb](https://www.snirh.gov.br/hidroweb/)
