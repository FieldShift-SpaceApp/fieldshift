# Did soybean after a winter cover crop suffer less in the drought? A 30 m test with NASA HLS (Cruz Alta, RS, summers 2020/21–2025/26)

> **SI-assisted:** the hypothesis (use the per-pixel winter classes of `analysis/rotation-fingerprint/` as the treatment of a natural experiment on soybean vigour in the drought summers) was synthesized with Claude Code (Anthropic) at the team lead's request; the scripts and this text were written with Claude Code. Every number comes from running the scripts in this folder; none was produced by the AI. Human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

**Status of this file:** the Method section below was written and committed **before any model was run** (pre-registration). Results are added in a later commit; the method is not changed after seeing them. Any deviation is listed under "Deviations".

## Credit and what is already known

This is a re-test, at 30 m and with explicit winter classes, of a natural experiment already run by **João** (FieldShift team) in the private research repository (`docs/research/rotacao/A1_experimento_natural.md`, `RESUMO.md`; Landsat 120 m and MODIS 250 m–1 km, 2002–2025). His verdicts:

1. **Not validated:** a winter crop protecting soybean from drought (municipal panel and pixel panels; the drought interaction is about zero or does not pass the placebo).
2. **Partly validated:** on the same piece of field, soybean after a greener winter has a better canopy in a normal year (+0.026 NDVI per SD of winter NDVI, Landsat 120 m), and that gain does not grow in dry summers (+0.0015 [−0.004; +0.007]).
3. **Soybean enters later after a green winter** (December NDVI lower), read as later sowing, pending a real planting date.

An earlier team probe with Sentinel-2 k-means groups (2022 only, no planting-date control) also found no sign and attributed the group differences to the sowing calendar.

What is new here: (a) **classes, not a continuous winter NDVI**: wheat-like cereal (T), autumn-sown cover crop (C) and other (O) per 30 m pixel and year, from `analysis/rotation-fingerprint/`; João's winter NDVI cannot tell a cover crop from a wheat crop; (b) **a planting-date proxy per pixel-year** from the HLS green-up of the summer crop, used as an explicit control; (c) 30 m pixels inside ~1 km blocks, with block × summer fixed effects for local rain.

## Question (pre-registered)

In Cruz Alta, did the soybean that followed a **winter cover crop (C)** keep more of its canopy in the drought summers than the soybean that followed a **wheat-like winter cereal (T)**, on the same pixel, compared with normal summers, **after allowing for the planting date**?

## Method (pre-registered; written before running any model)

**Units.** Pixel-summers: every 30 m cropland pixel of `analysis/rotation-fingerprint/` (WorldCover 2021 cropland in the IBGE polygon, 1,165,531 pixels) in the summers 2020/21 … 2025/26. Summer Y/Y+1 follows winter Y.

**Treatment.** The winter class of the pixel in winter Y from `analysis/rotation-fingerprint/` (main run): T, C, O; fallow P (0.3–0.8% of the cropland) is merged into O. Reference: T. Unclassified pixel-years are dropped.

**Outcome (NASA HLS NDVI).** Half-month median composites from 1 October (year Y) to 31 March (Y+1), 12 half-months, built exactly as the fingerprint composites (Fmask-clear observations, median, linear gap fill). October–November come from the fingerprint raw vectors; December–March are read by `scenes_summer.py` with the same reader. A pixel-summer is kept when ≥ 8 of the 12 half-months are clear, ≥ 2 of the 4 January–February half-months are clear and ≥ 1 of November-1 … December-2 is clear.

- **Primary:** mean NDVI of January-1 … February-2 (the "integral" of January–February; the window that tracks soybean yield in Cruz Alta, municipal r = 0.80 in the team's research note `cruz-alta-satelite.md`).
- **Secondary:** peak NDVI of December-1 … February-2 (comparable with João's peak).
- A within-summer drop ("veranico") is **not** used: in a pixel planted in early October the canopy matures in February, so a drop is confounded with maturity.

**Drought summers.** Fixed in advance from the team's earlier work (soybean yield −53% and −33% in IBGE PAM, January–February NDVI z −2.95 and −1.36): **2021/22 and 2022/23**. NASA POWER (PRECTOTCORR) December–February rainfall is used only as a confirmation (`fetch_power.py`, `results/power_rain_dec_feb.csv`): 181.5 mm and 185.2 mm, the 2nd and 3rd driest of 26 summers (2000/01–2025/26). The other four summers are "normal" (2020/21 302 mm, 2023/24 460 mm, 2024/25 323 mm, 2025/26 372 mm).

**Planting-date proxy.** Summer green-up = the first half-month after the lowest half-month of October-1 … December-2 (the gap between the winter canopy and the summer crop) whose NDVI is ≥ 0.50, searched up to February-1; otherwise "none". Strata: ≤ November-1, November-2, December-1, December-2, January-1, ≥ January-2, none. It is a proxy for emergence, not a sowing date. Because cover crops are killed earlier than wheat is harvested, the planting date is partly a **consequence** of the treatment (a mediator), so two estimands are reported: **total** (no planting-date control) and **direct** (within the same planting-date stratum).

**Models.** OLS with fixed effects removed by alternating projections:

- **M1 total:** `y = pixel FE + (1 km block × summer) FE + b_C·C + b_O·O + d_C·C·Drought + d_O·O·Drought`
- **M2 direct (main test):** M1 + (planting-date stratum × summer) FE.
- **M3 matched:** M1 on the pixel-summers in the planting-date strata where both C and T have ≥ 10% of their pixel-summers (computed mechanically from the data).

Reported effects: **C − T in normal summers = b_C**; **C − T in drought = b_C + d_C**; **protection = d_C** (C − T in drought minus C − T in normal summers). The pixel fixed effect absorbs soil, slope and anything else fixed in the pixel; the block × summer fixed effect absorbs the rain of that summer in that ~1 km block (blocks of 33 × 33 pixels, 990 m).

**Inference.** Standard errors clustered by 1 km block (CR1). With six summers, a year-clustered error is not reliable, so the year dimension is checked by (i) the per-summer C − T contrast (pixel-summers of one summer, block FE + planting-date stratum FE), (ii) leave-one-summer-out and (iii) placebo P2.

**Placebos.** **P1 future winter:** the same models with the class of winter **Y+1** (after the summer) as a fake treatment (summers 2020/21–2025/26, winters 2021–2026; 2026 provisional); a real effect of the previous winter should not show up here. **P2 fake drought:** among the four normal summers only, each one in turn labelled "drought"; the spread of the four fake d_C is the year-to-year noise a real d_C has to beat.

**Robustness.** R1 history: share of cover-crop winters in 2020 … Y as a continuous treatment (× Drought), summers from 2021/22. R2 conservative classes: drop pixel-years whose winter green-up is within one half-month of the T/C split (keep C with green-up ≤ June-1, T with green-up ≥ July-2). R3 the secondary outcome (peak). R4 leave-one-summer-out.

**Decision rule (fixed before the results).** "Soybean after cover crop suffered less in the drought" is supported only if, in **M2**, d_C > 0 with a 95% block-clustered CI above zero, **and** d_C is larger than every fake d_C of P2, **and** the P1 placebo d_C is not of similar size (less than half of d_C). Otherwise the answer is "not shown". A positive b_C alone (better canopy in normal years) is **not** a drought-protection result.

**Translation to yield.** Only if the effect passes the rule: by the municipal relation between January–February NDVI and PAM soybean yield (team note `cruz-alta-satelite.md`, r = 0.80, n = 25), with the caveat that a municipal slope is not a field response.

## Results

Pending (added after the run, in a separate commit).

## Deviations

None so far.
