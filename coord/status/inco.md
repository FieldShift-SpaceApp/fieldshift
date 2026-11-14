# Status — INCO

> Only the INCO front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 19:55 — INCO (SITE-PAGE front, Claude Code)
Done: site page `/sites/[siteId]` (T2, architecture "Routing"), SSG for every synced site (today `/sites/cruz-alta`), PR `inco/site-page-cruz-alta`. Header (name, point sent to NASA POWER read from the request URL in the provenance, source, record range, unit toggle); recent 24 months of precipitation, Tmax and Tmin (two SVG panels + table, values as published); the 8 metrics of `indices.json`; 1991–2020 month-by-month table from the 7 profiles; ground-check limitations (#31) shown on the page and in the panel, link to `/data-methods#satellite-vs-ground-check`. Every number via `<Value>`/`<MetricValue>`; no VL1 exemption on the page. Loaders `src/lib/data/loaders.ts` (sync reads, contract major check), view model `src/lib/site-view.ts`; home lists the sites. Tests: Vitest (loader, view model, VL1 scan, panel) and Playwright (opens from `/`, every `data-prov` exists in `provenance.json`, panel shows the ground check, no console error, no external request, imperial toggle, no horizontal scroll at 360 px).
Next: switch the header to `site.json` (name, point, default units) and `generateStaticParams` to `index.json` once the pipeline writes them; rotation section (AC4) when a real `rotation-current.json` exists.
Blocked by: nothing.
Needs from others: EECOM/GUIDO — `site.json`, `manifest.json` and `index.json` are not in `data/sites/cruz-alta/output/` yet (the site name lives in `en.ts` meanwhile); a 1991–2020 monthly normal of precipitation/Tmax/Tmin in `indices.json` profiles if the page should show rain and temperature climatology (today it shows recorded months only).
Contract changes: none

## 2026-11-14 14:30 — coordination (Claude Code), ROTAÇÃO front, issue #23
Done: Story 2.3 without real data (PR `inco/rotation-timeline`). Pipeline `fieldshift rotation --site X`: reads `input/site.yaml` (`ag_year`) and `input/rotation-current.yaml`, validates with a `file:line field` error, derives the timeline by rule v1 (transition at establishment, overlap = most protective state, month without a segment = bare, wraps at the end of the cycle) and writes `output/rotation-current.json` + 2 provenance records merged into `output/provenance.json`. pytest tests: year boundary, double cropping, multi-year, explicit and implicit fallow, same rotation in both hemispheres. Web: `<AgYearAxis>` and `<SoilCoverStrip>` (icon + pattern + text, never color alone; `data-prov` on the container), neutral soil-state tokens; Vitest tests. "TEST FIXTURE" identical on both sides (pytest checks that the web JSON is the pipeline output).
Next: with #8, run `fieldshift rotation` for brasil and nevada and wire the site page section (AC4) when the route exists.
Blocked by: #8 (the agronomist's real rotations).
Needs from others: SURGEON — new `reference_ag_year` in `rotation-current.yaml` (agricultural year in which the cycle starts; it only dates the bare-months metric) and `refs` on every segment (AC3, now required). GUIDO/SURGEON — a `content/methods` page with the `soil-cover-derivation` anchor. EECOM — `fetch power` overwrites `provenance.json`; the rotation stage merges, so run rotation after POWER until the `build` orchestrator exists.
Contract changes: none (Rotation v1.0.0 used as is; the YAML model belongs to the pipeline, it is not a published contract).

## 2026-11-14 13:58 — coordination (Claude Code), issue #19
Done: concept-agnostic web foundation (PR `inco/units-provenance`). `lib/units.ts` (ΔT ×1.8 without +32) and `lib/agyear.ts` with parity tests on `packages/contracts/fixtures`; per-page Zustand store (`stores/ui-store.tsx`: only unit and panel, no priorities); `<Value>`/`<MetricValue>` require `provenanceId` and render `data-prov`; `<ProvenancePanel>` (radix-ui Dialog; click 1 opens the FR19 fields, click 2 is the source link); `<DataTypeLabel>`; `<UnitToggle>`. Item 3 solved with component tests only (no demo page). VL1 layer 3 in `tests/e2e/vl1-provenance.spec.ts` on the canary page `/` (the canary's "2026" became `data-prov-exempt="ui"`). New deps: `zustand` 5.1.0 and `@fieldshift/contracts` (workspace).
Next: add `/sites/[siteId]` to the VL1 spec route list and the "every data-prov exists in the registry" check when Story 2.2 brings a real `provenance.json`; `<AgYearAxis>` and `<SoilCoverStrip>` (Story 2.3).
Blocked by: nothing.
Needs from others: nothing.
Contract changes: none (only consumes types and fixtures).
