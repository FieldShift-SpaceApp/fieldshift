# Status — INCO

> Only the INCO front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 14:30 — coordenação (Claude Code), frente ROTAÇÃO, issue #23
Done: Story 2.3 sem dado real (PR `inco/rotation-timeline`). Pipeline `fieldshift rotation --site X`: lê `input/site.yaml` (`ag_year`) e `input/rotation-current.yaml`, valida com erro `arquivo:linha campo`, deriva a linha do tempo pela regra v1 (transição no estabelecimento, sobreposição = estado mais protetor, mês sem segmento = nu, volta no fim do ciclo) e grava `output/rotation-current.json` + 2 registros de procedência mesclados em `output/provenance.json`. Testes pytest: virada do ano, dupla safra, plurianual, pousio explícito e implícito, mesma rotação nos 2 hemisférios. Web: `<AgYearAxis>` e `<SoilCoverStrip>` (ícone + padrão + texto, nunca só cor; `data-prov` no contêiner), tokens neutros de estado do solo; testes Vitest. Fixture "TEST FIXTURE" igual nos dois lados (pytest confere que o JSON do web é a saída do pipeline).
Next: com o #8, rodar `fieldshift rotation` para brasil e nevada e ligar a seção da página do site (AC4) quando a rota existir.
Blocked by: #8 (rotações reais do agrônomo).
Needs from others: SURGEON — `reference_ag_year` novo no `rotation-current.yaml` (ano agrícola em que o ciclo começa; só data a métrica de meses nus) e `refs` em todo segmento (AC3, agora obrigatório). GUIDO/SURGEON — página `content/methods` com a âncora `soil-cover-derivation`. EECOM — `fetch power` sobrescreve `provenance.json`; o estágio de rotação mescla, então rodar rotação depois do POWER até o orquestrador `build` existir.
Contract changes: none (Rotation v1.0.0 usado como está; o modelo do YAML é do pipeline, não é contrato publicado).

## 2026-11-14 13:58 — coordenação (Claude Code), issue #19
Done: fundação web conceito-agnóstica (PR `inco/units-provenance`). `lib/units.ts` (ΔT ×1,8 sem +32) e `lib/agyear.ts` com testes de paridade sobre `packages/contracts/fixtures`; store Zustand por página (`stores/ui-store.tsx`: só unidade e painel, sem prioridades); `<Value>`/`<MetricValue>` exigem `provenanceId` e renderizam `data-prov`; `<ProvenancePanel>` (Dialog do radix-ui; clique 1 abre os campos do FR19, clique 2 é o link da fonte); `<DataTypeLabel>`; `<UnitToggle>`. Item 3 resolvido só com testes de componente (sem página de demonstração). VL1 camada 3 em `tests/e2e/vl1-provenance.spec.ts` na página-canário `/` (o "2026" do canário ficou `data-prov-exempt="ui"`). Novas deps: `zustand` 5.1.0 e `@fieldshift/contracts` (workspace).
Next: incluir `/sites/[siteId]` na lista de rotas do spec VL1 e a checagem "todo data-prov existe no registro" quando a Story 2.2 trouxer `provenance.json` real; `<AgYearAxis>` e `<SoilCoverStrip>` (Story 2.3).
Blocked by: nada.
Needs from others: nada.
Contract changes: none (só consome tipos e fixtures).
