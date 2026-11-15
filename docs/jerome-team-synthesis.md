# Jerome's project synthesis for team review

> **SI-assisted:** compiled with ChatGPT (OpenAI) from Jerome's project discussion and the public FieldShift repository; team review pending (see `SI-USAGE.md`). This is a discussion brief, not a team-approved product or agronomic decision.

## Project in one paragraph

**Stella Root** is the working name Jerome has used for a free, open-source decision-support tool for farmers. It should help small and family farmers first, while remaining useful to larger farms and regional users. It brings climate history, weather observations, satellite evidence, soil and crop context, and the farmer's own rotation history into an understandable comparison of **at least three rotation strategies**. It explains risks and uncertainty so the farmer can decide; it does not decide or guarantee an outcome for them.

The team conversation identifies seven regions around Cruz Alta as an intended study area. Confirm the exact region names and boundaries with the team before treating that scope as settled. The public repository currently represents Cruz Alta with a municipal-centroid site, which is regional context rather than a farm field. Nevada/Diamond Valley has also appeared in earlier discussion, but the current data plan in this PR is focused on Cruz Alta.

## The evidence layers we discussed

These layers answer different questions. The app should keep them distinguishable, show source/date/scale/uncertainty, and combine them only through a documented method validated against local evidence.

| Layer | Candidate inputs | What it contributes | Scale and interpretation |
|---|---|---|---|
| Weather observations and climate history | INMET stations, ANA rain gauges, NASA POWER | Observed temperature/rainfall and long-term climate context; station records help check gridded data | Match dates, time zones and units; stations are points, POWER is gridded/reanalysis-based. Keep coverage gaps and known source differences visible. |
| Rainfall from satellite | NASA GPM IMERG | Independent precipitation estimate and heavy-rain context alongside stations and POWER | Compare rather than blindly average. Note satellite pixel size, daily UTC convention, product run/version and missing periods. |
| Climate modes and outlook | NOAA CPC ENSO indices/outlooks, NMME, IRI and NASA GEOS-S2S where relevant | Large-scale ENSO context and dated seasonal forecast probabilities | ENSO is not a local farm-rainfall forecast. Show issue date, lead time, probability and historical skill; distinguish observation, outlook, hindcast and forecast. NOAA's current operational guidance uses RONI, while ONI remains useful for historical analyses. |
| Vegetation and cover | Landsat/HLS and Sentinel-2 optical imagery; NDVI/EVI and cover/residue indicators | Seasonal greenness, probable bare soil/residue windows and possible crop-calendar clues | Cloud gaps, mixed pixels and revisit timing matter. Sentinel-2 is ESA Copernicus optical data, not a thermal sensor. Vegetation indices do not directly measure soil fertility or nitrogen fixation. |
| Surface thermal response | NASA ECOSTRESS LST&E, Landsat Collection 2 Surface Temperature; MODIS MOD11A1 for broad context | Surface-temperature patterns that may help investigate heat or water stress when compared with weather and cover | These are land-surface temperatures, not air temperature or direct measurements of individual leaves. ECOSTRESS is 70 m with variable sampling; Landsat thermal observations are coarser than the 30 m grid at which some products are delivered; MODIS is about 1 km. Clouds and overpass time limit comparisons. |
| Soil water and local soil | NASA SMAP L4; farmer soil tests, local measurements, Embrapa/Brazilian sources | Regional wet/dry context plus field-specific soil properties | SMAP's roughly 9 km grid is regional context, not a measurement of one field. Satellite soil-moisture estimates do not replace a soil test. |
| Terrain and erosion context | NASADEM/SRTM slope, rainfall, cover and local observations | Terrain context when evaluating erosion-related practices | Slope by itself is not an erosion measurement or a forecast. |
| Rotation and farmer feedback | Farmer's actual recent rotation, sowing/harvest dates, crop observations, costs/preferences and end-of-season feedback | Ground truth for comparing current practice with alternatives and learning from outcomes | Keep farmer reports separate from satellite-derived classifications. Feedback can improve calibration over time, but one season does not establish causation. |

## How to combine the layers

1. **Start with the field and farmer:** boundary, soil profile or test, the recent rotation, crop and sowing context, and the farmer's priorities. Label Cruz Alta's municipal-centroid data as regional until field inputs exist.
2. **Establish observed weather:** compare INMET/ANA with POWER and GPM IMERG. Show the time period, data gaps, quality information, units, and how point-versus-grid differences affect interpretation.
3. **Add the climate context:** place ENSO and seasonal forecast probabilities beside local observations. Explain that longer lead times carry more uncertainty and validate forecast skill for the relevant region and season.
4. **Look for crop response:** compare thermal scenes with vegetation/cover, rain, radiation, humidity, wind, and soil-water context. Respect the acquisition times and pixel sizes; do not turn one hot scene into a diagnosis.
5. **Compare rotations:** show the farmer's current system and at least two alternatives, for at least three strategies total. Describe the evidence, likely trade-offs, and uncertainty for each. Agronomic assumptions and crop tolerances need review by an agronomist.
6. **Close the feedback loop:** let farmers record what they planted and observed, whether the forecast was useful, and outcomes after harvest. Preserve the data source and model version so later calibration can be audited.

A clear interface could show a 30-year climate baseline next to recent conditions, then separate panels for rainfall, heat/radiation, surface temperature, vegetation/cover and soil-water context. Use plain-language labels such as “observed”, “estimated from satellite”, “seasonal outlook” and “uncertain”. A comparison card for each rotation can state what evidence supports it and what the data cannot establish. Do not collapse layers into one risk score until its method is calibrated and validated locally.

## Time windows and honest claims

The team has discussed comparing long historical series such as 1995–2025 and testing how ENSO phases relate to seasonal rainfall and crop outcomes. That is a useful research window, but not every sensor covers 30 years: SMAP begins in 2015 and ECOSTRESS in 2018, while Landsat and longer station/reanalysis records can support longer histories. For any comparison, state the overlapping years and sample size. A correlation between ENSO and rainfall is not proof of causation, crop loss, or field-level forecast skill.

Short-term extremes (dry spells, intense rain, heat and high radiation) can matter even when ENSO is neutral. Use stations and satellite observations to detect or review these events; use seasonal climate modes as background context, not as substitutes for local weather evidence.

## Where Jerome can contribute

Jerome's oceanography background is directly useful for the climate-science part of the work:

- separate ocean climate modes from regional weather and farm-scale impacts;
- assess short-, medium- and seasonal forecast uncertainty, lead time and skill against a baseline;
- define event windows and compare like with like across seasons and crop stages;
- connect radiation, air temperature, humidity, wind and rain to surface-temperature and evaporative-demand interpretation;
- check satellite/reanalysis products against ground observations and explain spatial/temporal limits; and
- translate those limits into clear language farmers can use without overstating certainty.

This complements agronomy and software work; crop tolerances, rotation feasibility and soil interpretation need agronomist/farmer validation.

## What the public repository currently documents

- NASA POWER is the selected app climate base.
- NOAA ENSO indices/outlooks and NMME, GPM IMERG, Landsat/HLS, Sentinel-2 and other sources appear as research, candidate or complement data in the repository; that does not automatically mean they are integrated into the farmer-facing app.
- A teammate reports ECOSTRESS/Landsat thermal and vegetation work. The current public inventory does not yet list ECOSTRESS as an app feed, so product/version, scenes, processing method, quality checks, validation and the app data path should be recorded before claiming that integration.
- The current Cruz Alta site coordinate is a municipal centroid. The repository notes that field boundary, rotation and agronomic inputs remain important dependencies.

## Team and open items for the meeting

Jerome's team introduction named **Otávio, Victor, João, Luís and Kauã**. The working project name in this discussion is **Stella Root**; confirm the official project name and the seven study-region boundaries with the team.

Suggested meeting decisions:
1. Confirm the site list and whether the initial demonstration is regional or tied to a real farm field.
2. Confirm the three rotation strategies and who validates crop/soil assumptions.
3. Identify which data sources already have working pipelines and exact product/version details.
4. Pick the first integrated view: local rain validation, or thermal–vegetation evidence with weather context.
5. Agree on uncertainty labels, farmer feedback fields, and validation criteria before calling any forecast “accurate”.

## Repository and technical references

- [Current data-integration proposal in PR #71](https://github.com/FieldShift-SpaceApp/fieldshift/pull/71)
- [Project data inventory](../RESOURCES.md)
- [Satellite and ground-station comparison](../content/methods/satellite-vs-ground.md)
- [ENSO forecast-skill method](../content/methods/enso-forecast-skill.md)
- [NASA ECOSTRESS LST&E V003](https://doi.org/10.5067/ECOSTRESS/ECO_L2G_LSTE.003)
- [USGS Landsat Surface Temperature](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature)
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg)
- [NASA SMAP L4](https://smap.jpl.nasa.gov/files/smap2/smap_handbook_web.pdf)
- [NOAA CPC ENSO information](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v5/)
