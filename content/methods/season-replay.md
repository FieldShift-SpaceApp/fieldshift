---
anchor: season-replay
title: Winter 2023 replay (ENSO alert, sowing window, credit, wheat result)
order: 63
refs:
  - label: "NOAA CPC, ENSO Diagnostic Discussions, April and June 2023"
    url: https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_disc_apr2023/ensodisc.shtml
  - label: "MAPA, ZARC risk table 2022/2023 (open data, CC BY)"
    url: https://dados.agricultura.gov.br/dataset/6d3d141c-885e-41a4-ab7f-dc8ff323b96f
  - label: "Banco Central do Brasil, SICOR open data (CusteioMunicipioProduto)"
    url: https://olinda.bcb.gov.br/olinda/servico/SICOR/versao/v2/odata/CusteioMunicipioProduto
  - label: "IBGE, Produção Agrícola Municipal, SIDRA table 1612"
    url: https://sidra.ibge.gov.br/tabela/1612
limitations:
  - "Only measured facts in sequence; the replay does not say what any farmer or bank decided, or why."
  - "The wheat failure count depends on the threshold (11, 14 and 16 of 18 municipalities at 70%, 75% and 80% of trend), and the 18 municipalities are one regional event, not 18 independent cases."
  - "Credit covers only operating credit for wheat registered in SICOR in 18 municipalities, by calendar year of issue (area: January-October)."
  - "The money figures are a team analysis, not independently re-verified; fallow has no sourced cost and is not given a value."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from services/science/src/fieldshift/complements/replay.py and data/sites/cruz-alta/input/replay-2023.yaml (EECOM, complements); review by GUIDO + SURGEON pending (see SI-USAGE.md). -->

**What it is.** The 2023 winter at Cruz Alta as a sequence of dated or annual facts: the NOAA El Niño Watch (13 April) and Advisory (8 June), the ZARC sowing window for rainfed wheat, operating credit for wheat in the region, the wheat failures, and the money per hectare of wheat and of a cover crop.

**Transcribed events.** Each one comes from `data/sites/cruz-alta/input/replay-2023.yaml` with its primary source, attribution and limitations; every number there was checked against its primary source by the team's independent verification, except the money figures, which are flagged.

**Computed event (wheat failures).** `fieldshift complements` reads the IBGE PAM wheat yields of the 18 Planalto Médio municipalities (downloaded by `fieldshift fetch ibge-pam --product 2716`), fits a least-squares linear trend per municipality on 1981-2025 (years with a positive yield, 2023 included, at least 10 years) and counts the municipalities whose 2023 yield is below 75% of the trend value, with 70% and 80% as sensitivity.
