---
anchor: climate-indices
title: Climate indices (heat and frost days, growing degree-days, water deficit, extreme rain)
order: 25
refs:
  - label: "Zhang, X., Alexander, L., Hegerl, G.C., Jones, P., Klein Tank, A., Peterson, T.C., Trewin, B., Zwiers, F.W. (2011). Indices for monitoring changes in extremes based on daily temperature and precipitation data. WIREs Climate Change 2, 851-870."
    url: https://doi.org/10.1002/wcc.147
  - label: "ETCCDI, definitions of the 27 core indices"
    url: https://etccdi.pacificclimate.org/list_27_indices.shtml
  - label: "McMaster, G.S., Wilhelm, W.W. (1997). Growing degree-days: one equation, two interpretations. Agricultural and Forest Meteorology 87, 291-300."
    url: https://doi.org/10.1016/S0168-1923(97)00027-0
  - label: "Hyndman, R.J., Fan, Y. (1996). Sample quantiles in statistical packages. The American Statistician 50(4), 361-365."
    url: https://doi.org/10.1080/00031305.1996.10473566
limitations:
  - "The heat threshold (35 °C) and the growing degree-day base (10 °C) are generic defaults until the agronomist sets them per site and per crop; when a default is used, the provenance record of the number says so."
  - "All indices use the NASA POWER grid cell that contains the site point (about 50 km): local frost in low spots and short local storms are smoothed out."
  - "Heat days read POWER Tmax, which shifted warm against the ground from about 2019 at Cruz Alta (+1.84 °C in January-February 2019-2025 against INMET A853, +0.41 °C before): a rise in heat days that appears only after 2019 may be an artifact of the data. Check it against a local weather station."
  - "Extreme rain days use POWER daily rain, which smooths heavy rain (on days with 60 mm or more at a Cruz Alta gauge, POWER recorded 46-57% of the amount) and rains a little on too many days, so dry spells are underestimated. Check extremes and dry spells against a rain gauge or GPM IMERG."
  - "The water deficit (ET0 minus rain) is a climate indicator, not a soil water balance: it has no runoff, soil storage or crop coefficient."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from services/science/src/fieldshift/indices/climate.py and its tests (EECOM, issue #22); review by GUIDO + SURGEON pending (see SI-USAGE.md). -->

**What they are.** Simple counts and totals that summarize the weather of each month at the site: hot days, frost days, accumulated warmth for crop growth, the gap between evaporative demand and rain, and very heavy rain days.

**How we compute them.** Every index is computed on the daily [NASA POWER](#nasa-power) data first, then summed per calendar month (`fieldshift.indices.climate` in `services/science`). A day missing an input has no value, so its month has no value either (see [monthly harmonization](#monthly-harmonization)).

| Index | Daily rule | Per month |
|---|---|---|
| Heat days | maximum temperature above the heat threshold (default 35 °C) | number of days |
| Frost days | minimum air temperature at 2 m at or below 0 °C | number of days |
| Growing degree-days | (maximum + minimum) / 2 minus the base temperature (default 10 °C), never below zero (McMaster and Wilhelm 1997, method 1) | sum (°C·day) |
| Water deficit | [ET0](#et0-fao56) minus rain; above zero means demand above rain | sum (mm) |
| Extreme rain days and total | rain above the 95th percentile of wet days (1 mm or more) in 1991–2020 (ETCCDI R95p) | number of days; rain on those days (mm) |

The 95th percentile uses linear interpolation between ordered values (Hyndman and Fan type 7, the default of R and numpy). The same form as the ETCCDI indices is kept, with two differences stated here: ETCCDI counts frost with minimum temperature strictly below 0 °C and uses 1961–1990 as the base period; NASA POWER starts in 1981, so the base period here is 1991–2020.

**Climatology.** For each index and for ET0, the site page can show the 1991–2020 mean of each calendar month and the mean yearly total. A month (or the yearly mean) is left out unless every year of 1991–2020 has a value.

**Parameters.** Thresholds are settings, not results: each provenance record lists the values used (`method.parameters`). The agronomist sets the heat threshold, the frost threshold and the base temperature per site.

**Checks.** `services/science/tests/test_indices.py`: reference values for the percentile (for 1 to 100, the 95th percentile is 95.05) and for growing degree-days, threshold edges (a day at exactly 35 °C is not a heat day; a day at exactly 0 °C is a frost day), and the rule that a missing day makes the month and its climatology empty.

**Provenance.** Each index value has a `computed` provenance record whose inputs are the NASA POWER records it reads (and the ET0 record for the water deficit) and whose method points to this section. The records of the heat-day and extreme-rain indices (and of their climatology and percentile) also carry the result of the team's [ground check](#satellite-vs-ground-check) as a limitation, with the recommended cross-check.
