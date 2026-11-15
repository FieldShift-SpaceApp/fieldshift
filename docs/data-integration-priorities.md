# Data integration priorities for Cruz Alta

> **SI-assisted:** drafted with ChatGPT (OpenAI) from the public FieldShift repository and the NASA Space Apps challenge brief; human and front-owner review pending (see `SI-USAGE.md`).

## Purpose and status

This is a data-readiness and integration recommendation for the team. It does not change the product concept, mark any candidate dataset as adopted, or claim that a source is already wired into the farmer-facing application. The challenge asks for NASA Earth observations together with local soil information, crop characteristics, and farmer priorities; the data should support comparison and explain uncertainty, not imply a guaranteed forecast. See the [official challenge brief](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/).

The repository identifies NASA POWER as the selected climate base. It lists SMAP, GPM IMERG, Landsat/HLS, Sentinel-2, SRTM, and the NOAA products below as candidates or research/complement sources. Check the actual application read path and provenance before describing any candidate as integrated. The current Cruz Alta site input is a municipal centroid, so its outputs are regional context, not field-specific measurements.

## Recommended order

| Priority | Source | Purpose in the app | Evidence and limits | Adoption gate |
|---|---|---|---|---|
| 0 — required context | Farmer's field boundary, recent rotation history, soil properties, crop traits, and farmer priorities | Make comparisons specific to a field and show why each strategy fits the farmer's stated constraints | These are part of the challenge itself. Satellite pixels and a municipal centroid cannot supply a farmer's field history, soil test, or priorities. | Human-approved site and rotation inputs; agronomist review of crop assumptions. Do not present field recommendations from a municipality centroid. |
| 1 — local weather validation | INMET stations and ANA rain gauges, compared with NASA POWER and GPM IMERG | Show observed station data and source agreement for recent rain, dry spells, and heavy-rain events; expose gaps and quality flags | The repository already documents station comparisons. IMERG matched the INMET A853 daily rain series better than POWER in that comparison, but grids and point gauges have different spatial support; the ANA gauge has a gap and a likely level shift. This is evidence for a cross-check, not proof one source is always correct. | Match timestamps and units; preserve station quality codes and missing periods; compare point-to-point and grid-to-point; do not average sources blindly. Record the IMERG product/run and access date where available. |
| 2 — ENSO context, with uncertainty | NOAA CPC ONI/RONI history and official outlook; optionally NMME forecast skill | Give a clearly labeled large-scale climate context alongside local observations, not a local rainfall forecast or a rotation command | The team has already used ONI, CPC discussions, official CPC/IRI probabilities, and NMME in analyses and complement outputs. The forecast-skill report finds small event samples and phase errors; skill at ENSO phase is not skill at Cruz Alta rainfall or crop yield. NOAA now identifies RONI for operational monitoring while keeping ONI available for historical use. | Decide which index is used for each historical/operational view; display issue date, probability, lead, and source; preserve neutral/uncertain outcomes. Never convert an ENSO phase directly into a farm-level rain prediction. |
| 3 — regional soil-water context | NASA SMAP L4 (surface and root-zone soil moisture) | Add a regional wet/dry context layer to help interpret a drought signal | SMAP is currently a candidate and is much coarser than a farm field (about 9 km in the resource inventory). It should not be described as a direct measurement of an individual field's root-zone moisture. | Trial against local soil-moisture observations if available; show spatial scale and retrieval/model limits; add only if it changes an explained decision comparison. |
| 4 — crop cover and rotation evidence | NASA/USGS HLS or Landsat, with Sentinel-2 as a partner source | Show seasonal greenness, probable bare soil/residue windows, and observed land-cover timing | These sources have already been explored in analyses, but cloud gaps, revisit timing, mixed pixels, and crop-class ambiguity remain. They do not directly measure soil fertility, nitrogen fixation, or the farmer's intended rotation. Sentinel-2 is ESA Copernicus data, not NASA data. | Start with one documented indicator and ground-check examples with farmer records or field observations. Preserve scene dates, cloud masks, spatial aggregation, and uncertainty; do not infer a named crop where the evidence is ambiguous. |
| 5 — erosion context, if used in a decision | NASADEM/SRTM elevation and derived slope | Flag terrain context that could make erosion practices worth discussing | Slope is static terrain context, not a measure of current erosion, soil loss, or storm damage. The repository has a slope analysis, but this source is not yet an app input. | Include only with an agronomist-reviewed interpretation and a locally relevant threshold; pair with rainfall/cover context rather than presenting slope as an erosion forecast. |

## Defer for this Brazil prototype

- U.S.-specific services and maps in the challenge resource list (USDA CDL, WSS/SSURGO, PRISM, NAIP, NLCD, CoCoRaHS, USGS NWIS, AMS, NASS, and LANDFIRE) do not cover Cruz Alta in a way that supports the current use case. Use Brazilian equivalents, such as INMET, ANA, IBGE, MAPA/ZARC, Embrapa, and locally collected soil data.
- ECOSTRESS, GLDAS, ERA5, and additional overlapping vegetation products should wait until a named app decision needs them and the team can validate their scale, timing, and incremental value.
- Do not add a dataset only to increase the NASA-data count. The source must change a visible comparison or explain a limitation.

## Implementation sequence and checks

1. Resolve human-owned project and site inputs first: finalize the concept gate, select a real field boundary, enter the recent rotation, soil information, crop assumptions, and farmer priorities. The current Cruz Alta centroid is not a substitute.
2. Promote the existing ground-check work into a small, transparent comparison view: station observations beside POWER and IMERG, with date coverage, missingness, station quality, units, spatial support, and source links. Keep raw sources distinct.
3. Keep ENSO as a dated probability/context panel. Reconcile the historical ONI classification with NOAA's current RONI operational guidance; retain forecast lead and uncertainty.
4. Evaluate SMAP only as a coarse regional water-context layer. Evaluate HLS/Landsat and Sentinel-2 for cover/residue observations, with field examples and cloud/scene metadata.
5. Add SRTM slope only if an erosion-related choice is explicitly supported in the farmer workflow.
6. For every adopted source, update `RESOURCES.md`, the method page, contracts/provenance as needed, and the application read path in the same reviewed change. Any shared contract change needs approval from its consumers under `AGENTS.md`.

## Inventory follow-up

The `RESOURCES.md` GPM IMERG row describes IMERG as a candidate and says it is not yet in the app, while part of its Feeds text describes a share “shown in the farmer-facing app.” Reconcile that wording against the current UI/read path before the team claims IMERG is live. This document intentionally leaves the candidate status unchanged.

## References

- [NASA POWER method and source inventory](../RESOURCES.md)
- [Satellite and ground station comparison](../content/methods/satellite-vs-ground.md)
- [ENSO heavy-rain method and limitations](../content/methods/enso-heavy-rain.md)
- [ENSO forecast-skill method and limitations](../content/methods/enso-forecast-skill.md)
- [NOAA CPC ONI / ERSSTv5 historical table and RONI notice](https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso/oni/v5/)
- [NASA SMAP L4 product search](https://search.earthdata.nasa.gov/search?q=SPL4SMGP)
- [NASA GPM IMERG](https://gpm.nasa.gov/data/imerg)
