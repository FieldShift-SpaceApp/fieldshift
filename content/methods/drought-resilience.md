---
anchor: drought-resilience
title: Drought sensitivity of soybean before and after winter cover became the rule (a negative result)
order: 66
refs:
  - label: "Analysis folder with the pre-registered method, scripts, results, figure and full write-up (analysis/drought-resilience)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/drought-resilience
  - label: "NASA POWER daily point API (PRECTOTCORR, T2M_MAX)"
    url: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
  - label: "IBGE PAM, SIDRA table 1612 (soybean average yield and planted area by municipality)"
    url: https://sidra.ibge.gov.br/tabela/1612
  - label: "ANA HidroWeb web service, HidroSerieHistorica, rain gauge 2853015"
    url: https://telemetriaws1.ana.gov.br/ServiceANA.asmx/HidroSerieHistorica?codEstacao=2853015&dataInicio=&dataFim=&tipoDados=2&nivelConsistencia=
limitations:
  - "Not supported: the change in drought sensitivity after 1995 is -4.5 points with a 95% interval of -24.3 to +19.2 (permutation by year p = 0.61), and its sign flips with the cut year. The result says nothing for or against soil cover at field scale."
  - "Low power: only 13 harvests (1982-1994) and one drought summer (1991) precede the Landsat drop in bare soil, so a halving of the sensitivity could not have been told from no change."
  - "Confounded: cultivars, sowing dates, soybean area and the quality of old PAM data changed over the same years; the before/after split is a proxy taken from one municipality's Landsat series."
  - "Rain is one point per municipality centroid (9 distinct POWER cells for 18 municipalities); POWER agrees with the ANA gauge at Cruz Alta (r = 0.89 for DJF totals, 39 summers)."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the scripts and results in analysis/drought-resilience (run of 2026-11-15); the hypothesis was synthesized with AI at the team lead's request; human review pending (see SI-USAGE.md). -->

**Why this analysis.** Landsat shows that probable bare soil on Cruz Alta cropland in early November fell from a median of 5.7% in 1984–1994 to at most 2.2% every year since 1995 (`analysis/residue-landsat`). The team asked whether soybean yields became less sensitive to summer drought after that change, which would be regional evidence that soil care protects income. The method was written and committed before any number was computed. Every number comes from [`analysis/drought-resilience/`](../../analysis/drought-resilience/README.md), rerun with one command.

**Method.** Soybean yield of the 18 Planalto Médio municipalities (IBGE PAM, 1982–2025) is expressed as the deviation from each municipality's linear trend. Summer drought is the December–February rain total from NASA POWER (`PRECTOTCORR`) at each municipality centroid, standardized per municipality. Sensitivity is the regression slope of the yield deviation on standardized rain, in 1982–1994 and in 1995–2025. Because neighbouring municipalities share the same summer, uncertainty is computed with the **year** as the unit: a bootstrap that resamples years and a permutation that shuffles years between the two periods (10,000 draws each). Robustness: cut year 1993–1998, dropping the 2005, 2012, 2022 and 2023 droughts, a LOESS trend, the longest dry spell instead of rain, 2005–2025 as the "after" period, regional means, and the ANA gauge instead of POWER at Cruz Alta.

**Result.** Yield moved **+21.5% of trend per standard deviation of summer rain in 1982–1994** (95% interval −0.3 to +39.8) and **+17.1% in 1995–2025** (+9.8 to +25.4); since 2005 it is +25.1%. The difference is not distinguishable from zero in any variant, and its sign flips when the cut year is 1997 or 1998. **The hypothesis is not supported.**

**What it does show.** Summer drought still costs soybean yield in the region: in the five driest summers since 1995 (2005, 2012, 2020, 2022, 2023), the municipalities' mean yield fell 25% to 70% below trend. That is why drought risk belongs in the winter decision; it is not evidence that winter cover reduces that risk.
