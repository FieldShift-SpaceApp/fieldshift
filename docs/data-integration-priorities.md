# Data integration priorities for Cruz Alta

> **SI-assisted:** drafted with ChatGPT (OpenAI) from the public FieldShift repository, official challenge brief, NASA/USGS/ESA product documentation; human and front-owner review pending (see `SI-USAGE.md`).

## Purpose and current status

This is a data-readiness and integration recommendation for the team. It does not change the product concept or mark candidate datasets as adopted. The challenge asks for NASA Earth observations with local soil information, crop characteristics, and farmer priorities. The data should help compare options and explain uncertainty, not promise a precise farm-level forecast. See the [official challenge brief](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).

The repository identifies NASA POWER as the selected climate base. Its inventory marks SMAP, ECOSTRESS, GPM IMERG, Landsat/HLS, Sentinel-2, SRTM, and NOAA sources as candidate or research/complement sources. In particular, the current inventory does **not** document ECOSTRESS as an app feed: its row has no feed. Landsat/HLS are documented as analysis products. If the team has additional ECOSTRESS processing in another workspace, it should be added to the inventory with product/version, dates, method, and provenance before describing it as part of the app.

The Cruz Alta site coordinate is the municipality centroid, not a farm polygon. Until a real field boundary, rotation history, and local soil information are entered, app outputs at Cruz Alta must be described as regional context.

## Build complementary evidence layers

The sources should be aligned and shown as separate evidence layers. They measure different parts of the climate–land–crop system; combining them does not make every value more accurate automatically.

| Layer | Sources to integrate or evaluate | What the layer can show | Main caveat |
|---|---|---|---|
| 1. Local weather and rainfall | INMET station observations, ANA gauges, NASA POWER, NASA GPM IMERG | Recent observed weather; rainfall totals and event timing; comparison of station, reanalysis-based grid, and satellite estimates | A station is a point and a satellite/reanalysis pixel is an area. Keep source series separate, expose missingness and station quality, align time zones/accumulations, and do not average blindly. |
| 2. Climate background and outlook | NOAA CPC RONI/ONI history and official probabilities; NMME or NASA GEOS-S2S forecast evidence; seasonal climatology | ENSO state and dated large-scale outlook context, alongside forecast lead and historical skill | ENSO phase is not a local rainfall forecast. The team's own forecast-skill analysis reports small event samples and phase errors. Keep probability, issue date, lead, and uncertainty visible. |
| 3. Vegetation and surface cover | Landsat/HLS and Sentinel-2 surface reflectance; NDVI/EVI, residue/bare-soil indicators | Green cover, seasonal vegetation dynamics, possible residue or bare-soil windows, and crop-calendar clues | Optical imagery has cloud/revisit gaps and mixed pixels. Sentinel-2 is ESA Copernicus data and has no thermal bands; vegetation indices do not directly measure fertility, nitrogen fixation, or a farmer's intended crop. |
| 4. Thermal stress at the surface | NASA ECOSTRESS LST&E; Landsat Collection 2 Surface Temperature; optionally MODIS MOD11A1 for regional context | Clear-sky surface-temperature patterns and anomalies. Compare with vegetation cover and weather to investigate possible water/heat stress | Satellite land-surface temperature is not air temperature or a direct leaf thermometer. Pixels can mix canopy and exposed soil. ECOSTRESS is 70 m with variable acquisition times/coverage; Landsat thermal measurements are natively coarser than the 30 m grid in which products may be delivered; clouds and overpass timing leave gaps. MODIS is about 1 km, useful for broader daily day/night context, not small fields. |
| 5. Soil-water context | NASA SMAP L4 surface/root-zone soil-moisture analysis; local soil moisture or agronomic observations where available | Regional wet/dry context to interpret rainfall and thermal signals | SMAP's roughly 9 km grid is much larger than a field; L4 is an analysis product, not a direct point measurement of the farm's root zone. |
| 6. Soil and terrain context | Local soil test and farmer/agronomist records; Brazilian soil sources; NASADEM/SRTM slope where useful | Soil constraints and terrain context relevant to water retention, crop options, and erosion practices | Terrain slope alone does not measure erosion. Regional soil maps do not replace a field soil test. |
| 7. Rotation outcome and farmer feedback | Farmer's recent rotation, planting/harvest dates, crop observations and end-of-season feedback | Compare the current system with at least two alternatives and record what worked for that farmer | Satellite classification cannot reliably reconstruct every crop or management decision. Keep farmer-reported records distinct from remote-sensing estimates. |

## Thermal layer: recommended interpretation

Treat ECOSTRESS as a **high-resolution, opportunistic surface-temperature observation**, not the only or automatically “best” measure of leaf temperature. NASA's current V003 product documentation describes L2 LST&E at a 70 m grid with temporal resolution that varies. Its different acquisition times can help examine surface conditions at different times of day, but the irregular coverage means it cannot provide a continuous daily farm forecast. Compare quality flags, cloud mask, acquisition time, and LST error where available.

Use Landsat Collection 2 Surface Temperature as a historical and spatial complement. USGS notes that the thermal measurements are acquired at 100 m and can be resampled to 30 m to match multispectral bands. A 30 m output cell therefore does not mean a 30 m independent thermal measurement. Collection 2 also documents known issues, including missing emissivity support and errors where vegetation changed substantially between the ASTER emissivity baseline and the Landsat scene.

Sentinel-2 can contribute optical vegetation indicators such as NDVI, but not temperature. MODIS MOD11A1 V6.1 provides daily day/night LST at about 1 km under clear-sky conditions, giving broader regional context. Choose between them by the question: ECOSTRESS for irregular finer-scale thermal snapshots, Landsat for a longer scene-based record, and MODIS for broader temporal context.

To interpret a hot surface, compare the same location and crop stage with:
- air temperature, humidity, wind and incoming radiation from ground observations and NASA POWER;
- recent rainfall from INMET/ANA and GPM IMERG;
- vegetation/cover state from Landsat/HLS or Sentinel-2;
- regional soil-water context from SMAP; and
- field notes or soil measurements when available.

Do not collapse these into a single “stress score” until the team has chosen a method, checked it against field evidence, and documented uncertainty. A hot pixel may represent bare soil, crop residue, stressed vegetation, or a mixture.

## Recommended implementation order

1. **Resolve field context first:** obtain a field polygon, recent rotation history, soil data, crop assumptions, and farmer priorities. Have an agronomist review crop-specific interpretations.
2. **Expose local weather validation:** put INMET/ANA observations beside POWER and GPM IMERG with date coverage, quality flags, missingness, units, time conventions, spatial support, and source links. The existing comparison found IMERG tracked daily INMET A853 rainfall better than POWER in that one comparison, but this is not proof that IMERG is universally best.
3. **Add a dated climate-context panel:** show NOAA's operational ENSO outlook and the historical index used in analysis, with issue date, lead, probability, skill context, and uncertainty. Do not turn ENSO state directly into a local rainfall or crop-loss prediction.
4. **Prototype the thermal–vegetation view:** use one ECOSTRESS or Landsat surface-temperature product with a vegetation/cover layer and quality masking. Compare candidate scenes to weather observations and field notes before showing a stress interpretation.
5. **Add SMAP only as regional context:** show its footprint and analysis-product status, and test whether it adds useful information beyond rainfall and the thermal/vegetation view.
6. **Add terrain and other datasets only when they change a farmer-facing comparison.** Update `RESOURCES.md`, methods, provenance, and the application read path in the same reviewed change. Shared contract changes require approval from their consumers under `AGENTS.md`.

## Where oceanography and climatology expertise adds value

The oceanography/climatology contribution can strengthen the scientific layer by:
- separating climate modes (ENSO) from regional weather and field-scale impacts;
- describing forecast horizon, issue date, and uncertainty rather than presenting one deterministic forecast;
- checking seasonal and short-to-medium outlook skill against observed outcomes and a simple baseline;
- defining comparable event windows (for example, heat, dry spells, heavy-rain periods) and connecting them to crop stage without claiming causation;
- checking surface observations against station data, and noting when a grid/pixel cannot resolve a farm;
- documenting how radiation, humidity, wind and rainfall shape surface temperature and evaporative demand; and
- explaining to farmers what each layer observes, its spatial/temporal scale, and what it cannot tell them.

## Defer for this Brazil prototype

- U.S.-specific products in the challenge resource list (USDA CDL, WSS/SSURGO, PRISM, NAIP, NLCD, CoCoRaHS, USGS NWIS, AMS, NASS, and LANDFIRE) do not fit Cruz Alta. Prefer Brazilian sources such as INMET, ANA, IBGE, MAPA/ZARC, Embrapa, and farm-level soil data.
- Add ECOSTRESS, SMAP, Landsat/HLS, Sentinel-2, or SRTM to the app only after verifying the actual data path, product/version, coverage, scale, quality flags, and how it changes an explained comparison. Do not add layers merely to increase the dataset count.
- The GPM IMERG row in `RESOURCES.md` marks it as a candidate/not yet in the app, while part of its Feeds text says a share is “shown in the farmer-facing app.” Reconcile that statement against the app's actual read path before claiming it is live.

## References

- [NASA Space Apps challenge brief](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/)
- [Project source inventory](../RESOURCES.md)
- [Satellite and ground-station comparison](../content/methods/satellite-vs-ground.md)
- [ENSO heavy-rain method and limits](../content/methods/enso-heavy-rain.md)
- [ENSO forecast-skill method and limits](../content/methods/enso-forecast-skill.md)
- [NASA ECOSTRESS LST&E product V003 (70 m; variable temporal resolution)](https://doi.org/10.5067/ECOSTRESS/ECO_L2G_LSTE.003)
- [ECOSTRESS product documentation](https://ecostress.jpl.nasa.gov/data/atbds-summary-table)
- [USGS Landsat Collection 2 Surface Temperature](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature)
- [USGS Landsat 8-9 instrument thermal-band sampling](https://www.usgs.gov/centers/eros/science/usgs-eros-archive-landsat-archives-landsat-8-9-operational-land)
- [ESA Sentinel-2 MSI instrument](https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-2/Instrument)
- [NASA MODIS MOD11A1 V6.1 daily LST product](https://doi.org/10.5067/MODIS/MOD11A1.061)
- [NASA SMAP L4 product description](https://smap.jpl.nasa.gov/files/smap2/smap_handbook_web.pdf)
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg)
- [NOAA CPC ONI/RONI information](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v5/)
