# Status — INCO

> Only the INCO front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 13:58 — coordenação (Claude Code), issue #19
Done: fundação web conceito-agnóstica (PR `inco/units-provenance`). `lib/units.ts` (ΔT ×1,8 sem +32) e `lib/agyear.ts` com testes de paridade sobre `packages/contracts/fixtures`; store Zustand por página (`stores/ui-store.tsx`: só unidade e painel, sem prioridades); `<Value>`/`<MetricValue>` exigem `provenanceId` e renderizam `data-prov`; `<ProvenancePanel>` (Dialog do radix-ui; clique 1 abre os campos do FR19, clique 2 é o link da fonte); `<DataTypeLabel>`; `<UnitToggle>`. Item 3 resolvido só com testes de componente (sem página de demonstração). VL1 camada 3 em `tests/e2e/vl1-provenance.spec.ts` na página-canário `/` (o "2026" do canário ficou `data-prov-exempt="ui"`). Novas deps: `zustand` 5.1.0 e `@fieldshift/contracts` (workspace).
Next: incluir `/sites/[siteId]` na lista de rotas do spec VL1 e a checagem "todo data-prov existe no registro" quando a Story 2.2 trouxer `provenance.json` real; `<AgYearAxis>` e `<SoilCoverStrip>` (Story 2.3).
Blocked by: nada.
Needs from others: nada.
Contract changes: none (só consome tipos e fixtures).
