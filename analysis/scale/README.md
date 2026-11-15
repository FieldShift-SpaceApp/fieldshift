# Scale of the problem: the numbers on the submission page, rechecked from the sources

> **SI-assisted:** script and text written with Claude Code (Anthropic) from the team's scale research of 2026-11-14 in the private planning repository; every number below was produced by running `scale.py` against the public sources, not by the AI. Human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

The submission page ([`docs/submission/page-draft.md`](../../docs/submission/page-draft.md), fields 2 and 5) says how big the winter-wheat decision is beyond the 18 study municipalities. `scale.py` downloads the sources again and checks each number at the precision the page uses. It exits with an error if any number no longer matches.

## Result (run of 2026-11-14 BRT; all checks pass)

| Number on the page | Recomputed from the source | Source | Match |
|---|---|---|---|
| Rio Grande do Sul planted **1.16 million ha** of wheat in 2025 | 1,164,275 ha | IBGE PAM, SIDRA 1612, variable 109 (planted area) | yes |
| **46%** of Brazil's wheat area | 46.3% (Brazil: 2,515,514 ha) | same | yes |
| on **about 20,000 farms** (2017 Census of Agriculture) | 19,716 establishments that produced wheat in Rio Grande do Sul | IBGE Census of Agriculture 2017, SIDRA 6957, variable 10084 | yes |
| the state's wheat output fell from **5.3 to 2.6 million t** (2022 → 2023) | 5,299,994 t → 2,587,340 t (5.30 → 2.59; −51.2%) | IBGE PAM, SIDRA 1612, variable 214 (production) | yes |
| Proagro approved **R$ 2.07 billion** in wheat claims (2023) | R$ 2,067,090,847 approved ("deferido") for Rio Grande do Sul wheat contracts issued in 2023, on 92.6% of the insured area (619,786 of 669,546 ha) | BCB Proagro data matrix, "regiao" view, file `MATRIZ_PROAGRO_REGIAO_2023.gz` (published 2026-09-03) | yes |
| field 5: **about 10%** of the world's wheat area | 10.3% for Argentina + Uruguay + Australia + **Brazil** (9.0% without Brazil), wheat area harvested 2024 | FAOSTAT, Production_Crops_Livestock (bulk, normalized) | yes, but see the wording note below |

All values and the exact page wording are in `results/scale.json` (`checks`); context numbers in `context`.

**Wording note for field 5.** The page says "Rio Grande do Sul, Argentina, Uruguay and Australia together grow wheat on about 10%", but the 10% (10.3%) is computed with **all of Brazil** from FAOSTAT. Replacing Brazil with Rio Grande do Sul's harvested area of 2024 (IBGE PAM: 1,331,698 ha) gives 9.6%: still "about 10%", but it mixes two sources (PAM and FAOSTAT). Suggested text: "Brazil, Argentina, Uruguay and Australia together grow wheat on about 10% of the world's wheat area (FAOSTAT 2024)".

## Data

| Source | Endpoint | Terms | Committed here? |
|---|---|---|---|
| IBGE PAM, SIDRA table 1612 | `apisidra.ibge.gov.br/values/t/1612/n1/all/n3/43/v/109,216,214/p/2014-2025/c81/2716` | public federal data; cite IBGE | `results/ibge_pam_1612_wheat.csv` (Brazil and Rio Grande do Sul, wheat, 2014–2025) |
| IBGE Census of Agriculture 2017, SIDRA table 6957 | `apisidra.ibge.gov.br/values/t/6957/...` (Brazil, South, Rio Grande do Sul; variable 10084; totals of typology, producer condition and activity group) | public federal data; cite IBGE | `results/ibge_census2017_6957_establishments.csv` |
| Banco Central do Brasil, Proagro data matrix, "regiao" view | file list `www.bcb.gov.br/api/servico/sitebcb/Documentos/byListGuid?...&pasta=%2Fregiao` ([page](https://www.bcb.gov.br/estabilidadefinanceira/proagro)) | BCB site terms: reproduction allowed with the source cited ([Política de Privacidade e Termos de Uso](https://www.bcb.gov.br/acessoinformacao/politicaprivacidade)) | `results/bcb_proagro_wheat_rs_2023_file.csv` (Rio Grande do Sul wheat totals by issue year found in the 2023 file) |
| FAOSTAT, Production_Crops_Livestock (bulk, normalized) | `bulks-faostat.fao.org/production/Production_Crops_Livestock_E_All_Data_(Normalized).zip` (about 34 MB) | CC BY 4.0 ([FAO database terms](https://www.fao.org/contact-us/terms/db-terms-of-use/en/)); cite "FAO. FAOSTAT: Crops and livestock products. Accessed on 14 November 2026. Licence: CC-BY-4.0." | `results/faostat_wheat_area_harvested.csv` (5 areas, wheat, 2020–2024) |

Raw downloads (Proagro 2023 file and the FAOSTAT zip) go to `~/.cache/fieldshift/scale/` (or `--raw DIR`) and are never committed. `results/sources.json` records every URL and access time (UTC); `results/run_info.json` the run time and library versions.

## Limitations

- **The census is from 2017.** the wheat area has changed since then (1.16 million ha planted in 2025), so today's number of farms is probably different; no newer source has this breakdown. Say "about 20,000 farms (2017 Census)".
- **Proagro covers only financed area that enrolled** (669,546 ha in 2023, less than half of the planted area), and this view has no cause of loss: the R$ 2.07 billion was approved *in* the El Niño year, not attributed to El Niño. The cause by event is in [`analysis/ground-truth-proagro/`](../ground-truth-proagro/README.md) (18 municipalities).
- **BRL values are nominal.** IBGE PAM 2025 is the latest year published; PAM values can be revised by IBGE.
- **FAOSTAT 2024** is the latest year available; Uruguay's 2024 value carries FAO flag `I` (imputed); the others carry `A` (official figure) (column `flag`).

## Reproduce

From the repository root, with [uv](https://docs.astral.sh/uv/):

```bash
uv run --with httpx==0.28.1 python -I analysis/scale/scale.py
```

The script is linted with Ruff (`ruff.toml` here); it is outside the `services/science` package and its CI job. The run of 2026-11-14 matched, to the unit, the team's private scale research of the same day (1,164,275 ha; 2,515,514 ha; 19,716; 5,299,994 t and 2,587,340 t; R$ 2,067,090,847 on 619,786 of 669,546 ha; FAOSTAT 19.7 million ha for AR + UY + AU and 219.5 million ha world).
