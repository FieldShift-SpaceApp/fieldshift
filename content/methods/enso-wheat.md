---
anchor: enso-wheat
title: El Niño and wheat losses in the Planalto Médio (reproducible analysis)
order: 45
refs:
  - label: "Analysis folder with scripts, results and the full write-up (analysis/enso-wheat)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/enso-wheat
  - label: "IBGE PAM, SIDRA table 1612 (municipal crop yield)"
    url: https://servicodados.ibge.gov.br/api/v3/agregados/1612/metadados
  - label: "NOAA CPC Oceanic Niño Index (ONI)"
    url: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
  - label: "NOAA CPC ENSO Diagnostic Discussion archive"
    url: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml
  - label: "Banco Central do Brasil, rural credit data matrix (SICOR), ODbL"
    url: https://dadosabertos.bcb.gov.br/dataset/matrizdadoscreditorural
  - label: "Atlas Digital de Desastres no Brasil (MIDR/SEDEC), downloads"
    url: https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml
  - label: "IRI ENSO forecasts (Columbia University)"
    url: https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/
limitations:
  - "The ENSO and wheat result rests on 8 El Niño and 5 La Niña winters (1981-2025). The 18 municipalities share the weather and fail together, so the 137 and 86 municipal seasons are not independent cases; the evidence is the winter-level permutation test (p = 0.003)."
  - "The soybean contrast after El Niño and La Niña (6.5% vs 23.0%) does not hold as a rate: it comes from 1987/88 and 2022/23, and the winter-level test gives p = 0.40. 2022/23 is a case, not a rate."
  - "Municipal drought records of the disaster Atlas after La Niña vs El Niño (45.8% vs 1.9%) do not hold as a rate: without 2022 the La Niña share is 27.8%, the same as neutral (27.3%). The Atlas licence is not declared, so its derived counts are not committed."
  - "ENSO forecasts issued in February did not beat a forecast of 'always neutral' on the phase of the following June-August, so the historical link does not by itself make the season predictable at wheat sowing."
  - "Yield is municipal (IBGE PAM), the trend a simple linear fit, and the ONI is revised by NOAA (2009 enters the El Niño group with ONI JJA = +0.50 exactly). The association is statistical, not a measured agronomic cause."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the scripts and results in analysis/enso-wheat (run of 2026-11-14), ported from the team's independent verification; human review pending (see SI-USAGE.md). -->

**Why this analysis.** Winter wheat and summer soybean share the same fields in southern Brazil. The team asked whether the El Niño–Southern Oscillation (ENSO) phase of the winter changes the chance of a low-yield wheat season in the Planalto Médio of Rio Grande do Sul (Cruz Alta and 17 neighbouring municipalities). Every number on this page comes from the scripts in [`analysis/enso-wheat/`](../../analysis/enso-wheat/README.md), which download the public sources and can be rerun with one command; the run of 2026-11-14 reproduced the team's independent verification to the last digit.

**Criterion.**

- **Low-yield season:** municipal wheat yield (IBGE PAM, SIDRA table 1612) below **75% of the municipality's own linear trend**, 1981–2025.
- **Winter phase:** NOAA CPC ONI of June–August: **El Niño ≥ +0.5**, **La Niña ≤ −0.5**, otherwise neutral.
- **Evidence:** a permutation test that shuffles the phase between winters while keeping each winter's municipalities together, because neighbouring municipalities share the weather.

**What we found.**

| Winter phase | Winters | Municipal wheat seasons | Below 75% of trend |
|---|---|---|---|
| El Niño | 8 | 137 | **73 (53.3%)** |
| Neutral | 32 | 557 | 96 (17.2%) |
| La Niña | 5 | 86 | **3 (3.5%)** |

- **Winter-level test:** difference of 49.8 percentage points, **p = 0.003**.
- **2023 (El Niño):** wheat fell below the threshold in **14 of 18** municipalities (11 at a 70% threshold, 16 at 80%).
- **Robustness:** El Niño stays far above neutral, and La Niña below it, in all 12 variants (threshold 70/75/80%, linear or quadratic trend, 1981–2025 or 1990–2025).
- **Concentration:** four winters (1982, 2002, 2015, 2023) carry most of the losses, while 1987 had 0 of 16 and 2009 had 1 of 18.

**Context for 2023.** NOAA CPC issued an El Niño Watch on 13 April 2023 and the El Niño Advisory on 8 June 2023. Wheat operating credit in the 18 municipalities stayed stable that year: full-year value −3.1% in real terms (BRL of Dec/2025, IPCA), financed area of January–October +2.3% (BCB SICOR).

**How to say it.** "Wheat fell below 75% of trend in 53% of municipal seasons in El Niño winters (8 winters, 18 municipalities, 1981–2025), against 3.5% in La Niña winters." Not "in 53% of El Niño winters".
