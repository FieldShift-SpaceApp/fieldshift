# Submission preflight

> **SI-assisted:** checks run and written with Claude Code (Anthropic); human review pending. A person must re-run the checks marked UNVERIFIED and sign the final run (`checklist.md`).

Owner: FLIGHT. State of the repository on **2026-11-14 14:48 BRT**, `main` at `f21d8c6` (after #24, #25 and #28), merged into this branch. Sources: squad submission checklist (team workspace), [`checklist.md`](checklist.md), the official [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) and [Judging & Awards Guide](https://www.spaceappschallenge.org/resources/judging-awards-guide/) (2026-11-13 versions).

**Legend:** PASS = checked, evidence given · FAIL = checked and not compliant today · UNVERIFIED = cannot be checked from the repository (needs a person logged in, or the artifact does not exist yet) · PENDING = depends on `D-001`, not a defect today.

## Summary

| Status | Count |
|---|---|
| PASS | 11 |
| FAIL | 14 |
| UNVERIFIED | 9 |
| PENDING | 1 |

## A. Eligibility

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| A1 | All members (≤ 6) on the Members tab, confirmed at the same Local Event, none on the waitlist | UNVERIFIED | not visible from the repo | log in, open the Members tab, paste the 6 names in `page-draft.md` | FLIGHT |
| A2 | Official challenge selected: "Field Shift: Adapting Farms with NASA Data" | UNVERIFIED | not visible from the repo | check on the project page | FLIGHT |

## B. Project page

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| B1 | All required fields filled | FAIL | `page-draft.md`: fields 1, 2, 3, 5 depend on D-001; field 4 lacks the app URL | fill D-001, then replace every `[PENDING D-001: …]` | team (D-001) + FLIGHT |
| B2 | English on the page **and in linked materials** | FAIL | page draft: English. Repo: Portuguese lines in `coord/status/eecom.md` (lines 6, 7, 13, 14, 16), `guido.md` (9), `inco.md` (6, 7, 9, 10, 13), `surgeon.md` (6–9), and the docstring/comments of `services/science/tests/test_units_fixture.py` (lines 1–5, 22). `AGENTS.md` §6 allows Portuguese in `coord/`, which conflicts with the official rule because the repo is the linked final project | each front translates its own `coord/status/<code>.md` to English before 20:00 Sun; GUIDO translates the test docstring and comments; FLIGHT proposes the `AGENTS.md` §6 change ("English everywhere in the repo") | EECOM, GUIDO, INCO, SURGEON; FLIGHT (AGENTS.md) |
| B3 | One-line statement at the top of the description | FAIL | D-001 "One-line differentiator" is empty | write it in D-001 (people, no AI) | team |
| B4 | "NASA Data" section lists each NASA dataset with link | PASS | `page-draft.md` field 7: NASA POWER, version, variables (incl. `GWETPROF` and `EVLAND` added by #28), upstream MERRA-2/CERES, link and the two citation sentences from the POWER referencing guide; `https://power.larc.nasa.gov/` returns 200 | fill the access date of the submitted site data | FLIGHT |
| B5 | Partner / other data section | PASS | field 8: no partner or non-NASA data is read by code today (`RESOURCES.md`: only NASA POWER is `selected`) | add rows when D-001 adopts a dataset | SURGEON |
| B6 | Limitations and "supports, not replaces, farmer judgment" | PASS | field 5 of the draft, from `content/methods/*.md` limitations (incl. `climate-indices.md` from #28) and `apps/web/src/i18n/en.ts` `disclaimer.support` | add concept-specific limitations after D-001 | GUIDO + SURGEON |
| B7 | SI declaration complete (field 6) | FAIL | draft text written from `SI-USAGE.md`, but `SI-USAGE.md` has **no row for the demo video** (synthetic voice, illustrative cards); tool names unknown | the member who made the video adds a row to `SI-USAGE.md` (date/time BRT, tool for voice, tool for cards, file, "audio" / "image"), then FLIGHT fills the `[PENDING: tool name]` slots of fields 6 and 8 | member who made the video + CAPCOM |
| B8 | References field lists every external code, text and image | FAIL | in code but missing from `RESOURCES.md`: `zustand` 5.1.0 (MIT, `apps/web`), `json-schema-to-typescript` 16.0.0 (MIT, `packages/contracts`), `@tailwindcss/turbopack` 4.3.5 (MIT), Geist / Geist Mono fonts via `next/font/google` (SIL OFL 1.1), default `favicon.ico` from `create-next-app` (Next.js mark) | add the four rows to the "Tools and libraries" table of `RESOURCES.md`; replace the favicon with a team icon or cite it | SURGEON (`RESOURCES.md`); INCO (favicon) |

## C. Demo

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| C1 | Format chosen (video ≤ 30 s **or** ≤ 7 slides) | FAIL | D-001 "Demo format" is empty; `docs/pitch/` is empty | decide in D-001 | team + CAPCOM |
| C2 | Within the limit | UNVERIFIED | no demo file yet | `ffprobe` duration ≤ 30.0 s or slide count ≤ 7, pasted here (`demo-plan.md` §5) | CAPCOM |
| C3 | English captions (if spoken in another language) | UNVERIFIED | no demo file yet | burn in English captions | CAPCOM |
| C4 | No person under 18 (image, voice, likeness) | UNVERIFIED | no demo file yet | frame-by-frame check | CAPCOM + FLIGHT |
| C5 | SI images/video watermarked; SI voice declared; illustrative cards labeled | FAIL | known: a member's demo video uses a synthetic voice and illustrative cards; no declaration exists yet (`SI-USAGE.md`, page fields 6 and 8, video metadata) | apply `demo-plan.md` §2: "AI-generated" watermark on SI cards, "Illustrative" on non-data cards, voice acknowledged in description + metadata + on screen | member who made the video + CAPCOM |
| C6 | No NASA logo, flag or insignia in the demo | UNVERIFIED | no demo file yet (repo assets: see R5) | check every frame and slide | CAPCOM |

## D. Links

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| D1 | Demo link opens without login | FAIL | no link yet | host as YouTube Unlisted/Public or Drive "Anyone with the link"; test in a private window | CAPCOM |
| D2 | Repository public | PASS | anonymous `curl -s -o /dev/null -w '%{http_code}' -L` → 200 for the repo, `README.md`, `RESOURCES.md`, `SI-USAGE.md`, `LICENSE`, `content/methods/` and `raw.githubusercontent.com/.../README.md`; `gh repo view` → `"visibility":"PUBLIC"` | — | — |
| D3 | README in English: how to run, datasets, credits, description, demo, live link | FAIL | English, "Run locally" and links to `RESOURCES.md`/`SI-USAGE.md`: present. Line 7 still says "Project description, demo and live link will be added here." | after D-001 and the Vercel URL: add the summary, demo link, app URL and the NASA POWER citation to `README.md` | FLIGHT |
| D4 | App public and working | FAIL | no deployment: `gh api repos/FieldShift-SpaceApp/fieldshift/deployments` → 0; repo `homepageUrl` empty; Vercel not connected | import the repo in Vercel: Root Directory `apps/web`, Node 24, default `npm run build` (the `prebuild` step `scripts/sync-data.mjs` reads files at the repo root, so keep "Include files outside the root directory" on); no password protection on the production URL; then `gh repo edit FieldShift-SpaceApp/fieldshift --homepage <url>` and `curl -s -o /dev/null -w '%{http_code}' <url>` → 200 for `/`, `/data-methods`, `/glossary`. Optional (guide): request a FortiGuard category for the domain | Otávio (FLIGHT) |
| D5 | No "Restricted" Google Drive link | UNVERIFIED | no Drive link exists yet | check each link before submit | FLIGHT |

## R. Repository compliance (`checklist.md` items 1–9 and extras)

| # | Item | Status | Evidence | Correction | Owner |
|---|---|---|---|---|---|
| R1 | C1: D-001 FINAL | FAIL | `DECISIONS.md` D-001 "Status: OPEN", every field empty | concept meeting, without AI, fills every field with names and time | team |
| R2 | C2: SI row for every AI-assisted PR | PASS | rows for PRs #4, #5, #6, #16, `infra/tests-compliance` (#17), `eecom/power-ingest` (#20), `inco/units-provenance` (#21), `surgeon/related-work-methods` (#24), `inco/rotation-timeline` (#25), #28 (two EECOM rows, issue #22); this PR adds its own row. "Reviewed by" is `pending` in most rows: not required by the event, but the team convention asks for names | reviewers replace `pending` with their names | each front |
| R3 | SI images/videos watermarked | UNVERIFIED | the repo has no SI-generated image (only image file: `favicon.ico`, tool output); demo not made yet | see C5 | CAPCOM |
| R4 | SI audio, code and data acknowledged | FAIL | code and data: PASS (file headers, `SI-USAGE.md`, `provenance.json`). Audio: the synthetic demo voice is not acknowledged anywhere yet | see B7 and C5 | member who made the video + CAPCOM |
| R5 | C3: no NASA logo, flag or insignia in the repo or app | PASS | `git ls-files` for png/jpg/jpeg/svg/gif/webp/ico/mp4/mp3/wav → only `apps/web/src/app/favicon.ico`; opened (converted to PNG): the Next.js "N" mark, 3 sizes; `apps/web/public/` does not exist; `git grep -i 'meatball\|nasa logo\|insignia'` → only the rule text in `AGENTS.md`, `SI-USAGE.md`, `checklist.md` | re-run on the final commit (new assets, pitch files) | FLIGHT |
| R6 | C4: NASA dataset listed and shown in the app | FAIL | `RESOURCES.md`: NASA POWER `selected`, with link and citation (PASS). App: no page shows a NASA value yet; only DEV data exists (`data/dev/dev-floripa/`), `data/sites/` is empty | run `fieldshift fetch power` for the demo sites (needs `site.yaml`, issue #8) and render the series in the app | EECOM + INCO (SURGEON for #8) |
| R7 | Licenses of data used and committed | PASS | committed data: only NASA POWER raw and derived files (`data/cache/power/dev-floripa/`, `data/dev/dev-floripa/output/`), open terms; nothing marked "In git? no" is committed (`git ls-files data`) | — | — |
| R8 | "check" licenses in `RESOURCES.md` | PENDING | 8 rows with "In git? check" (INMET, CONAB, SoilGrids, FAOSTAT, WaPOR, USDA CDL, SSURGO, USGS), all `candidate`; none read by code | if D-001 adopts one, confirm its license on the provider page and change "check" to yes/no **in the same PR as the code** | SURGEON + EECOM |
| R9 | Project license (OSI) | PASS | `LICENSE` Apache-2.0; `gh repo view` → `licenseInfo.key: apache-2.0` (Space Apps default license) | — | — |
| R10 | Public production URL returns 200 | FAIL | no production URL (D4) | see D4 | Otávio (FLIGHT) |
| R11 | Secrets: CI `hygiene` green on the submitted commit | PASS | `gh run list --branch main` → `success` on `f21d8c6` (hygiene + science + web). This PR's first run, before merging `main`, failed `hygiene` with "leaks found: 1" (the CI log names no file). Local gitleaks v8.30.1 on this branch after the merge: "no leaks found" (48 commits, all refs; also 0 on this PR's own commit alone). Most likely cause: the run happened before #28 brought `.gitleaksignore` to `main`, while the #28 branch commit `3edf140` was already in the fetched history. Final word: the PR checks after the merge | re-check on the final submitted commit | FLIGHT |
| R11b | `.gitleaksignore` entries are reviewed false positives only | PASS | one entry: `3edf140…:services/science/src/fieldshift/contracts/common.py:generic-api-key:16`, a code comment with the word "keys" listing contract additions (PR #28), already reviewed by the coordination; the comment was reworded later, the entry covers only the old commit. Checked in this run: line 16 of that commit is `# 1.1.0 (MINOR, issue #22): climate-index keys, EVLAND/GWETPROF keys, Metric/MonthlyProfile` (no secret); `3edf140` lives only on the `eecom/indices-validate` branch (not in `main`, which got the squash `f21d8c6`) | any new entry needs the same note (commit, file, rule, line, why) and a reviewer | FLIGHT |
| R12 | Page in English, limitations, SI field drafted | PASS | `page-draft.md` (this PR) | fill the placeholders | FLIGHT |
| R13 | Submit before the deadline, confirmation captured | UNVERIFIED | Sunday action | Submit for Judging by 20:00 BRT; screenshot of the confirmation banner in `coord/status/flight.md`; re-submit if improved before 23:59 (only the last save counts) | FLIGHT |

## Drift found

- `AGENTS.md` §6 ("`coord/` notes: Portuguese is fine") vs the official rule "Use English language on the project submission page and in any linked materials". The repo is the linked final project. Proposed fix in B2; needs FLIGHT's OK.
- `README.md` line 7 promises content that does not exist yet (D3).

## Non-blocking suggestions

- Replace the Next.js default favicon with a team icon (also removes a third-party mark from the app).
- Request a FortiGuard Web Filter category for the production domain (the guide recommends it; not required).
