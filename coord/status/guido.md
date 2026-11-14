# Status — GUIDO

> Only the GUIDO front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 19:40 — GUIDO (T1 front, coordination, Claude Code, issue #26)
Done: Cruz Alta (RS) published as the site `cruz-alta` in PR `guido/site-cruz-alta`: `data/sites/cruz-alta/input/site.yaml` (IBGE centroid of 4306106, rounded to the POWER echo; only sourced facts), output written by `fieldshift fetch power --site cruz-alta` after a fresh POWER download (`data/cache/power/cruz-alta/`, 3.6 MB): 20 series, 35 provenance records, indices; monthly values identical to `dev-cruz-alta`; no "DEV ONLY" label; ground-check limitations (#31) on the 12 Tmax/rain records. `validate --all`, pytest (248), ruff, lint, typecheck, Vitest (107), build and Playwright (6) pass. `sync-data` now publishes `public/data/sites/cruz-alta/{series,provenance,indices}.json` (HTTP 200 from `next start`). dev-floripa stays DEV; `dev-cruz-alta` kept (IBGE files, drought check, open PR #35 writes there). Also translated the 13:15 entry below to English (preflight B2).
Next: nothing in this PR; merge is a human decision (D-001 is still OPEN).
Blocked by: none.
Needs from others: INCO: the app has no site route yet (build lists only `/`, `/data-methods`, `/glossary`), so Cruz Alta is published as data but not listed or rendered. Pipeline: `index.json`, `manifest.json` and `site.json` have no writer yet (`fieldshift build`/`build-all` in the architecture). SURGEON/agronomist (#8): `field`, `ag_year`, `default_units`, `context` and `indices:` thresholds for `cruz-alta`.
Contract changes: none

## 2026-11-14 13:15 — CONTRACTS chat (coordination, Claude Code)
Done: issue #12 — contracts v1.0.0 in pydantic (`services/science/src/fieldshift/contracts/`), `fieldshift contracts export` → `packages/contracts/schema/contracts.schema.json`, `npm run contracts` → `ts/generated.ts` + `ts/index.ts` (`CONTRACT_MAJOR = 1`), `fieldshift.calendar.agyear` + `fixtures/agyear-cases.json` and `fixtures/units-cases.json` (delta_degC ×1.8 without +32), drift steps in CI.
Next: `apps/web/src/lib/agyear.ts` and `units.ts` to consume the fixtures (INCO); cross-file validator (`fieldshift validate --all`) once there is data.
Blocked by: none.
Needs from others: SURGEON — the architecture's `site.yaml` has `heat_threshold_degC`, which does not exist in the `Site` contract; the YAML input model is left to Story 2.2. INCO — confirm the imperial units in `units-cases.json` (degF, in, ft, ac, mph).
Contract changes: PR guido/contracts-codegen (creates contracts v1.0.0)
