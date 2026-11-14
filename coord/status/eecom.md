# Status — EECOM

> Only the EECOM front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 14:55 — EECOM (CRUZ-ALTA front, Claude Code, issue #26)
Done: Cruz Alta (RS) preparado como CANDIDATO só em `data/dev/dev-cruz-alta/` (fora do sync do app; nada em `data/sites/`; PR #30, com merge da main/#28: `validate --all` passa). JSON do IBGE (bruto + proveniência simples) em `data/cache/ibge/dev-cruz-alta/`, porque o validador só aceita contrato em `output/`. Código IBGE **4306106** confirmado na API de localidades; malha municipal 2022 (GeoJSON, qualidade máxima) e centróide IBGE (−28,703, −53,5626) com procedência e sha256; NASA POWER diário 1981→2026-10 no centróide pelo CLI (`--site dev-cruz-alta`, 13 parâmetros, cache 3,6 MB); PAM SIDRA 1612 soja 1974–2025 via `fieldshift fetch ibge-pam` (módulo `sources/ibge_pam.py` + testes com resposta gravada). Números de seca conferidos: 2022 = 1.337 kg/ha e 2021 = 3.920 kg/ha confirmados (PAM); "4 de 14 safras" depende do critério (3 a 6 com critérios simples; 4 = 2012, 2020, 2022, 2023 quando se exige queda de rendimento e chuva baixa juntas). Evento 2021/22 registrado como candidato da Story 2.5 no README.
Next: nada até a equipe decidir (D-001/#8). Se Cruz Alta virar site: `site.yaml` do SURGEON e rodar `fetch power` para ele.
Blocked by: D-001 / #8 (decisão humana).
Needs from others: SURGEON: linha "IBGE malhas" em `RESOURCES.md` e status da PAM (hoje "candidate"); GUIDO/contratos: estatística oficial (PAM) não tem `DataType` nem unidades (t, kg/ha) no contrato v1.1.0 (nem a malha) — por isso a PAM saiu em CSV + proveniência simples; só vira contrato com PR `contract`.
Contract changes: none

## 2026-11-14 14:35 — EECOM (DADOS-2 front, Claude Code)
Done: #22 em `eecom/indices-validate`: contratos v1.1.0 (MINOR; `VariableKey` + `evap_land_modeled`, `soil_wetness_profile_modeled`, `heat_days`, `frost_days`, `extreme_precip_days`, `extreme_precip_total`, `water_deficit`, `growing_degree_days`; `IndexKey` e `index_key` opcional em `Metric`/`MonthlyProfile`; `ProvenanceMethod.parameters` opcional). Índices no diário antes de agregar (ADR-3), série mensal + perfil 1991–2020 por mês + média anual em `indices.json`, procedência `computed` com método, parâmetros e insumos. POWER agora traz `GWETPROF` e `EVLAND`. `fieldshift validate --all` (ADR-8 camada 1) no job science do CI. dev-floripa regenerado (séries antigas idênticas em valor).
Next: rodar `fetch power` para brasil e nevada quando o `site.yaml` existir (#8), com limiares no bloco `indices:`.
Blocked by: coordenadas dos sites reais (#8, SURGEON).
Needs from others: SURGEON/agrônomo: `indices.heat_tmax_c` (e `gdd_base_c` quando as culturas existirem, D9) no `site.yaml`; hoje valem defaults genéricos (35 °C, 10 °C) marcados na procedência. GUIDO/SURGEON: revisar `content/methods/climate-indices.md` (âncora `climate-indices`), escrita por esta frente porque o teste VL6 do web (#24) reprova âncora sem página. `fetch power` agora mescla o provenance.json por id (pedido da ROTAÇÃO, #25). Arquitetura: déficit hídrico implementado como ET0 − P (brief do #22); a arquitetura escreve "P − ET0"; e o exemplo de âncora lá é `method-et0-fao56`, o código usa `et0-fao56`.
Contract changes: v1.1.0 (MINOR) neste PR, etiqueta `contract`; `packages/contracts/package.json` continua 1.0.0 porque o app fixa a versão exata do workspace.

## 2026-11-14 14:10 — EECOM (DADOS front, Claude Code)
Done: camada NASA POWER (#11, Story 2.2): `fieldshift fetch power --site <id>` (ou `--lat/--lon`), daily community AG 1981→fim do mês anterior, cache bruto em `data/cache/power/<site>/`, retry/backoff, `--offline`; `series.json` + `provenance.json` (contratos v1.0.0) com FR19 completo; agregação mensal ADR-3 (mês só com todos os dias válidos, senão null + known_gaps); ET0 FAO-56 diário em Python puro (testado contra os Exemplos 8 e 18 do FAO-56); flags de calor/geada; ponto DEV `dev-floripa` gravado em `data/dev/` (fora do sync do app). EVPTRNS investigado e descartado (é só transpiração no MERRA-2; ~0 na célula de Floripa).
Next: rodar `fetch power` para brasil e nevada assim que o `site.yaml` existir (#8); `GWETPROF`/`EVLAND` só com chave nova de contrato.
Blocked by: coordenadas dos sites reais (#8, SURGEON).
Needs from others: GUIDO/SURGEON: página `content/methods/` com a âncora `et0-fao56` (VL6) e o método do POWER (Story 2.2 AC8); GUIDO: contagens mensais de calor/geada vão para `ClimateIndices` (sem `VariableKey` para elas); limiar de calor por site no `site.yaml` (SURGEON).
Contract changes: none
