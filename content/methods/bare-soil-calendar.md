---
anchor: bare-soil-calendar
title: Observed calendar of cropland without green cover (Sentinel-2 and MODIS)
order: 62
refs:
  - label: "Copernicus Sentinel-2 L2A, Earth Search STAC collection sentinel-2-l2a (Element 84)"
    url: https://earth-search.aws.element84.com/v1/collections/sentinel-2-l2a
  - label: "ESA WorldCover 2021 v200 (cropland mask)"
    url: https://esa-worldcover.org/
  - label: "Didan, K. MOD13Q1 MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061, NASA LP DAAC"
    url: https://doi.org/10.5067/MODIS/MOD13Q1.061
  - label: "Tucker, C.J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. Remote Sensing of Environment 8, 127-150."
    url: https://doi.org/10.1016/0034-4257(79)90013-0
limitations:
  - "NDVI < 0.25 does not separate straw from bare soil: under no-till, dry straw after desiccation looks like bare ground. Read the calendar as 'no green cover', not as 'exposed soil'."
  - "One Sentinel-2 scene per fortnight, on a different day each year; seven years give a calendar, not a trend."
  - "The Sentinel-2 blocks cover 64% of the municipality's cropland, chosen for having the most cropland; the WorldCover mask is a single year (2021)."
  - "Sentinel-2 is partner data (ESA Copernicus), credited as its licence asks; MODIS is NASA data."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from services/science/src/fieldshift/complements/baresoil.py (EECOM, complements); review by GUIDO + SURGEON pending (see SI-USAGE.md). -->

**What it is.** For each fortnight of the year (days 1-15 and 16 to the end of the month), the share of cropland with NDVI below 0.25, as seen by **Sentinel-2** at 10 m (median, minimum and maximum over 2019-2025) and by **MODIS** at 250 m (median), side by side.

**Sentinel-2.** One L2A scene per fortnight from tile 22JBP (lowest tile cloud cover, at most 70%); NDVI from bands B04 and B08; cloud mask from the scene classification (SCL 4 or 5 = clear); cropland = ESA WorldCover 2021 class 40. A scene counts when at least half of the cropland pixels are clear. Each row of `data/sites/cruz-alta/input/bare-soil-s2-scenes.csv` links to its STAC item.

**MODIS.** MOD13Q1 and MYD13Q1 v061 valid observations (reliability 0 or 1) of pixels with at least 80% cropland, grouped by the fortnight of their acquisition day (`bare-soil-modis-fortnights.csv`).

**Why the two differ.** MODIS shows much less "no green" than Sentinel-2 in the same fortnights (in late November, about 12% against 76%). Sentinel-2 aggregated to 250 m keeps its own level, so the gap is in the MODIS 16-day maximum-value composite, which picks the greenest day, not in the pixel size (hypothesis, not tested).
