---
anchor: team-rotation-evidence
title: Team research reproduced in public - heavy rain on soil without a living plant (calendar model only) and revenue per hectare
order: 70
refs:
  - label: "Analysis folder with scripts, inputs and results (analysis/team-rotation-evidence)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/team-rotation-evidence
  - label: "Straw, not bare soil: 40 years of Landsat and HLS (the satellite measurement)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/residue-landsat
  - label: "Storms meet soil (the satellite measurement of cover in November)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/storms-bare-soil
  - label: "GPM IMERG Final V07 (Huffman et al. 2023), daily, via SERVIR ClimateSERV"
    url: https://doi.org/10.5067/GPM/IMERG/3B-HH/07
  - label: "IBGE PAM, SIDRA table 1612, and IPCA, SIDRA table 1737"
    url: https://sidra.ibge.gov.br/tabela/1612
limitations:
  - "Calendar model only; satellite measurement (residue-landsat, storms-bare-soil) shows total-year exposure does not fall with a winter crop; protection in Oct–Nov comes from straw."
  - "Sowing dates and stage lengths are assumptions of the team's research, to be validated by an agronomist; straw counts as no living plant; one 0.1 degree rain cell stands for the municipality."
  - "Revenue is gross (value of production per harvested hectare, IBGE), not a margin: production costs are not subtracted."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from analysis/team-rotation-evidence (run of 2026-11-15) and the team's research note of 15 November on the calendar model; human review pending (see SI-USAGE.md). -->

> **Calendar model only.** Satellite measurement (residue-landsat, storms-bare-soil) shows total-year exposure does not fall with a winter crop; protection in Oct–Nov comes from straw.

**What it is.** A minimal public port of two results of the FieldShift team research, rerun from public sources: (1) the share of the heavy rain (days of 25 mm or more) that falls on soil with no living plant, per winter calendar, from daily NASA GPM IMERG at Cruz Alta; (2) the gross revenue per hectare of wheat + soybean against soybean + fallow, from IBGE PAM and IPCA. Both match the team's tables.

**How to read (1).** It is a crop-calendar model: each sequence is drawn as sowing dates and stage lengths, and every day outside a living canopy counts as exposed. It is **not** a measurement and **not** evidence that a winter crop protects the soil. The satellites measure something different: a winter crop is green in July–September and leaves the field without a living plant in October–November, under straw, and probable bare soil in early November is now rare in Cruz Alta (Landsat and HLS, [straw, not bare soil](#residue-landsat); [storms meet soil](#storms-bare-soil)). The protection in October–November comes from straw, not from a living plant.

**How to read (2).** Wheat adds gross revenue on the same hectare; it does not show that it adds profit, because costs are not subtracted.
