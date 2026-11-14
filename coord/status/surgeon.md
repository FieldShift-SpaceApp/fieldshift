# Status — SURGEON

> Only the SURGEON front edits this file. Newest entry on top. Format: AGENTS.md §4.2

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
