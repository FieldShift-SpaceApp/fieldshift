# Submission preflight

> **SI-assisted:** checks run and written with Claude Code (Anthropic); human review pending. A person must re-run the checks marked UNVERIFIED and sign the final run (`checklist.md`).

Owner: FLIGHT. Sources: squad submission checklist (team workspace), [`checklist.md`](checklist.md), the official [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) and [Judging & Awards Guide](https://www.spaceappschallenge.org/resources/judging-awards-guide/) (2026-11-13 versions).

**Legend:** PASS = checked, evidence given · FAIL = checked and not compliant today · UNVERIFIED = cannot be checked from the repository (needs a person logged in, or the artifact does not exist yet) · PENDING = depends on `D-001` (still OPEN), not a defect today.

## Runs

| Run | Date/time (BRT) | `main` at | PASS | FAIL | UNVERIFIED | PENDING |
|---|---|---|---|---|---|---|
| 1 | 2026-11-14 14:48 | `f21d8c6` (after #24, #25, #28) | 11 | 14 | 9 | 1 |
| 2 | 2026-11-14 19:41 | `741ea61` (after #30–#36), plus the fixes of PR `flight/preflight-fixes` | 15 | 6 | 9 | 5 |

**What changed in run 2.**
- Fixed by PR `flight/preflight-fixes` → PASS: B2 (English in the repo, with the `AGENTS.md` §6 protocol change), B8 (missing `RESOURCES.md` rows; default favicon replaced).
- Fixed on `main` since run 1 → PASS: D4 and R10 (the app is live, README link from #32).
- **Reclassified, not fixed** (FAIL → PENDING, because they depend only on `D-001`): B3, C1, R1, D3 (D3 also needed the NASA POWER credit in the README, added by this PR).
- New finding fixed in this PR: IBGE localities/mesh data (source of the `cruz-alta` site point, #36) was committed without a `RESOURCES.md` row; row added.
- B2, B8 and the README credit hold for `main` only after this PR is merged.

## A. Eligibility

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| A1 | All members (≤ 6) on the Members tab, confirmed at the same Local Event, none on the waitlist | UNVERIFIED | not visible from the repo | log in, open the Members tab, paste the 6 names in `page-draft.md` | FLIGHT |
| A2 | Official challenge selected: "Field Shift: Adapting Farms with NASA Data" | UNVERIFIED | not visible from the repo | check on the project page | FLIGHT |

## B. Project page

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| B1 | All required fields filled | FAIL | `page-draft.md`: field 4 now filled (app URL and `/data-methods` URL, both 200). Still open: fields 1, 2, 3, 5 and parts of 7–8 (D-001); member names (A1); demo tool names (B7); reviewer names (field 6) | fill D-001, then replace every `[PENDING …]`; people items in A1, B7, R2 | team (D-001) + FLIGHT |
| B2 | English on the page **and in linked materials** | PASS | Translated in this PR: `coord/status/eecom.md`, `inco.md`, `surgeon.md`; docstring and comments of `services/science/tests/test_units_fixture.py`, `test_calendar_agyear.py`, `test_contracts.py`, `test_contracts_export.py`, `test_ibge_pam.py`, `src/fieldshift/sources/ibge_pam.py`, `src/fieldshift/contracts/indices.py`. `coord/status/guido.md` was already English on `main` (#36). `AGENTS.md` §6 now says "English everywhere in the repo (`coord/` included)". Scan of every tracked text file (`git ls-files`, minus `data/cache/` and JSON) with a Portuguese word list and an accented-letter search: remaining hits are proper names (Florianópolis, Três Capões, Otávio), official titles and labels of Brazilian sources quoted as data (IBGE PAM labels in `ibge_pam.py` `name_pt`/`unit_pt` and test fixtures, "Comunicado Técnico 181", "Atlas Digital de Desastres no Brasil", the PAM table title in `data/dev/dev-cruz-alta/README.md`, the term "safra" glossed as "harvest year") and team front code names in `SI-USAGE.md`/`coord/` ("DADOS", "ROTAÇÃO", "CONTEÚDO"…). Raw IBGE API responses in `data/cache/ibge/` and their test fixtures are source data in Portuguese by nature. No `pt` content field or Portuguese i18n file exists (`apps/web/src/i18n/` has only `en.ts`) | demo captions: see C3 | CAPCOM (demo) |
| B3 | One-line statement at the top of the description | PENDING | D-001 "One-line differentiator" is empty | write it in D-001 (people, no AI) | team |
| B4 | "NASA Data" section lists each NASA dataset with link | PASS | `page-draft.md` field 7: NASA POWER, version, variables, upstream MERRA-2/CERES, link and the two citation sentences from the POWER referencing guide; `https://power.larc.nasa.gov/` returns 200 | fill the access date of the submitted site data (D-001 picks the sites; `cruz-alta` data was accessed 2026-11-14) | FLIGHT |
| B5 | Partner / other data section | PASS | field 8: no partner data. Non-NASA data read by code for a site today: IBGE localities/mesh (centroid of the `cruz-alta` point, #36), now in `RESOURCES.md` | when D-001 keeps `cruz-alta`, add the IBGE row to field 8 "Other data" | SURGEON |
| B6 | Limitations and "supports, not replaces, farmer judgment" | PASS | field 5 of the draft, from `content/methods/*.md` limitations and `apps/web/src/i18n/en.ts` `disclaimer.support`; the live `/` page shows "supports, and does not replace, the judgment of farmers and agronomists" (anonymous `curl`) | add concept-specific limitations after D-001 | GUIDO + SURGEON |
| B7 | SI declaration complete (field 6) | FAIL | `SI-USAGE.md` has **no row for the demo video** (synthetic voice, illustrative cards); tool names unknown | the member who made the video adds a row to `SI-USAGE.md` (date/time BRT, tool for voice, tool for cards, file, "audio" / "image"), then FLIGHT fills the `[PENDING: tool name]` slots of fields 6 and 8 | member who made the video + CAPCOM |
| B8 | References field lists every external code, text and image | PASS | Direct dependencies re-read from `package.json` (root, `apps/web`, `packages/contracts`) and `services/science/pyproject.toml` (incl. dev group and build backend), plus imports in `apps/`, `packages/`, `scripts/` and `services/`: every one now has a row in `RESOURCES.md` and in field 8 — added `@tailwindcss/turbopack` 4.3.5, `zustand` 5.1.0, `json-schema-to-typescript` 16.0.0, `@types/node` 24.19.2 / `@types/react` 19.3.0 / `@types/react-dom` 19.3.0 (all MIT, from `package-lock.json`), Geist and Geist Mono (SIL OFL 1.1), `uv_build`. Default `create-next-app` favicon (Next.js "N" mark, re-rendered with ffmpeg) removed; replaced by `apps/web/src/app/icon.svg` (team icon, SVG code written with Claude Code, declared in `SI-USAGE.md` and field 8; `next build` lists the `/icon.svg` route). Scope: repo and app. Demo/slide assets do not exist yet and are tracked in B7/C5 | re-run when demo or slide assets are added | FLIGHT |

## C. Demo

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| C1 | Format chosen (video ≤ 30 s **or** ≤ 7 slides) | PENDING | D-001 "Demo format" is empty; `docs/pitch/` is empty | decide in D-001 | team + CAPCOM |
| C2 | Within the limit | UNVERIFIED | no demo file in the repo | `ffprobe` duration ≤ 30.0 s or slide count ≤ 7, pasted here (`demo-plan.md` §5) | CAPCOM |
| C3 | English captions (if spoken in another language) | UNVERIFIED | no demo file in the repo | burn in English captions | CAPCOM |
| C4 | No person under 18 (image, voice, likeness) | UNVERIFIED | no demo file in the repo | frame-by-frame check | CAPCOM + FLIGHT |
| C5 | SI images/video watermarked; SI voice declared; illustrative cards labeled | FAIL | known: a member's demo video uses a synthetic voice and illustrative cards; no declaration exists yet (`SI-USAGE.md`, page fields 6 and 8, video metadata) | apply `demo-plan.md` §2: "AI-generated" watermark on SI cards, "Illustrative" on non-data cards, voice acknowledged in description + metadata + on screen | member who made the video + CAPCOM |
| C6 | No NASA logo, flag or insignia in the demo | UNVERIFIED | no demo file in the repo (repo assets: see R5) | check every frame and slide | CAPCOM |

## D. Links

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| D1 | Demo link opens without login | FAIL | no link yet | host as YouTube Unlisted/Public or Drive "Anyone with the link"; test in a private window | CAPCOM |
| D2 | Repository public | PASS | run 2, anonymous `curl -s -o /dev/null -w '%{http_code}' -L` → 200 for the repo, `README.md`, `RESOURCES.md`, `SI-USAGE.md`, `LICENSE`; `gh repo view` → `"visibility":"PUBLIC"` | — | — |
| D3 | README in English: how to run, datasets, credits, description, demo, live link | PENDING | present: English, "Run locally", live link (#32), and (this PR) a "NASA data and credits" section with the NASA POWER citation and links to `RESOURCES.md`, `content/methods/`, `SI-USAGE.md`. Missing only the project description and the demo link, both from D-001 | after D-001: add the summary and the demo link to `README.md` line 7 | FLIGHT |
| D4 | App public and working | PASS | `https://fieldshift-spaceapp.vercel.app` (README, #32), anonymous `curl -L` at 19:39 BRT: `/` 200, `/data-methods` 200, `/glossary` 200, `Server: Vercel`, no login. Note: the GitHub `deployments` API returns 0 and the repo `homepageUrl` is empty (Vercel Git integration without GitHub deployments) | optional: `gh repo edit FieldShift-SpaceApp/fieldshift --homepage https://fieldshift-spaceapp.vercel.app` (visible repo setting, Otávio); after this PR is deployed, `/icon.svg` should return 200 (today 404, the live site still serves the old `favicon.ico`) | Otávio (FLIGHT) |
| D5 | No "Restricted" Google Drive link | UNVERIFIED | no Drive link exists yet | check each link before submit | FLIGHT |

## R. Repository compliance (`checklist.md` items 1–9 and extras)

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| R1 | C1: D-001 FINAL | PENDING | `DECISIONS.md` D-001 "Status: OPEN", every field empty | concept meeting, without AI, fills every field with names and time | team |
| R2 | C2: SI row for every AI-assisted PR | PASS | rows through #36 (`guido/site-cruz-alta`); this PR adds two rows (text fixes; app icon). "Reviewed by" is `pending` in most rows: not required by the event, but the team convention asks for names | reviewers replace `pending` with their names | each front |
| R3 | SI images/videos watermarked | UNVERIFIED | new: `apps/web/src/app/icon.svg` is SVG markup written by Claude Code (three bars on a square, no text, no third-party mark). An "AI-generated" watermark is not readable at 16–32 px; it is declared in `SI-USAGE.md` and field 8 instead. Whether the watermark rule applies to a code-drawn vector icon is a human call. Demo not made yet | FLIGHT decides: accept with the declaration, **or** a person redraws/edits the icon (it is 4 shapes) and updates the `SI-USAGE.md` row, **or** remove it; demo: see C5 | FLIGHT; CAPCOM (demo) |
| R4 | SI audio, code and data acknowledged | FAIL | code and data: PASS (file headers, `SI-USAGE.md`, `provenance.json`). Audio: the synthetic demo voice is not acknowledged anywhere yet | see B7 and C5 | member who made the video + CAPCOM |
| R5 | C3: no NASA logo, flag or insignia in the repo or app | PASS | run 2: `git ls-files '*.png' '*.jpg' '*.jpeg' '*.svg' '*.gif' '*.webp' '*.ico' '*.mp4' '*.mp3' '*.wav'` → only `apps/web/src/app/icon.svg` (opened: geometric bars, rendered with Playwright at 64 and 16 px); no other `<svg` or `data:image` in `apps/`, `content/`, `docs/`; `apps/web/public/` has no tracked file (only the git-ignored synced `data/`); `git grep -i 'meatball\|nasa logo\|insignia\|worm'` → only rule text (`AGENTS.md`, `SI-USAGE.md`, `checklist.md`, `demo-plan.md`, `page-draft.md`, this file) | re-run on the final commit (new assets, pitch files) | FLIGHT |
| R6 | C4: NASA dataset listed and shown in the app | FAIL | `RESOURCES.md`: NASA POWER `selected`, with link and citation (PASS). Data: `data/sites/cruz-alta/output/` now holds NASA POWER series and indices (#36). App: no page shows a NASA value yet (`next build` routes: `/`, `/data-methods`, `/glossary`, `/icon.svg`; no site route) | render the site series in the app (`/sites/[siteId]`) | INCO |
| R7 | Licenses of data used and committed | PASS | `git ls-files data`: NASA POWER raw and derived files (`dev-floripa`, `dev-cruz-alta`, `cruz-alta`; open terms) and IBGE PAM/localities/mesh files (`RESOURCES.md` "yes, cite source"); nothing marked "In git? no" is committed | SURGEON to confirm the IBGE terms for the localities/mesh APIs (row says "not re-checked") | SURGEON |
| R8 | "check" licenses in `RESOURCES.md` | PENDING | rows with "In git? check" are all `candidate` and none is read by app code | if D-001 adopts one, confirm its license on the provider page and change "check" to yes/no **in the same PR as the code** | SURGEON + EECOM |
| R9 | Project license (OSI) | PASS | `LICENSE` Apache-2.0; `gh repo view` → `licenseInfo.key: apache-2.0` | — | — |
| R10 | Public production URL returns 200 | PASS | see D4 | — | — |
| R11 | Secrets: CI `hygiene` green on the submitted commit | PASS | `gh run list --branch main` → `ci` `success` on `741ea61` (hygiene + science + web); local `bash scripts/check-public-repo.sh` → "NFR9 ok". Final word for this PR: its own checks | re-check on the final submitted commit | FLIGHT |
| R11b | `.gitleaksignore` entries are reviewed false positives only | PASS | unchanged since run 1: two entries (`3edf140…` PR #28 comment; `0c653c0…` run-1 quote of it), both with a note; no new entry in this PR | any new entry needs the same note (commit, file, rule, line, why) and a reviewer | FLIGHT |
| R12 | Page in English, limitations, SI field drafted | PASS | `page-draft.md` | fill the placeholders | FLIGHT |
| R13 | Submit before the deadline, confirmation captured | UNVERIFIED | Sunday action | Submit for Judging by 20:00 BRT; screenshot of the confirmation banner in `coord/status/flight.md`; re-submit if improved before 23:59 (only the last save counts) | FLIGHT |

## Left for people (no AI can close these)

- **D-001** (team, without AI): B3, C1, D3, R1, then B1, R8.
- **Demo** (member who made the video + CAPCOM): B7, C2–C6, D1, R4.
- **Logged-in checks** (FLIGHT): A1, A2, D5, R13.
- **App** (INCO): R6, a site page showing the NASA POWER series.
- **Decisions**: R3 icon (accept / redraw / remove); merge of this PR, which includes the `AGENTS.md` §6 protocol change.

## Drift found

- Run 1: `AGENTS.md` §6 vs the official English rule — fixed in this PR (protocol change, needs FLIGHT's OK at merge).
- Run 2: IBGE localities/mesh data committed by #30/#36 without a `RESOURCES.md` row — fixed in this PR.
- Run 2: the GitHub repo "homepage" field is empty although the app is live (D4, optional).

## Non-blocking suggestions

- Request a FortiGuard Web Filter category for the production domain (the guide recommends it; not required).
