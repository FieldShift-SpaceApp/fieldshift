---
anchor: nasa-ai-prithvi
title: NASA's AI on Cruz Alta's winter - the Prithvi foundation model against our rules
order: 68
refs:
  - label: "Analysis folder with scripts, results, figure and the full write-up (analysis/nasa-ai-prithvi)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/nasa-ai-prithvi
  - label: "Prithvi-EO-1.0-100M multi-temporal crop classification (NASA/IBM, Apache-2.0)"
    url: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-1.0-100M-multi-temporal-crop-classification
  - label: "Prithvi-EO-2.0-100M-TL (NASA/IBM, Apache-2.0)"
    url: https://huggingface.co/ibm-nasa-geospatial/Prithvi-EO-2.0-100M-TL
  - label: "Jakubik et al. (2023), Foundation models for generalist geospatial artificial intelligence"
    url: https://arxiv.org/abs/2310.18660
  - label: "Szwarcman et al. (2024), Prithvi-EO-2.0"
    url: https://arxiv.org/abs/2412.02732
  - label: "HLS Sentinel-2 30 m v2.0, HLSS30 (NASA LP DAAC)"
    url: https://doi.org/10.5067/HLS/HLSS30.002
  - label: "HLS Landsat 30 m v2.0, HLSL30 (NASA LP DAAC)"
    url: https://doi.org/10.5067/HLS/HLSL30.002
limitations:
  - "No field labels: every number is agreement between Prithvi and our phenological rules, not accuracy, and the rules are themselves hypotheses."
  - "The crop model was fine-tuned on US 2022 crops (USDA CDL, northern-hemisphere calendar, no cover-crop class); on a southern-hemisphere winter it is out of domain, and the negative zero-shot result says nothing about it where it was trained."
  - "No fine-tuning on Brazilian labels (we have none); only linear probes, trained on the rule classes as weak labels, on one 13.4 km window, one year (2024) and three dates."
  - "The Prithvi-EO-2.0 encoder gives one embedding per 480 m patch, coarse for fields of a few tens of hectares; the fair raw-band baseline at the same scale is reported beside it."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the scripts and results in analysis/nasa-ai-prithvi (run of 2026-11-15 BRT); the idea was synthesized with AI at the team lead's request; human review pending (see SI-USAGE.md). -->

**Why this analysis.** The challenge invites comparing SI approaches. NASA and IBM publish an open geospatial foundation model, Prithvi, pre-trained on NASA HLS, and a version fine-tuned to classify crops from three HLS dates. We asked whether it reads the winter of a Cruz Alta field (wheat-like cereal, cover crop or other) as well as the explicit phenological rules of the [rotation fingerprint](rotation-fingerprint.md). Every number comes from [`analysis/nasa-ai-prithvi/`](../../analysis/nasa-ai-prithvi/README.md).

**Method.**

- **Model:** the published Prithvi-EO-1.0-100M crop checkpoint (Apache-2.0), run on a laptop CPU through a plain-PyTorch re-implementation; checked on the model's own US validation chips (56.6% pixel accuracy on 40 chips against 60.6% published).
- **Data:** a 13.4 km × 13.4 km window of Cruz Alta cropland (82.5% WorldCover cropland), NASA HLS v2.0 of 23 July, 3 September and 10 November 2024, all about 100% clear; 165,315 cropland pixels compared.
- **Reference:** the rule classes of the rotation fingerprint for 2024 in the same window (96 granules, 16 half-months).
- **Zero-shot:** Prithvi's 13 US classes against the rules, with the mapping fixed beforehand (Winter Wheat = wheat-like).
- **Linear probes (experiment):** logistic regression trained on the rule classes in the west half of the window, tested on the east half, on Prithvi features, on the Prithvi-EO-2.0 encoder embeddings and on the raw HLS bands of the same three dates.

**What we found.**

1. **It runs on a CPU, with no account and no GPU** (the whole window in 39 seconds).
2. **Zero-shot it gives no useful winter class here:** 77.9% of the pixels go to the US class "Other"; "Winter Wheat" covers 2.4% of the pixels where the rules see a wheat-like cereal on 51.0%; agreement 48.5%, kappa −0.01 (chance).
3. **Its features do not beat the raw bands:** probes reproduce the rules on 65.6–69.7% of the held-out pixels with the crop model's features (kappa 0.39–0.47) and 48.0% with the Prithvi-EO-2.0 encoder (kappa 0.23), against **82.7% (kappa 0.70) with the 18 raw band values** of the same dates (68.4% when degraded to the encoder's 480 m patches).
4. **What it means for the app:** without local labels to fine-tune it, NASA's foundation model adds nothing over the raw NASA HLS bands for the winter-path question, so the app keeps the explicit, explainable rules. A fine-tuned Prithvi becomes worth testing the day there are field labels (for example farmers' declared winter crops).
