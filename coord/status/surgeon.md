# Status — SURGEON

> Only the SURGEON front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-15 13:45 — SURGEON (ChatGPT, OpenAI)
Done: drafted a source-priority and adoption-gate note in PR `surgeon/data-integration-priorities`; documentation only, no new ingestion or app behavior. It prioritizes local field/soil/rotation inputs, INMET/ANA ground validation with POWER and IMERG, careful NOAA ENSO context, then SMAP, HLS/Landsat/Sentinel-2, and SRTM; it also flags the IMERG inventory wording mismatch.
Next: EECOM review the data pipeline steps; FLIGHT review the AI-use log entry. Adopt sources only after the human concept/site inputs and consumer approvals are in place.
Blocked by: none.
Needs from others: EECOM: review data source priorities and validation gates; FLIGHT: review the appended SI-USAGE.md entry.
Contract changes: none

## 2026-11-15 14:00 — SURGEON (ChatGPT, OpenAI)
Done: expanded PR #71 with a layered evidence stack for local weather, climate outlook, vegetation, thermal surface response, soil water, terrain/soil, and rotation/farmer feedback. Added the climatology/oceanography contribution and corrected thermal terminology: ECOSTRESS/Landsat report land-surface temperature, not direct leaf temperature; pixel scale, acquisition gaps, and product quality must remain visible.
Next: EECOM review the data pipeline steps; FLIGHT review the AI-use log entry. Adopt sources only after human site inputs and consumer approvals are in place.
Blocked by: none.
Needs from others: EECOM: review data-source priorities and validation gates; FLIGHT: review SI-USAGE.md.
Contract changes: none

## 2026-11-15 01:10 — coordination (Claude Code), DESCOBERTA front
Done: pre-registered test of "soybean became less sensitive to summer drought after winter cover became the rule" (PR `surgeon/drought-resilience`): `analysis/drought-resilience/` (one command, IBGE PAM 1612 × NASA POWER Dec–Feb rain, 18 municipalities, 1982–2025; bootstrap and permutation by year; 17 robustness variants incl. ANA gauge) and `content/methods/drought-resilience.md`. Result: **not supported** (slope +21.5% → +17.1% of trend per SD of rain, Δ −4.5 points, 95% CI −24.3 to +19.2, p = 0.61; sign flips at cut 1997/1998; +25.1% since 2005). What holds: summer drought still costs 25–70% of trend yield in the driest summers.
Next: human review; CAPCOM/FLIGHT must not use "40 years prove soil care protects income" in the pitch (see README "What can and cannot be said").
Blocked by: nothing.
Needs from others: none.
Contract changes: none

## 2026-11-14 23:30 — coordination (Claude Code), PROVA-PÚBLICA front
Done: three PRs so the judges can check the pitch from the public repo. #50 `analysis/ground-truth-proagro/` (Proagro excess-rain wheat claims × GPM IMERG Sep–Nov rain, 2013–2025: pre-registered heavy-rain days ρ = 0.41, p = 0.085; Sep–Nov total ρ = 0.69, p = 0.006, 0.61 without 2023, Bonferroni 0.031/0.050; identical to the HQ). #51 `analysis/scale/` (1.16 Mha, 46%, 19,716 farms, 5.30 → 2.59 Mt, R$ 2.07 bn, 10.3% world area: all match; field 5 wording "Rio Grande do Sul" vs the Brazil-wide FAOSTAT computation flagged). This PR: licences of ANA, INMET, CONAB, NMME, Atlas confirmed on the provider pages; preflight run 4 (R7, R8 → PASS); nothing removed.
Next: human review; FLIGHT decides the field 5 wording and whether to list FAOSTAT in field 8.
Blocked by: nothing.
Needs from others: FLIGHT: merge order of #50/#51/this PR does not matter (different rows). EECOM: if CONAB objects to derived figures (CC BY-ND), drop the two margins from `replay-2023.yaml`.
Contract changes: none

## 2026-11-14 20:50 — coordination (Claude Code), REPRODUTIBILIDADE front
Done: the statistical validation behind the ENSO × wheat numbers is now public and reproducible (PR `surgeon/analysis-enso-wheat`): `analysis/enso-wheat/` (scripts ported from the HQ's independent verification, one command `reproduce.py`, small results with access times, README with limitations), method page `content/methods/enso-wheat.md` (listed on /data-methods with no code change), `RESOURCES.md` rows marked "used in `analysis/enso-wheat/`". Rerun on 2026-11-14 reproduced the HQ numbers exactly (53.3% vs 3.5%, p = 0.003, 14/18 in 2023).
Next: human review of the README wording; the station-vs-satellite scripts (method `satellite-vs-ground-check`) are still only in the HQ.
Blocked by: Atlas licence not declared (derived counts kept out of git).
Needs from others: CAPCOM: pitch can now link `analysis/enso-wheat/README.md` instead of the private repo.
Contract changes: none

## 2026-11-14 19:10 — coordination (Claude Code), CONTEÚDO-2 front, issue #31
Done: Validity criterion, concept-agnostic (PR `surgeon/methods-validation`). New page `content/methods/satellite-vs-ground.md` (anchor `satellite-vs-ground-check`; the anchor `satellite-vs-ground` is already a section id of /data-methods): POWER, IMERG and CHIRPS × INMET A853 and ANA 2853015, numbers only from the HQ's `estacao-vs-satelite.md`/`verificacao-dados.md`. New limitations in `nasa-power.md` and `climate-indices.md`. In the pipeline, `fieldshift.provenance.ground_check`: POWER Tmax deviation since ~2019 in the records of `T2M_MAX`, `heat_days` and climatology; rain on too many days / short dry spells / smoothed extremes in those of `PRECTOTCORR`, `extreme_precip_*` and P95; test `test_ground_check.py`; DEV outputs regenerated offline (only the limitation text changes). `RESOURCES.md`: IMERG (via POWER), MODIS v061 via Planetary Computer, GEOS-S2S, CHIRPS v3/ClimateSERV, ZARC, IBGE PAM, INMET, ANA, CONAB costs, CPC ONI, NMME, IRI, SICOR (ODbL), Atlas (license not declared), with "analysis only (fieldshift-hq), not yet in the app". Glossary: `reanalysis-bias`, `dry-spell`, `enso`, `oni`, `probabilistic-forecast`, `hindcast` (pending the agronomist).
Next: agronomist review of the 6 new terms; when a concept adopts IMERG or a station, change the status in `RESOURCES.md` in the same PR as the code.
Blocked by: nothing.
Needs from others: EECOM/GUIDO: review the change in `services/science/src/fieldshift/provenance/` (their folder; requested by the coordination in #31). INCO: the new page enters the methods list without a code change; if they want, link the "Satellite vs. ground" section of /data-methods to the anchor `#satellite-vs-ground-check`.
Contract changes: none

## 2026-11-14 14:25 — coordination (Claude Code), CONTEÚDO front, issue #18
Done: Stories 1.3 and 1.4, concept-agnostic part (PR `surgeon/related-work-methods`). ◐ items checked at the source: WCCC covers Nevada (13 states, UC ANR); SARE MCCP 3rd ed. confirmed; CropRota, APSIM, DSSAT, RUSLE2 confirmed (APSIM is not open source; DSSAT BSD-3). Corrected: ROTAT is *Eur. J. Agron.* 2003; Embrapa is Comunicado Técnico 181 (2018); OpenET covers 48 states since 2025-12-15 and has conflicting terms (non-commercial ToS × CC BY in the GEE catalog); OpTIS is CTIC + Regrow + TNC; Cornell's Water Deficit Calculator is no longer on the list. `content/related-work.md` (11 categories, "how we differ" = Pending D-001), `content/methods/` (`nasa-power`, `et0-fao56` requested by the DADOS front, `monthly-harmonization`, `units-calendar`, `provenance`; `EVPTRNS` limitation recorded), `content/glossary.yaml` (14 terms), terms of use in `RESOURCES.md` (selectors, OpenET, SATVeg), `/data-methods` and `/glossary` pages with tests.
Next: glossary review by the agronomist (replace `reviewed_by: pending`); "Scale of the problem" needs provenance records for the FR17 numbers; Validation waits for Story 2.5.
Blocked by: Story 1.3 AC1 (WCCC at the Nevada coordinate) depends on Q2; AC2 (the NVS-knot demo) was not seen: the project tab requires login and no public repo/video was found.
Needs from others: FLIGHT/CAPCOM: the 5-line summary for "how we differ" is in the PR body (the sentence is the team's, C1). INCO: review the `data-prov-exempt="ui"` exemptions in the documentation blocks.
Contract changes: none

## 2026-11-15 14:40 — SURGEON (ChatGPT, OpenAI)
Done: recorded the teammate-reported ECOSTRESS/Landsat surface-temperature and vegetation work in PR #71, while separating it from the current public inventory's app-feed status. Listed the product/version, scene, method, quality, validation, provenance, and app-path details needed to reconcile the inventory.
Next: EECOM review the source metadata and pipeline steps; FLIGHT review the AI-use log. Keep reported analysis use distinct from verified app integration.
Blocked by: none.
Needs from others: EECOM: confirm product/version and data path for the reported thermal work; FLIGHT: review SI-USAGE.md.
Contract changes: none

## 2026-11-15 14:43 — SURGEON (ChatGPT, OpenAI)
Done: added `docs/jerome-team-synthesis.md` to PR #71 as a shareable English synthesis for the team, with the project vision, layered data plan, rotation comparison, uncertainty, feedback, Jerome's climatology contribution, repo status, and open meeting decisions.
Next: EECOM review source facts; FLIGHT review AI-use record; team confirms name, sites, rotations, and app integration status.
Blocked by: none.
Needs from others: team review of the open items listed in the synthesis.
Contract changes: none

## 2026-11-15 14:50 — SURGEON (ChatGPT, OpenAI)
Done: added `docs/climate-evidence-table-cruz-alta.md` to PR #71 with rainfall, temperature, radiation, dry-spell/extreme-rain, ENSO and seasonal-outlook evidence; includes period, scale, uncertainty, allowed interpretation, local validation results, and the 1995–2025 limits.
Next: team reviews the source audit; repeat for the other six intended regions after boundaries/stations are confirmed.
Blocked by: none.
Needs from others: EECOM: confirm data-path/product versions; team: confirm seven region boundaries.
Contract changes: none
