# Submission preflight

> **SI-assisted:** checks run and written with Claude Code (Anthropic); human review pending. A person must re-run the checks marked UNVERIFIED and sign the final run (`checklist.md`).

Owner: FLIGHT. Sources: squad submission checklist (team workspace), [`checklist.md`](checklist.md), the official [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) and [Judging & Awards Guide](https://www.spaceappschallenge.org/resources/judging-awards-guide/) (2026-11-13 versions).

**Legend:** PASS = checked, evidence given · FAIL = checked and not compliant today · UNVERIFIED = cannot be checked from the repository (needs a person logged in, or the artifact does not exist yet) · PENDING = depends on `D-001` (still OPEN), not a defect today.

## Runs

| Run | Date/time (BRT) | `main` at | PASS | FAIL | UNVERIFIED | PENDING |
|---|---|---|---|---|---|---|
| 1 | 2026-11-14 14:48 | `f21d8c6` (after #24, #25, #28) | 11 | 14 | 9 | 1 |
| 2 | 2026-11-14 19:41 | `741ea61` (after #30–#36), plus the fixes of PR `flight/preflight-fixes` | 15 | 6 | 9 | 5 |
| 3 | 2026-11-14 22:29 | `06dcc73` (after #37–#47), plus the page text of PR `flight/submission-text` | 15 | 7 | 9 | 4 |
| 4 | 2026-11-14 23:18 | `3ede21d` (after #49), plus PR `surgeon/licence-checks`; **only R7 and R8 re-checked**, every other row carried from run 3 | 17 | 5 | 9 | 4 |
| 5 | 2026-11-15 10:21 | `cb024bc` (after #54, #58–#61), plus PR `flight/text-coherence`; **re-checked B1, B4, B8, D2, D4, R6, R11**, every other row carried from run 4 | 17 | 5 | 9 | 4 |
| 6 | 2026-11-15 13:05 | `e3a6d88` (after #62–#67), plus PR `flight/text-coherence-r5`; **re-checked B1, B7, C1–C6, D1, R4** with the demo file; every other row carried from run 5 | 23 | 2 | 7 | 3 |

**What changed in run 6** (COERÊNCIA front, jury round 5; partial run). The demo exists: `demo-28s.mp4` in the team's demo folder (not in the repo). `ffprobe -show_entries format=duration` → **28.200000 s**; one video stream 1920×1080, **no audio stream**; metadata comment: "Screen recording of the published FieldShift app (no synthetic voice, no AI-generated images). Captions and assembly scripted with Claude Code (Anthropic), reviewed by the team." A 1-frame-per-second contact sheet (28 frames, `ffmpeg -vf fps=1,tile=4x8`) was viewed in full.
- **C1 PENDING → PASS:** format = video ≤ 30 s (the file exists). D-001's "Demo format" field is still empty; that stays under R1.
- **C2 UNVERIFIED → PASS:** 28.2 s ≤ 30 s (`ffprobe`, above).
- **C3 UNVERIFIED → PASS:** burned-in English captions in every sampled frame (e.g. "Every winter, Brazilian farmers choose: wheat or a cover crop.", "Free. Open NASA data. fieldshift-spaceapp.vercel.app").
- **C5 FAIL → PASS:** no voice and no audio track, no AI-generated image; captions and assembly are SI-assisted and declared in the file metadata, in page field 6 (variant "captions only" chosen) and in a new `SI-USAGE.md` row.
- **R4 FAIL → PASS:** the audio item no longer applies (no audio track); code and data acknowledged as before.
- **B7 FAIL → PASS:** field 6 has the demo declaration (no `[CHOOSE]` left) and `SI-USAGE.md` has a demo row. Reviewer names stay `pending` (R2).
- **C4 and C6 stay UNVERIFIED:** the 28 sampled frames show no person and no NASA logo, flag or insignia (app screens, maps and captions only), but a person must still watch the whole video once at full speed.
- **D1 still FAIL:** the video is not uploaded yet; field 3 says `[DEMO LINK]`.
- **B1 still FAIL:** open items are field 1 and the one-line statement (D-001), `[DEMO LINK]`, the app source `[PENDING]`, member names and reviewer names.
- Page text (no status change): the "no R$/ha is given" line is replaced by "≈ R$ 49–98/ha a year, estimate using the RS average soybean premium R$ 488/ha (PSR 2024)"; the 98% is written as conditional; `/policy`, `/calibrate`, `analysis/policy-targeting`, `analysis/field-calibration`, `analysis/team-rotation-evidence` and the Prithvi null result (field 7 item 9) are added; the old NEX-GDDP-CMIP6 note is removed (the number is no longer in the app). The pipeline app's `/data-methods` has no "Pending" section left (Validation, Scale, How we differ) and no "(working title)"; `npm run lint`, `typecheck`, `test` (121 tests), `build` and `e2e` (11 tests) pass locally.

**What changed in run 5** (COERÊNCIA front; partial run, rows listed in the table). Counts unchanged; evidence updated:
- **D4 PASS (re-checked):** the links changed by the team lead's decision. Anonymous `curl -L -A Mozilla/5.0` at 10:21 BRT: farmer-facing app https://fieldshift-spaceapp.vercel.app `/`, `/start`, `/soil-level`, `/rotations`, `/my-farm`, `/globe`, `/sources`, `/about` → 200; pipeline pages https://fieldshift-data.vercel.app `/data-methods`, `/sites/cruz-alta`, `/glossary` → 200. Page field 4 and `README.md` now list both.
- **D2 PASS (re-checked):** repo URL → 200; `gh repo view` → `PUBLIC apache-2.0`.
- **B4 PASS (re-checked):** field 7 now lists NASA POWER, GPM IMERG, Landsat C2 L2, HLS v2.0, MODIS VI, GEOS-S2S, **NASADEM** (read by `analysis/residue-landsat` and `analysis/farm-reports`: `results/nasadem_slope_classes.json`, 87.4% of cropland ≥ 3%) and **NASA GIBS** (Blue Marble and HLS tiles on the app's `/globe`, seen in the live app's HTML and script: `gibs.earthdata.nasa.gov/wmts/epsg3857/best`). DOIs of NASADEM, HLSL30, HLSS30, the GIBS page and the GIBS WMTS capabilities → 200. NEX-GDDP-CMIP6 is **not** listed (see drift below).
- **B8 PASS (re-checked):** field 8 adds CAR/SICAR, the MAPA news on Paraná's first pilot season (the anonymous `curl` with a browser user agent → 200 at `/noticias/2025/…`; it shows "Vinte e nove áreas de produção" and "57% no nível 2"), Census 2006/2017 no-till tables, rasterio/pystac-client/planetary-computer, the new charts and the NASADEM citation; every `[IF MERGED #54]` passage is resolved (PR #54 merged in `7b7ca4f`).
- **R6 PASS (re-checked):** the live farmer-facing app shows NASA data on screen: `/globe` credits "NASA GIBS / Blue Marble · NASA HLS · NASA/USGS Landsat · NASADEM" (anonymous `curl`).
- **R11 PASS (re-checked):** local gitleaks 8.30.1 on this branch before push (see the PR body).
- **B1 still FAIL:** besides D-001, demo, member names and the field 6 variant, field 4 now carries `[PENDING: public URL of the farmer-facing app's source code]`.

**What changed in run 4** (SURGEON, PROVA-PÚBLICA front; partial run: only the licence rows).
- **R7 FAIL → PASS** and **R8 FAIL → PASS**: every "check" licence that the code or the repo uses was confirmed on the provider's page and its `RESOURCES.md` row now gives the URL, a quote and the date (2026-11-14). Nothing had to be removed: the only raw third-party file in question (ANA gauge 2853015) is covered by ANA's reproduction-with-citation terms.
- Not re-checked in this run (status carried from run 3): all other rows. The scale-numbers drift item is addressed by PR #51 (open) and the satellite-vs-ground proof by PR #50 (open); both are not on `main` yet.

**What changed in run 3.**
- Fixed on `main` since run 2 → PASS: **R6** (the live `/sites/cruz-alta` page shows NASA POWER values, PR #39).
- New FAIL, found in this run: **R7** (ANA rain-gauge data committed while `RESOURCES.md` says its licence is "check") and **R8** (rows with "check" licences are now read by pipeline and analysis code: ANA, NMME, CONAB; Atlas fetched at run time).
- Updated by this PR, still PASS: B4 (field 7 now lists the four NASA datasets the public code reads, with links and citations), B5 (field 8 now lists ESA Sentinel-2 and WorldCover as partner data; "Partner data: none" removed), B8 (analysis libraries, literature and data sources added to field 8).
- Unchanged PENDING: B3, C1, D3, R1 (D-001). Fields 2 and 5 are now written; only the name and the one-line statement remain `[PENDING D-001]`, plus `[IF PUBLISHED]` passages for the agronomist's app.
- This PR also aligns `SI-USAGE.md` line 7 ("Not used for: generating the solution concept…") with page field 6 and `analysis/storms-bare-soil/README.md`: AI helped compare and synthesize concepts from the team's ideas at the team lead's request; the team chooses and writes the name and one-line statement.

## A. Eligibility

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| A1 | All members (≤ 6) on the Members tab, confirmed at the same Local Event, none on the waitlist | UNVERIFIED | not visible from the repo | log in, open the Members tab, paste the 6 names in `page-draft.md` | FLIGHT |
| A2 | Official challenge selected: "Field Shift: Adapting Farms with NASA Data" | UNVERIFIED | not visible from the repo | check on the project page | FLIGHT |

## B. Project page

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| B1 | All required fields filled | FAIL | run 6: still open: field 1 and the one-line statement (D-001), `[DEMO LINK]`, app source `[PENDING]`, member names (A1), reviewer names (field 6) | fill D-001, demo URL and names; resolve `[CHOOSE]` and `[IF PUBLISHED]` | team (D-001) + FLIGHT + CAPCOM |
| B2 | English on the page **and in linked materials** | PASS | Run 3 scan of the 78 text files changed since `741ea61` (`git diff --name-only 741ea61 origin/main`, minus `data/cache`, JSON, CSV) with a Portuguese word list: remaining hits are proper names (municipalities such as Não-Me-Toque, Ijuí; Florianópolis), titles of cited Brazilian publications, official source labels kept as data (SICOR product labels `TRIGO`/`AVEIA`, ANA field `ChuvaNN`), file names in the private workspace and team front code names. Run 2 evidence for the rest of the repo still holds | demo captions: see C3 | CAPCOM (demo) |
| B3 | One-line statement at the top of the description | PENDING | D-001 "One-line differentiator" is empty; fields 2 and 5 start with `[PENDING D-001: one-line statement]` and the text below works with any statement | the team writes it in its own words in D-001 | team |
| B4 | "NASA Data" section lists each NASA dataset with link | PASS | Run 5: NASADEM and NASA GIBS added, Landsat C2 and HLS unbracketed (see "What changed in run 5"). Run 3: `page-draft.md` field 7: NASA POWER (Daily API v2.10.3, variables, upstream MERRA-2/CERES, period, both referencing-guide sentences with access date 2026/11/14), GPM IMERG via POWER (period 1998–2025, 2026 stop at 2026-09-14, Huffman et al. 2023 V07 DOI), MODIS MOD13Q1/MYD13Q1 v061 (Didan 2021 DOIs), NASA GMAO GEOS-S2S via NMME/IRI (metrics only, Molod et al. 2020, Kirtman et al. 2014). Access times from `data/sites/cruz-alta/output/provenance.json`. Citations checked on the source pages on 2026-11-14 (POWER referencing guide; Earthdata catalog pages of IMERG V07 and MOD13Q1; DOI content negotiation for Molod 2020 and Kirtman 2014). Anonymous `curl -L`: POWER, POWER methodology, NMME folder, LP DAAC MOD13Q1/MYD13Q1 pages, `gpm.nasa.gov/data/imerg`, the three Earthdata DOIs → 200; `doi.org/10.1029/2019JD031767` → 403 to `curl` (Wiley blocks scripted clients; the DOI resolves) | open the Wiley DOI once in a browser | FLIGHT |
| B5 | Partner / other data section | PASS | field 8: partner data = Copernicus Sentinel-2 L2A and ESA WorldCover 2021, with the credit lines of their licences (same text as `provenance.json` attribution `group: partner`); other data: NOAA CPC, NMME, IRI, IBGE, BCB (SICOR under ODbL, Proagro), ANA, INMET, CHIRPS, MAPA ZARC, CONAB, Embrapa, Emater/RS-Ascar, Atlas Digital, access services. Copernicus DEM is not used anywhere (repo grep), so it is not listed | — | — |
| B6 | Limitations and "supports, not replaces, farmer judgment" | PASS | field 5 "Limitations and uncertainty" and "Use statement"; anonymous `curl -L` of the live `/sites/cruz-alta` page shows "This tool supports, and does not replace, the judgment of farmers and agronomists" and the ground-check limitations | — | GUIDO + SURGEON |
| B7 | SI declaration complete (field 6) | PASS | run 6: field 6 declares the demo (captions only, no voice, captions/assembly SI-assisted); `SI-USAGE.md` demo row added; reviewer names `pending` (R2) | the member who made the video adds a row to `SI-USAGE.md`; FLIGHT picks the variant and fills the tool names | member who made the video + CAPCOM |
| B8 | References field lists every external code, text and image | PASS | Direct dependencies of `apps/web`, `packages/contracts` and `services/science/pyproject.toml` unchanged since run 2 (re-read); analysis imports (`grep import` over `analysis/` and `services/science/scripts`) add NumPy, Matplotlib, xarray, netCDF4 → now in field 8 (already in `RESOURCES.md`). Data sources of every public data file and analysis, literature (FAO-56, Zhang, McMaster, Hyndman, Wilks, Tucker, Campos, Aita & Giacomini, Santos/Embrapa, Funk, Molod, Kirtman, Huffman, Didan) and images (icon, storms chart, app screenshots) listed. Agronomist-app extras (Leaflet, OpenStreetMap tiles, SoilGrids, MapBiomas, SRTM via Open Topo Data, Google Earth Engine) listed as `[IF PUBLISHED]` | re-run when demo or slide assets are added, and when the agronomist app is published | FLIGHT |

## C. Demo

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| C1 | Format chosen (video ≤ 30 s **or** ≤ 7 slides) | PASS | run 6: video `demo-28s.mp4`, 28.2 s (`ffprobe`); D-001 "Demo format" still empty (R1) | decide in D-001 | team + CAPCOM |
| C2 | Within the limit | PASS | run 6: `ffprobe -v error -show_entries format=duration` → 28.200000 s | `ffprobe` duration ≤ 30.0 s or slide count ≤ 7, pasted here (`demo-plan.md` §5) | CAPCOM |
| C3 | English captions (if spoken in another language) | PASS | run 6: English captions burned in every frame of a 1-fps contact sheet (28 frames) | burn in English captions | CAPCOM |
| C4 | No person under 18 (image, voice, likeness) | UNVERIFIED | run 6: no person in the 28 frames sampled at 1 fps (screen recording of the app); full-speed watch pending | frame-by-frame check | CAPCOM + FLIGHT |
| C5 | SI images/video watermarked; SI voice declared; illustrative cards labeled | PASS | run 6: no audio stream (`ffprobe`), no AI image; captions/assembly SI-assisted, declared in the mp4 `comment`, field 6 and `SI-USAGE.md` | apply `demo-plan.md` §2, or use variant B (captions only, no synthetic voice) | member who made the video + CAPCOM |
| C6 | No NASA logo, flag or insignia in the demo | UNVERIFIED | run 6: no NASA logo, flag or insignia in the 28 frames sampled at 1 fps; full-speed watch pending | check every frame and slide | CAPCOM |

## D. Links

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| D1 | Demo link opens without login | FAIL | run 6: video exists, link not published (field 3 `[DEMO LINK]`) | host as YouTube Unlisted/Public or Drive "Anyone with the link"; test in a private window | CAPCOM |
| D2 | Repository public | PASS | run 3, anonymous `curl -s -o /dev/null -w '%{http_code}' -L` → 200 for the repo, `SI-USAGE.md`, `RESOURCES.md`, `LICENSE`, `content/related-work.md`, `analysis/enso-wheat`, `analysis/storms-bare-soil`, `data/sites/cruz-alta/output`; `gh repo view` → `"visibility":"PUBLIC"` | — | — |
| D3 | README in English: how to run, datasets, credits, description, demo, live link | PENDING | English, "Run locally", live link, "NASA data and credits" present. Missing the project description and the demo link (D-001). The README credits only NASA POWER; IMERG, MODIS, GEOS-S2S and Sentinel-2 are credited in `RESOURCES.md` and the page, not in the README | after D-001: add the summary, the demo link and the other NASA/partner credits to `README.md` | FLIGHT |
| D4 | App public and working | PASS | run 5, anonymous `curl -L` at 10:21 BRT: farmer-facing app `fieldshift-spaceapp.vercel.app` (8 routes) and pipeline pages `fieldshift-data.vercel.app` (`/data-methods`, `/sites/cruz-alta`, `/glossary`) → 200, no login. Repo `homepageUrl` still empty | optional: `gh repo edit FieldShift-SpaceApp/fieldshift --homepage https://fieldshift-spaceapp.vercel.app` (visible repo setting, Otávio) | Otávio (FLIGHT) |
| D5 | No "Restricted" Google Drive link | UNVERIFIED | no Drive link exists yet | check each link before submit | FLIGHT |

## R. Repository compliance (`checklist.md` items 1–9 and extras)

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| R1 | C1: D-001 FINAL | PENDING | `DECISIONS.md` D-001 "Status: OPEN", every field empty | the team decides and writes every field in its own words, with names and time | team |
| R2 | C2: SI row for every AI-assisted PR | PASS | rows for every merged PR #37–#47 (`flight/preflight-fixes`, `eecom/complements-contract`, `inco/site-page-cruz-alta`, #40 field 6 row, `surgeon/analysis-enso-wheat`, `eecom/complements-data`, `globals.css` #43, `.gitleaksignore` #44, `eecom/now-2026-contract`, `eecom/now-2026`, `surgeon/storms-bare-soil`); this PR adds one row. "Reviewed by" is `pending` in most rows | reviewers replace `pending` with their names | each front |
| R3 | SI images/videos watermarked | UNVERIFIED | two SI-related images in git, neither with an "AI-generated" watermark: `apps/web/src/app/icon.svg` (SVG code written by Claude Code, declared in `SI-USAGE.md`) and, new, `analysis/storms-bare-soil/results/storms-bare-soil.png` (chart drawn by a Matplotlib script written by Claude Code from computed results; opened in this run: data chart with a source footer, no logo; declared in `SI-USAGE.md` as "image (chart)"). Whether the watermark rule applies to code-drawn icons and data charts is a human call. App screenshots in `apps/web/docs/screenshots/` are captures of the app, not SI-generated images | FLIGHT decides: accept with the declarations, or add a small "Chart generated by AI-written code" note to the PNG footer and redraw/edit the icon; demo: see C5 | FLIGHT; CAPCOM (demo) |
| R4 | SI audio, code and data acknowledged | PASS | run 6: no audio track in the demo; code and data acknowledged (file headers, `SI-USAGE.md`, `provenance.json`) | see B7 and C5 | member who made the video + CAPCOM |
| R5 | C3: no NASA logo, flag or insignia in the repo or app | PASS | run 3: `git ls-files '*.png' '*.jpg' '*.jpeg' '*.svg' '*.gif' '*.webp' '*.ico' '*.mp4' '*.mp3' '*.wav' '*.pdf'` → `icon.svg`, `storms-bare-soil.png`, `site-cruz-alta.png`, `site-cruz-alta-360.png`; all opened (storms chart and 360 px screenshot viewed in full): no logo, flag or insignia; `git grep -l 'data:image'` in `apps/ content/ docs/ analysis/` → only rule text in this file; `meatball`/`insignia` hits are rule text only | re-run on the final commit (demo, slides) | FLIGHT |
| R6 | C4: NASA dataset listed and shown in the app | PASS | `RESOURCES.md`: NASA POWER `selected`. Live `/sites/cruz-alta` (anonymous `curl -L`, visible text): "Data source NASA POWER · POWER Daily API (point), community AG; upstream MERRA-2 · v2.10.3 · NASA Langley Research Center (LaRC) · Modeled · Downloaded on 2026-11-14", monthly values Nov 2024–Oct 2026 and 1991–2020 indices, each opening its source. IMERG, MODIS and GEOS-S2S appear on `/data-methods` as methods and results, not as live data on a page | `[IF PUBLISHED]` app would add them on screen | INCO |
| R7 | Licences of data used and committed | PASS | run 4: `git ls-files data analysis` third-party data: NASA files (open), NOAA ONI (public domain), IBGE (cite source), Sentinel-2 scene list and MODIS table (open with attribution), BCB SICOR (ODbL, `license_id: odc-odbl` from the BCB CKAN API `package_show?id=matrizdadoscreditorural`, read 2026-11-14), NMME GEOS member and skill metrics (NOAA CPC files, NWS public domain), `replay-2023.yaml` (transcribed values; CONAB: two derived values only). `data/sites/cruz-alta/input/ana-2853015-sep-nov-daily.csv`: ANA's SNIRH metadata record "Rede Hidrometeorológica Nacional" states "É permitida a reprodução de dados e de informações, desde que citada a fonte" (`metadados.snirh.gov.br/geonetwork/srv/api/records/f85dbf06-a869-414c-afc5-bb01869e9156`, fetched 2026-11-14), plus Decree 8.777/2016 art. 4 (ANA is a federal agency); `RESOURCES.md` ANA row → "yes, cite source". No file removed, so no pipeline output changed | — | — |
| R8 | "check" licences in `RESOURCES.md` | PASS | run 4: rows whose "In git?" is still `check` (ISRIC SoilGrids, FAOSTAT, FAO WaPOR, USDA CDL, SSURGO, USGS) all have Feeds "—": no code, data file or analysis reads them (FAOSTAT gets its licence in PR #51, which adds a reader). Rows read by code, now with URL, quote and date: ANA (yes, cite source: SNIRH record), INMET (no raw files; site says data are disseminated free of charge, `portal.inmet.gov.br/sobre`; Decree 8.777 art. 4), CONAB (CONAB states it is outside Decree 8.777, `gov.br/conab/pt-br/acesso-a-informacao/dados-abertos`; site CC BY-ND 3.0 → no raw sheet, two derived values with attribution), NMME (NWS disclaimer "in the public domain, unless specifically noted otherwise", `weather.gov/disclaimer`; citation and acknowledgement from `cpc.ncep.noaa.gov/products/NMME/about.html`), Atlas (no terms on the download page or in a web search → not committed, counts quoted). Decree 8.777/2016 art. 2 III and art. 4 quoted from `planalto.gov.br` | if CONAB objects to derived figures under ND, drop the two margins from `replay-2023.yaml` (EECOM) | SURGEON |
| R9 | Project licence (OSI) | PASS | `LICENSE` Apache-2.0; `gh repo view` → `licenseInfo.key: apache-2.0` | — | — |
| R10 | Public production URL returns 200 | PASS | see D4 | — | — |
| R11 | Secrets: CI `hygiene` green on the submitted commit | PASS | `gh run list --branch main` → `ci` `success` on `06dcc73` (#47, 2026-11-15 01:07 UTC); local `bash scripts/check-public-repo.sh` → "NFR9 ok: no forbidden paths"; local gitleaks v8.30.1 on this branch before push (see PR) | re-check on the final submitted commit | FLIGHT |
| R11b | `.gitleaksignore` entries are reviewed false positives only | PASS | 9 entries: 2 from run 1 (#28, #29) and 7 from #43 (commit `3eb3b34`, metric ids named `"key"`), each group with a note; SI row and human-review note in `SI-USAGE.md`; no new entry in this PR | any new entry needs the same note and a reviewer | FLIGHT |
| R12 | Page in English, limitations, SI field drafted | PASS | `page-draft.md` | fill the placeholders | FLIGHT |
| R13 | Submit before the deadline, confirmation captured | UNVERIFIED | Sunday action | Submit for Judging by 20:00 BRT; screenshot of the confirmation banner in `coord/status/flight.md`; re-submit if improved before 23:59 (only the last save counts) | FLIGHT |

## Left for people (no AI can close these)

- **D-001** (team): name and one-line statement (B3, R1, D3), demo format (C1), then B1.
- **Demo** (member who made the video + CAPCOM): upload and paste the link (D1); watch it once at full speed for C4 and C6; human review of the captions.
- **Logged-in checks** (FLIGHT): A1, A2, D5, R13.
- **Farmer-facing app**: published at https://fieldshift-spaceapp.vercel.app (team lead, 15 November); its **source code is still private** — publish it and fill the `[PENDING]` in field 4.
- **Decisions**: R3 (icon and chart without watermark); merge of this PR.

## Drift found

- Run 1: `AGENTS.md` §6 vs the official English rule — fixed in run 2.
- Run 2: IBGE localities/mesh data without a `RESOURCES.md` row — fixed in run 2.
- Run 2: the GitHub repo "homepage" field is empty although the app is live (D4, optional) — still open.
- Run 3: `SI-USAGE.md` line 7 said AI was "not used for generating the solution concept", against page field 6 and `analysis/storms-bare-soil/README.md` — aligned in this PR.
- Run 3, **not fixed (protocol files, team's call):** `AGENTS.md` §1 rule C1 ("No AI ideation of the solution. Do not propose the product concept…") and `DECISIONS.md` D-001 ("Until then, nothing concept-specific is built") no longer describe what happened (complements and "Storms meet Soil" were synthesized with AI at the team lead's request and built before D-001). FLIGHT decides whether to amend them.
- Run 3: the POWER credit sentence in the complements' `provenance.json` attribution ("These data were obtained from the NASA Langley Research Center (LaRC) POWER Project funded through the NASA Earth Science/Applied Science Program.") is older wording; the current referencing guide sentence (used in the README, `RESOURCES.md` and field 7) ends "…funded through the NASA Earth Science Division." EECOM to align in the pipeline.
- Run 3: the GEOS-S2S URL in `RESOURCES.md` (`https://gmao.gsfc.nasa.gov/cc/research/subseasonal/`) now serves a login form (anonymous `curl`: "GMAO CMS", password and Launchpad fields); not used on the page. EECOM to replace it (e.g. the NMME folder or the Molod et al. 2020 DOI).
- Run 3: the scale numbers in field 2 (RS wheat 5.3 → 2.6 Mt, Proagro R$ 2.07 bn, 1.16 Mha, 46%, ~20,000 farms) and the ~10% of world wheat area in field 5 were verified by the team in the private workspace; no public script reproduces them yet.

- Run 5: the farmer-facing app is the linked product, but its source code is private (field 4 `[PENDING]`). Team lead's call.
- Run 5: the live app's `/sources` says the rule "names" its satellite data ("the satellite data it names (NASADEM; Landsat, Sentinel-2 or HLS)"); the faithful wording is "recommends Landsat, Sentinel-2 or HLS" (IN 2/2025 item 6.4) and "such as NASADEM or equivalent" (item 6.3). The public repo now uses the faithful wording everywhere (`analysis/farm-reports/README.md`, `content/methods/farm-reports.md` fixed in this run). Fix in the app's private repository.
- Run 5: the live app shows three numbers from the team's internal research (NEX-GDDP-CMIP6 hot days, heavy rain on soil without a living plant, system revenue). Their public reproduction is handled in a separate PR (`analysis/team-rotation-evidence/`); a number that does not reproduce there must not be cited on the page.

- Run 6: the demo's metadata says the captions were "reviewed by the team", while its script file says "human review pending". The person who reviews the captions should confirm one of the two.

## Non-blocking suggestions

- Request a FortiGuard Web Filter category for the production domain (the guide recommends it; not required).
