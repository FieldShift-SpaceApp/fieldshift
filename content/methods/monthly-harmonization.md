---
anchor: monthly-harmonization
title: Monthly harmonization (common base for all layers)
order: 30
refs:
  - label: "Implementation: fieldshift.harmonize.monthly (pipeline)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/services/science/src/fieldshift/harmonize/monthly.py
limitations:
  - "Variability within a month, and within the field for coarse products, is lost."
  - "Coarse products (POWER, GPM IMERG, SMAP, GRACE) describe the region around the field, not the field itself."
  - "Gaps are not interpolated: for example, the 2017-2018 gap between GRACE and GRACE-FO stays empty."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the project architecture (ADR-3, accepted); human review pending (see SI-USAGE.md). -->

Datasets arrive at different resolutions in space (from 30 m to hundreds of kilometres) and in time (3-hourly, daily, 16-day, monthly). Every layer is brought to one base before it is compared: **one value per calendar month (`YYYY-MM`) per site**. Today only NASA POWER is implemented; other layers follow the same rule when they are added.

**In time.**

| Aggregation | Variables |
|---|---|
| sum | precipitation, ET, ET0 |
| mean | temperature, soil moisture, NDVI |
| count | events (for example frost or heat days) |
| monthly composite | 16-day NDVI: mean of the composites whose composite day falls in the month |

Event indices (heat days, frost days, heavy rain, ET0) are computed on **daily** data first, then aggregated.

**In space.**

- Pixel smaller than or similar to the field (30 m products such as Landsat, OpenET, CDL, MapBiomas; MODIS at 250 m): statistics over the field polygon (mean and 10th, 50th and 90th percentiles), or class fractions for categorical data.
- Pixel much larger than the field (POWER, GPM IMERG at 0.1°, SMAP at 9 km, GRACE at about 300 km): the value of the pixel that contains the field centroid, labeled **"regional signal"** in its provenance. No interpolation, so the data do not pretend to be more precise than they are.

**Gaps** stay empty (`null`) and are listed as limitations.

**Anomalies** compare a month with the monthly climatology of a reference period recorded in the provenance: POWER 1991–2020; SMAP 2015–2025; GRACE, the product's own period.
