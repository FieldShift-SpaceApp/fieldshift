# Did soybean become less sensitive to summer drought after winter cover became the rule? (Planalto Médio, RS, Brazil)

> **SI-assisted:** the hypothesis was synthesized with Claude Code (Anthropic) at the team lead's request from the team's Landsat residue result (PR #54); the scripts and this text were written with Claude Code. Every number in this folder is produced by the scripts on the sources listed; none is produced by the AI. Human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

## Question

Landsat shows that the share of Cruz Alta cropland with a probable bare-soil signature in early November fell from a median of 5.7% in 1984–1994 to at most 2.2% in every year since 1995 (0.3% in the median year since 2005; `analysis/residue-landsat`, PR #54). **After winter cover became the rule, did the soybean yield of the Planalto Médio become less sensitive to December–February drought?**

## Pre-registered method

Written and committed **before** any result was computed (see the git history of this file). The results section reports this method unchanged; anything added later is labelled "post hoc".

**Units.** The 18 municipalities of `analysis/enso-wheat` (Cruz Alta and neighbours), with the IBGE codes and centroids already committed in `analysis/ground-truth-proagro/results/municipalities.csv` (IBGE localities API and mesh metadata).

**Yield.** IBGE PAM, SIDRA table 1612, variable 112 (average yield, kg/ha), soybean (c81/2713), harvest years **1982–2025** (PAM year Y = summer harvest of Y). Missing values (`...`, `-`, `..`) are skipped. Planted area (variable 109) is fetched only to describe the change in soybean area.

**Detrending.** Per municipality, a linear trend (`numpy.polyfit`, degree 1) on all valid years 1982–2025; yield deviation `dev = yield / trend − 1`. Robustness: a LOESS trend (local linear, tricube weights, span 0.5 of the years).

**Drought index.** Window **1 December (Y−1) to the end of February (Y)** for harvest Y (soybean flowering and grain fill in the region). NASA POWER daily, point at each municipality centroid:
- primary: **DJF rain total**, `PRECTOTCORR` (mm), standardized per municipality over 1982–2025 (`z_rain`; negative = drier);
- robustness: **longest dry spell** in DJF (consecutive days < 1 mm), standardized and sign-flipped so that negative = drier (`z_dry`);
- descriptive only: days with `T2M_MAX` ≥ 32 °C in DJF (POWER Tmax has a known shift after about 2019, so heat is not used in any test).
Ground check: the ANA rain gauge 2853015 (Três Capões, 14.9 km from the Cruz Alta point) replaces POWER for Cruz Alta in one robustness run; a year enters only with a complete DJF window.

**Sensitivity.** Ordinary least-squares slope of `dev` on `z_rain`, pooling the municipality-years of a period (one intercept per period): the change in relative yield per one standard deviation of summer rain. Pearson r is reported beside it. Periods: **A = 1982–1994** (13 harvests, before the Landsat drop), **B = 1995–2025** (31 harvests); **B′ = 2005–2025** reported beside B.

**Primary statistic.** `Δ = slope_B − slope_A`. The hypothesis predicts Δ < 0 (yield follows summer rain less closely after 1995).

**Inference, with the year as the unit** (neighbouring municipalities share the same summer, so the effective n is the number of years, not of municipality-years):
- bootstrap by year: harvest years resampled with replacement within each period, all municipalities of a drawn year kept together; 10,000 draws, seed 20261115; 95% percentile interval for each slope and for Δ;
- permutation by year: the 44 harvest years shuffled between A and B (13 and 31), municipalities of a year kept together; 10,000 draws; **two-sided p** for Δ.

**Spatial replication.** Slope per municipality in A and B (municipalities with at least 10 valid harvests in A); count of municipalities with `slope_B < slope_A`. Descriptive only: the municipalities are not independent.

**Robustness (all run every time).** Cut year 1993, 1994, 1995, 1996, 1997, 1998 (A = 1982 to cut−1, B = cut to 2025); without 2005, without 2012, without 2022, without 2023, and without all four; LOESS detrending; `z_dry` instead of `z_rain`; B′ = 2005–2025 instead of B; regional means (one point per year: mean `dev` against mean `z_rain` of the municipalities); Cruz Alta alone with POWER and with the ANA gauge.

**Decision rule.** The hypothesis is called **supported** only if Δ < 0, the bootstrap 95% interval of Δ excludes 0, the permutation p < 0.05, and Δ keeps its sign in every cut-year and drop-year variant. If the interval contains 0 or the sign flips, the answer is **not supported** and is reported as such. Even when supported, the wording is "consistent with", never causal: plant breeding, sowing dates, soybean area and the quality of old PAM data change over the same years.

## Results

Pending the first run.
