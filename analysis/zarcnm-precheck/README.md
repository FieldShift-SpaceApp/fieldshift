# ZarcNM pre-check: how three winter paths after soybean score on Brazil's soil-management rule (Cruz Alta, RS)

> **SI-assisted:** origin: the team generated the starting ideas at a human ideation meeting; at the team lead's request, SI helped compare and synthesize options from those ideas and verified data; the team chose the direction (D-001). This idea (score the three winter paths against the ZarcNM rule) is one of those SI-synthesized options. The rules module, the pre-check script, the tests and this text were written with Claude Code from the norm texts. Every rule below is transcribed from the norm with its item number; every straw number comes from the committed straw clock or the cited literature; none was produced by the AI. Human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

Method summary for the app: [`content/methods/zarcnm-precheck.md`](../../content/methods/zarcnm-precheck.md). Output read by the app: [`results/precheck.json`](results/precheck.json).

## What this is

Since the 2026/27 season, soybean in Rio Grande do Sul has a **ZarcNM** (Zoneamento Agrícola de Risco Climático por Níveis de Manejo) zoning (Portaria SPA/MAPA 209/2026). A field is placed in one of four management levels, NM1 to NM4, from six indicators (IN SPA/MAPA 2/2025). In the 2026 pilot, the federal insurance-premium subsidy for soybean is **20 / 30 / 35 / 40%** of the premium for NM1 / NM2 / NM3 / NM4 (Resolução CGSR 111/2026).

This folder (1) implements the published rule (`zarcnm_rules.py`) and (2) estimates, for three winter paths after soybean (soybean-wheat, soybean-cover with black oat + common vetch, soybean-winter fallow), the level of the three **management** indicators that satellites and agronomy can estimate, and the NM range that follows **if** the soil tests are at a given level.

## What this is NOT

- **A pre-check, not a certificate.** The official class is produced only by Embrapa's SINM, after accredited agents register the field's identification, remote-sensing history and soil analyses (IN 2/2025, items 3, 4.1-4.6). This folder never states a final NM.
- Not a field measurement: straw cover is arithmetic, years without tillage is an assumption, and three indicators need a soil test.

## Result

| Path | T (no-till) | C (straw cover) | D (diversity) | NM range if soil tests at level 4 | Subsidy |
|---|---|---|---|---|---|
| Soybean-wheat | 4 (assumed) | 2-3 (41-89%) | 2 | **NM2-NM3** | 30-35% |
| Soybean-cover (oat + vetch) | 4 (assumed) | 2-4 (47-99%) | 3 | **NM3-NM4** | 35-40% |
| Soybean-fallow | 4 (assumed) | 1-2 (not modelled) | 1 | **NM1-NM2** | 20-30% |

Each path reads "pre-check: 3 of 6 indicators observable; NM range a-b if soil tests are at level 4; contour to confirm". With soil tests at level 3 the ranges are NM2-3, NM3 and NM1-2; at level 2 every path is NM2 or lower (the fallow NM1-2); at level 1 every path is NM1 (`nm_range_by_soil_level` in the JSON, with the three soil indicators at the same level).

Why: the winter path moves C and D. Soybean-fallow has D at level 1 whatever happens (3 crops, 1 species), so one more indicator at level 1 gives NM1 (item 3.2.1-IV-a); read literally it is also "soybean on soybean" (item 3.2.1-II, NM1) and a legume-only succession (item 3.2.1-III, at most NM2). Soybean-wheat has D at level 2; if straw cover is also at level 2, two indicators at level 2 cap it at NM2 (item 3.2.1-IV-b). Soybean-cover reaches D level 3 by either branch of the table, and NM4 needs at least 60% straw cover before sowing.

## The rules, with citation (IN SPA/MAPA 2/2025, Annex, soybean)

**Table 1** (`level_*` functions):

| # | Indicator | Level 1 | Level 2 | Level 3 | Level 4 |
|---|---|---|---|---|---|
| 1 | V% 0-20 cm, CEC < 5 | V < 35 | 35 ≤ V < 40 | 40 ≤ V < 50 | V ≥ 50 |
| 1 | V%, 5 ≤ CEC < 10 | V < 40 | 40 ≤ V < 45 | 45 ≤ V < 55 | V ≥ 55 |
| 1 | V%, CEC ≥ 10 | V < 50 | 50 ≤ V < 55 | 55 ≤ V < 65 | V ≥ 65 |
| 2 | Ca 20-40 cm (cmolc/dm³) | Ca < 0.5 | 0.5 ≤ Ca < 1 | 1 ≤ Ca < 1.5 | Ca ≥ 1.5 |
| 3 | m% 20-40 cm | m ≥ 20 | 10 ≤ m < 20 | 5 ≤ m < 10 | m < 5 |
| 4 | T, complete years without tillage | T < 3 | 3 ≤ T < 5 | 5 ≤ T < 8 | T ≥ 8 |
| 5 | C, straw cover before sowing (%) | 0 ≤ C < 30 | 30 ≤ C < 60 | 60 ≤ C < 90 | C ≥ 90 |
| 6 | D, crops in the last 3 agricultural years | other levels not met | ≥ 4 crops, ≥ 2 species, 2 families | ≥ 6 crops, ≥ 2 species, 2 families, and 1 cover > 4 months OR 3 covers > 45 days each | ≥ 6 crops, ≥ 4 species, 2 families, 1 cover > 4 months AND 2 covers > 45 days each |

- Item 2.2: no classification if any indicator is missing (`IncompleteIndicatorsError`).
- Item 2.3: localized tillage in sowing rows, terraces and fire-break headlands does not reset T.
- Item 2.4 (diversity): I, a grass as 3rd crop or in the autumn window replaces one cover of less than 4 months; II, grazed covers still count; III, silage/hay crops are not counted; IV, covers of more than 4 months must include a grass; V, pasture kept 12+ months in crop-livestock integration replaces the crop-count requirement.
- Item 3.2: mean Mi of the six levels. NM1 if Mi ≤ 1.75; NM2 if 1.75 < Mi ≤ 2.75; NM3 if 2.75 < Mi ≤ 3.50; NM4 if Mi > 3.50.
- Item 3.2.1, overriding the mean: I, slope ≥ 3% without contour sowing on at least 75% of the area in the last year → NM1; II, two or more consecutive soybean crops → NM1; III, legume-only crop before or after soybean → at most NM2; IV-a, two or more indicators at level 1 → NM1; IV-b, two or more at level 2, or one at 1 and one at 2 → NM2; V, mean at level 3-4 with m% at level 1 → NM2, with m% at level 2 → NM3.
- **Portaria SPA/MAPA 209/2026, item 2.4** (added here, not in the IN): the class is limited to the NM whose root depth Ze (40 / 60 / 80 / 100 cm for NM1-NM4, item 2.5) is below the useful soil depth Zus; Zus < 50 cm stays at NM1.

**Interpretations** (the text or the table layout is ambiguous; each one is marked `INTERPRETATION` in the code and covered by a test):

1. "More than 4 months" = more than 121.75 days (4 average months).
2. The 6-crop minimum of level 3 applies to both sides of its "OU".
3. At level 4, the "2 covers of more than 45 days" are in addition to the cover of more than 4 months (3 covers in all).
4. When several locks apply, the most restrictive wins (item 3.2 only says they have priority over the mean).
5. "Consecutive soybean crops": the norm does not say whether a fallow winter breaks the sequence. Read literally, soybean-fallow-soybean is consecutive; the pre-check keeps both readings in the range.
6. An item 2.4-I grass counts as one cover of more than 45 days.

## How the three management indicators are estimated

| Indicator | Satellite? | How | Source |
|---|---|---|---|
| T, years without tillage | yes (item 6.8: sudden changes in the NDVI/NDTI series) | **Assumed** 8+ years of continuous no-till (level 4) for all paths; the Landsat series from another front will confirm or lower it | IN 2/2025 items 2.3, 6.8 |
| C, straw cover | yes (item 6.7: NDTI in the month before sowing) | Straw on 1, 16 and 30 November from the straw clock ([`../storms-bare-soil/results/straw_clock.json`](../storms-bare-soil/results/straw_clock.json)) converted with Gregory (1982): cover = 1 − exp(−Am × kg/ha), Am 0.00024 (wheat stems only, McCool et al. 2006) to 0.00054 ha/kg (complete wheat residue, Gregory as quoted by McCool et al. 2006). Fallow: no winter straw; level 1-2 because soybean residue and weeds are not modelled | straw clock; McCool et al. 2006 |
| D, diversity | yes, with the farmer's declaration (item 4.1-I and II) | Table 1 row 6 and item 2.4 applied to each path's 3-year calendar. Cover crop sown 15 Apr-31 May (scenario), desiccated 1 Sep-31 Oct (straw clock window): 93-199 days | IN 2/2025; Santos et al. 2019 |
| V%, Ca, m% | **no** | not observable from satellite: needs soil test (0-20 and 20-40 cm, accredited lab, valid 24 months) | IN 2/2025 items 4.1-III, 7 |

## Limitations

1. **3 of 6 indicators are chemical** (V%, Ca, m%) and need a soil test; the NM range is conditional on them, and m% alone can downgrade NM4 to NM3 or NM2 (item 3.2.1-V).
2. **Contour sowing is not checked.** On slopes ≥ 3% (NASADEM, item 6.3, another front) a missing contour forces NM1 whatever the path. The useful soil depth (Portaria 209 item 2.4) is assumed deep.
3. **The straw threshold has no calibration.** Straw t/ha is arithmetic from one trial's half-lives; the mass-to-cover coefficients are US wheat measurements (no black-oat value was found); the norm itself measures cover with NDTI, for which no threshold was calibrated against field cover here. That is why C is a wide range.
4. **T is an assumption** until the Landsat series is read for the field.
5. **The subsidy budget is small:** Resolução CGSR 111/2026 sets R$ 1 million for soybean in the 2026 pilot, shared by four states (PR, SC, RS, MS, as reported by Agrolink), only for fields classified by Embrapa's method.
6. **No R$/ha.** No average soybean premium per hectare for Rio Grande do Sul was found (the PSR 2024 report gives the national soybean average, about R$ 415/ha, and RS totals for all crops), so `subsidy_brl_per_ha` is `null`.
7. The CGSR 111 percentages and budget were read on the Legismap transcription, not on the DOU PDF.
8. Portaria 209/2026 item 2.1 speaks of "sete indicadores"; IN 2/2025 Table 1 lists six, and this pre-check follows the IN.

## Reproduce

```bash
cd analysis/zarcnm-precheck
uv run --project ../../services/science python precheck.py      # writes results/precheck.json
uv run --project ../../services/science pytest -q tests          # 107 tests: every Table 1 row, item 3.2 interval and lock
```

Standard library only; no network. `tests/test_precheck.py` checks that the committed JSON equals a fresh run (except `generated_at`). These tests are not part of the CI `science` job, which runs only `services/science`.

## Sources

- IN SPA/MAPA nº 2, de 8 de julho de 2025, Annex (soybean), DOU 09/07/2025, ed. 127, seção 1, p. 3.
- Portaria SPA/MAPA nº 209, de 30 de junho de 2026, DOU 03/07/2026 ([MAPA page](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/portarias/safra-vigente/rio-grande-do-sul)).
- Resolução CGSR nº 111, de 28 de abril de 2026 ([Legismap transcription](https://legismap.com.br/leis-e-normas/resolucao-cgsr-n-111-de-28-04-2026)); states of the pilot: [Agrolink, 07/08/2026](https://www.agrolink.com.br/noticias/seguro-rural-em-agosto--psr-reserva-r--1-milhao-para-soja_517600.html).
- McCool, D.K. et al. (2006), Residue characteristics for wind and water erosion control, 14th ISCO Conference ([PDF](https://topsoil.nserl.purdue.edu/isco/isco14/5%20Erosion%20Process%20&%20Control/Oral/T5-McCool-Residue%20Characteristics%20for%20Windl-USA.pdf)), quoting Gregory, J.M. (1982), Trans. ASAE 25:1333-1337.
- Straw clock and its sources (Campos et al. 2011; Aita & Giacomini 2003; Santos et al. 2019): [`../storms-bare-soil/`](../storms-bare-soil/README.md).
- MAPA, [Relatório Geral PSR 2024](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/seguro-rural/dados/relatorios/relatorio-geral-psr-2024.pdf), Table 11.
