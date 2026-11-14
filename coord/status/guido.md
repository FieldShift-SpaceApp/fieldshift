# Status — GUIDO

> Only the GUIDO front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 16:15 — CONTRACTS chat (coordenação, Claude Code)
Done: issue #12 — contratos v1.0.0 em pydantic (`services/science/src/fieldshift/contracts/`), `fieldshift contracts export` → `packages/contracts/schema/contracts.schema.json`, `npm run contracts` → `ts/generated.ts` + `ts/index.ts` (`CONTRACT_MAJOR = 1`), `fieldshift.calendar.agyear` + `fixtures/agyear-cases.json` e `fixtures/units-cases.json` (delta_degC ×1,8 sem +32), steps de drift no CI.
Next: `apps/web/src/lib/agyear.ts` e `units.ts` consumirem os fixtures (INCO); validador entre arquivos (`fieldshift validate --all`) quando houver dados.
Blocked by: nada.
Needs from others: SURGEON — `site.yaml` da arquitetura tem `heat_threshold_degC`, que não existe no contrato `Site`; o modelo de entrada YAML fica para a Story 2.2. INCO — confirmar as unidades imperiais do `units-cases.json` (degF, in, ft, ac, mph).
Contract changes: PR guido/contracts-codegen (cria os contratos v1.0.0)
