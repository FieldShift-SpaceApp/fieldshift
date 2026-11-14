# Status — EECOM

> Only the EECOM front edits this file. Newest entry on top. Format: AGENTS.md §4.2

## 2026-11-14 14:55 — EECOM (CRUZ-ALTA front, Claude Code, issue #26)
Done: Cruz Alta (RS) prepared as a CANDIDATE only in `data/dev/dev-cruz-alta/` (outside the app sync; nothing in `data/sites/`; PR #30, with `main`/#28 merged in: `validate --all` passes). IBGE JSON (raw + plain provenance) in `data/cache/ibge/dev-cruz-alta/`, because the validator only accepts contract files in `output/`. IBGE code **4306106** confirmed on the localidades API; 2022 municipal mesh (GeoJSON, highest quality) and IBGE centroid (−28.703, −53.5626) with provenance and sha256; NASA POWER daily 1981→2026-10 at the centroid through the CLI (`--site dev-cruz-alta`, 13 parameters, 3.6 MB cache); PAM SIDRA 1612 soybean 1974–2025 via `fieldshift fetch ibge-pam` (module `sources/ibge_pam.py` + tests on a recorded response). Drought figures checked: 2022 = 1,337 kg/ha and 2021 = 3,920 kg/ha confirmed (PAM); "4 of 14 seasons" depends on the criterion (3 to 6 with simple criteria; 4 = 2012, 2020, 2022, 2023 when both a yield drop and low rainfall are required). The 2021/22 event is recorded as a Story 2.5 candidate in the README.
Next: nothing until the team decides (D-001/#8). If Cruz Alta becomes a site: SURGEON's `site.yaml`, then run `fetch power` for it.
Blocked by: D-001 / #8 (human decision).
Needs from others: SURGEON: an "IBGE meshes" row in `RESOURCES.md` and the PAM status (today "candidate"); GUIDO/contracts: official statistics (PAM) have no `DataType` and no units (t, kg/ha) in contracts v1.1.0 (nor does the mesh) — that is why PAM was written as CSV + plain provenance; it only becomes a contract through a `contract` PR.
Contract changes: none

## 2026-11-14 14:35 — EECOM (DADOS-2 front, Claude Code)
Done: #22 in `eecom/indices-validate`: contracts v1.1.0 (MINOR; `VariableKey` + `evap_land_modeled`, `soil_wetness_profile_modeled`, `heat_days`, `frost_days`, `extreme_precip_days`, `extreme_precip_total`, `water_deficit`, `growing_degree_days`; `IndexKey` and optional `index_key` in `Metric`/`MonthlyProfile`; optional `ProvenanceMethod.parameters`). Indices computed on daily data before aggregation (ADR-3), monthly series + 1991–2020 profile per month + annual mean in `indices.json`, `computed` provenance with method, parameters and inputs. POWER now brings `GWETPROF` and `EVLAND`. `fieldshift validate --all` (ADR-8 layer 1) in the CI science job. dev-floripa regenerated (old series identical in value).
Next: run `fetch power` for brasil and nevada when the `site.yaml` exists (#8), with thresholds in the `indices:` block.
Blocked by: coordinates of the real sites (#8, SURGEON).
Needs from others: SURGEON/agronomist: `indices.heat_tmax_c` (and `gdd_base_c` once the crops exist, D9) in `site.yaml`; generic defaults apply today (35 °C, 10 °C), flagged in the provenance. GUIDO/SURGEON: review `content/methods/climate-indices.md` (anchor `climate-indices`), written by this front because the web VL6 test (#24) fails an anchor without a page. `fetch power` now merges provenance.json by id (requested by the ROTAÇÃO front, #25). Architecture: water deficit implemented as ET0 − P (brief of #22); the architecture says "P − ET0"; and the anchor example there is `method-et0-fao56`, the code uses `et0-fao56`.
Contract changes: v1.1.0 (MINOR) in this PR, label `contract`; `packages/contracts/package.json` stays 1.0.0 because the app pins the exact workspace version.

## 2026-11-14 14:10 — EECOM (DADOS front, Claude Code)
Done: NASA POWER layer (#11, Story 2.2): `fieldshift fetch power --site <id>` (or `--lat/--lon`), daily community AG 1981→end of the previous month, raw cache in `data/cache/power/<site>/`, retry/backoff, `--offline`; `series.json` + `provenance.json` (contracts v1.0.0) with full FR19; ADR-3 monthly aggregation (a month only when every day is valid, otherwise null + known_gaps); daily FAO-56 ET0 in pure Python (tested against FAO-56 Examples 8 and 18); heat/frost flags; DEV point `dev-floripa` written to `data/dev/` (outside the app sync). EVPTRNS investigated and discarded (it is transpiration only in MERRA-2; ~0 in the Floripa cell).
Next: run `fetch power` for brasil and nevada as soon as the `site.yaml` exists (#8); `GWETPROF`/`EVLAND` only with a new contract key.
Blocked by: coordinates of the real sites (#8, SURGEON).
Needs from others: GUIDO/SURGEON: a `content/methods/` page with the `et0-fao56` anchor (VL6) and the POWER method (Story 2.2 AC8); GUIDO: monthly heat/frost counts go to `ClimateIndices` (no `VariableKey` for them); per-site heat threshold in `site.yaml` (SURGEON).
Contract changes: none
