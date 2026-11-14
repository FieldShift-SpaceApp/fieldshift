---
anchor: nasa-power
title: NASA POWER daily climate
order: 10
refs:
  - label: NASA POWER (Prediction Of Worldwide Energy Resources), NASA Langley Research Center
    url: https://power.larc.nasa.gov/
  - label: NASA POWER methodology
    url: https://power.larc.nasa.gov/docs/methodology/
  - label: NASA POWER referencing guide (citation and terms)
    url: https://power.larc.nasa.gov/docs/referencing/
limitations:
  - "Regional signal: each value is the POWER grid cell that contains the site point, not a field measurement, and it is not downscaled."
  - "POWER values are modeled (reanalysis-based for meteorology and soil wetness), not direct observations; they are labeled 'modeled'."
  - "POWER soil wetness (GWETTOP, GWETROOT) is a 0 to 1 fraction of saturation from a land-surface model, not volumetric soil moisture and not a satellite observation."
  - "Months with any missing day are left empty (declared gaps), never filled in."
  - "EVPTRNS is not used. POWER labels it 'Evapotranspiration Energy Flux', but in MERRA-2 it is the transpiration energy flux only. Live checks on 2026-11-14 gave values near zero all year in the Florianópolis development cell, while the neighbouring cell and the modeled land evaporation (EVLAND) of the same cell did not. ET0 is computed with FAO-56 instead."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from services/science/README.md, the POWER provenance builder and architecture ADR-3; human review pending (see SI-USAGE.md). -->

**What it is.** NASA POWER serves daily agro-climatic variables for any point on Earth. We use the POWER Daily API (point endpoint, community `AG`) as the climate base of every site, from 1981 to the last complete month.

**Upstream data.** POWER meteorology and soil wetness come from the MERRA-2 reanalysis (grid of about 0.5° × 0.625°); solar radiation comes from CERES SYN1deg (1° × 1°), per the POWER methodology page.

**Variables ingested.** `T2M`, `T2M_MAX`, `T2M_MIN`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `PRECTOTCORR`, `PS`, `GWETTOP`, `GWETROOT`. Units are converted to the project's canonical units when written (see [units and calendar](#units-calendar)).

**How a site gets its values.** One request per site; the raw response is cached in `data/cache/power/<site>/` with the request URL and access time, so the outputs can be rebuilt offline (`uv run fieldshift fetch power --site <id> --offline`). POWER's fill value `-999` is read as missing, never as a number. Because the POWER grid is much coarser than a field, the value is the grid cell that contains the site point and is labeled a **regional signal** in its provenance ([ADR-3 support rule](#monthly-harmonization)).

**Monthly values.** Precipitation is summed per calendar month; the other variables are averaged. A month gets a value only when every day in it is valid; otherwise it is `null` and listed as a known gap.

**Data type.** Every POWER value is labeled **modeled** ([data types](#provenance)).

**Citation.** "The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division", plus the POWER Daily API version and access date, which every provenance record carries.
