---
anchor: rotation-drought-test
title: Did soybean after a cover crop suffer less in the drought? A 30 m test in NASA HLS (answer - no)
order: 67
refs:
  - label: "Analysis folder with the pre-registered method, scripts, results and figure (analysis/rotation-drought-test)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/rotation-drought-test
  - label: "HLS Landsat 30 m v2.0, HLSL30 (NASA LP DAAC)"
    url: https://doi.org/10.5067/HLS/HLSL30.002
  - label: "HLS Sentinel-2 30 m v2.0, HLSS30 (NASA LP DAAC)"
    url: https://doi.org/10.5067/HLS/HLSS30.002
  - label: "NASA POWER Daily API (PRECTOTCORR, December-February rain at Cruz Alta)"
    url: https://power.larc.nasa.gov/
limitations:
  - "Winter classes are phenological hypotheses without field labels (rotation fingerprint); dropping the 18% of pixel-years nearest the wheat/cover split does not change the answer."
  - "Only two drought summers (2021/22, 2022/23): block-clustered intervals understate year-level noise; the fake-drought placebo puts that noise at about +/-0.006 NDVI, the size of every drought interaction estimated."
  - "The planting date is a proxy (summer green-up half-month), not a sowing date; no soybean mask (maize is in the panel); slope enters only as a pixel level (fixed effect)."
  - "NDVI is canopy greenness, not yield; nothing here is about soil health, straw, erosion or income, and nothing is causal for a given field."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the scripts and results in analysis/rotation-drought-test (run of 2026-11-15 BRT); the hypothesis was synthesized with AI at the team lead's request; human review pending (see SI-USAGE.md). -->

**Why this analysis.** "A cover crop protects the soybean in a drought" is the claim farmers hear most about winter cover. With the winter class of every 30 m pixel of Cruz Alta from the [rotation fingerprint](#rotation-fingerprint), the 2021/22 and 2022/23 droughts became a natural experiment. The method was written and committed before any model was run. It re-tests, at 30 m and with explicit classes, the team's earlier experiment by the team (Landsat 120 m and MODIS), which found no drought protection.

**Method.**

- **Outcome:** mean NASA HLS NDVI of January-February (and the December-February peak) of every cropland pixel in the summers 2020/21-2025/26, from 904 HLS granules.
- **Treatment:** the pixel's previous winter: cover crop (C), wheat-like cereal (T), other.
- **Comparison:** the same pixel across summers (pixel fixed effect), within the same ~1 km block and summer (local rain), and within the same planting half-month (summer green-up), because soybean after wheat is planted later.
- **Drought summers:** 2021/22 and 2022/23, fixed in advance. NASA POWER confirms them: 182 and 185 mm in December-February, the 2nd and 3rd driest of 26 summers.
- **Checks:** a placebo with the following winter, a placebo that labels each normal summer as a drought, conservative classes, leave-one-summer-out.

**What we found.**

- **No protection.** Same pixel, same planting half-month: C minus T was -0.007 NDVI in normal summers and -0.016 in the drought summers, so drought minus normal is **-0.008 [-0.011; -0.005]**. The decision rule (positive, beyond both placebos) fails. For scale, the drought cut the canopy by about 0.28 NDVI.
- **What looks like protection is the calendar.** On the peak NDVI, C seems to gain +0.015 in the drought. That disappears (-0.011) once the planting half-month is held fixed. After a cover crop, soybean greens up earlier: 14.5% of C pixel-summers by early November against 0.1% of T. After a wheat-like winter, 57% green up in January or later, against 32% after a cover crop.
- **The placebos are as large as the effects.** The following winter "predicts" the summer as much as the previous one does, and the fake droughts give +/-0.006. So the small interactions cannot be read as an effect of the winter.

**How to read it.** This confirms the team's earlier result with a NASA 30 m product and explicit classes. The case for winter cover in the app rests on soil cover and income, not on drought-proofing the soybean. What the satellite shows clearly is the calendar: a wheat-like winter pushes the soybean about half a month later.
