---
anchor: et0-fao56
title: Reference evapotranspiration (ET0), FAO-56 Penman-Monteith
order: 20
refs:
  - label: "Allen, R.G., Pereira, L.S., Raes, D., Smith, M. (1998). Crop evapotranspiration: guidelines for computing crop water requirements. FAO Irrigation and Drainage Paper 56. FAO, Rome."
    url: https://www.fao.org/4/x0490e/x0490e00.htm
  - label: "FAO-56, Chapter 3, Example 8 (extraterrestrial radiation, southern hemisphere)"
    url: https://www.fao.org/4/x0490e/x0490e07.htm
  - label: "FAO-56, Chapter 4, Example 18 (daily ET0, Uccle)"
    url: https://www.fao.org/4/x0490e/x0490e08.htm
limitations:
  - "ET0 is the water demand of a hypothetical grass reference surface, not the actual evapotranspiration of a crop."
  - "All inputs come from NASA POWER, so ET0 inherits its regional-signal resolution (the grid cell that contains the site point) and its modeled character."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from services/science/src/fieldshift/indices/et0.py and its tests; human review pending (see SI-USAGE.md). -->

**What it is.** ET0 is the evaporative demand of the air over a reference grass surface: how much water a well-watered grass would lose in a day under the site's weather. It is the starting point for crop water needs.

**How we compute it.** Daily, with the FAO-56 Penman-Monteith equation (FAO-56 eq. 6), in plain Python (`fieldshift.indices.et0` in `services/science`):

- soil heat flux G = 0 for the daily step (eq. 42); mean temperature from the daily maximum and minimum (eq. 9);
- saturation vapour pressure (eqs. 11–12) and its slope (eq. 13); psychrometric constant from surface pressure (eq. 8);
- actual vapour pressure from the dewpoint (eq. 14), the method FAO-56 prefers;
- extraterrestrial radiation from latitude and day of year (eqs. 21–25), net radiation (eqs. 37–40) with the grass albedo of 0.23 and Rs/Rso capped at 1.0.

**Inputs** (all from [NASA POWER](#nasa-power), daily): maximum and minimum air temperature at 2 m, dewpoint at 2 m, wind speed at 2 m, all-sky surface shortwave radiation and surface pressure, plus the elevation of the POWER grid cell for clear-sky radiation. A day without every input has no ET0.

**Aggregation.** Daily ET0 is summed per calendar month (mm). A month gets a value only when every day has one (see [monthly harmonization](#monthly-harmonization)).

**Checks.** The implementation is tested against the worked examples of the FAO-56 text: Example 8 (extraterrestrial radiation in the southern hemisphere) and Example 18 (daily ET0 at Uccle, Brussels), in `services/science/tests/test_et0_fao56.py`.

**Why not a library.** The `pyet` package (1.5.0, checked 2026-11-14) requires pandas below 3.0 and xarray, which conflicts with the pipeline's pandas 3.1.1. The equations are short and fully referenced, so they are written out and tested directly.

**Provenance.** Each ET0 value has a `computed` provenance record whose inputs are the six POWER records and whose method points to this section.
