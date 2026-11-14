# Status — EECOM

> Only the EECOM front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 14:10 — EECOM (DADOS front, Claude Code)
Done: camada NASA POWER (#11, Story 2.2): `fieldshift fetch power --site <id>` (ou `--lat/--lon`), daily community AG 1981→fim do mês anterior, cache bruto em `data/cache/power/<site>/`, retry/backoff, `--offline`; `series.json` + `provenance.json` (contratos v1.0.0) com FR19 completo; agregação mensal ADR-3 (mês só com todos os dias válidos, senão null + known_gaps); ET0 FAO-56 diário em Python puro (testado contra os Exemplos 8 e 18 do FAO-56); flags de calor/geada; ponto DEV `dev-floripa` gravado em `data/dev/` (fora do sync do app). EVPTRNS investigado e descartado (é só transpiração no MERRA-2; ~0 na célula de Floripa).
Next: rodar `fetch power` para brasil e nevada assim que o `site.yaml` existir (#8); `GWETPROF`/`EVLAND` só com chave nova de contrato.
Blocked by: coordenadas dos sites reais (#8, SURGEON).
Needs from others: GUIDO/SURGEON: página `content/methods/` com a âncora `et0-fao56` (VL6) e o método do POWER (Story 2.2 AC8); GUIDO: contagens mensais de calor/geada vão para `ClimateIndices` (sem `VariableKey` para elas); limiar de calor por site no `site.yaml` (SURGEON).
Contract changes: none
