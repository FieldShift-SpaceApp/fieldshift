# Submission page draft

> **SI-assisted:** written with Claude Code (Anthropic) from `RESOURCES.md`, `SI-USAGE.md`, `content/methods/` and the official 2026 Project Submission Guide; human review pending. Concept, name and differentiator are **not** written here (rule C1): every field that depends on them is a `[PENDING D-001: …]` placeholder for the team.

Owner: FLIGHT. This is the text to paste into the Space Apps project page. Fields are in the official order of the [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) (version of 2026-11-13, read 2026-11-14). Compliance status of each item: [`preflight.md`](preflight.md). Demo rules and script skeleton: [`demo-plan.md`](demo-plan.md).

## Rules that apply to every field

- **Language:** "All content in the project form must be in English." The same applies to every linked material (repo, app, demo).
- **Length:** the official guide gives **no character or word limit** for any field (checked in the 2026-11-13 version). It says: "The more information you provide on this page, the better the judges can rate your submission!"
- **Uploads:** images only, JPG/PNG/GIF up to 10 MB each. Videos and documents cannot be uploaded: link them.
- **Links:** "publicly accessible link with no logins, permissions, or registrations required." Test every link in a private window, logged out.
- **Required fields:** the guide does not mark them one by one; the form refuses to submit while a required field is empty. Treat all eight as required.
- **No NASA branding** in any SI-generated content; **no image, video, audio or likeness of anyone under 18**; no commercial promotion; no personal data.
- **Only the last saved submission is judged.** Deadline: Sun 2026-11-15 23:59 local time of the Local Event (BRT). Internal submit: 20:00 BRT.

## Team and event (set in the Members / Challenge tabs, not free text)

| Item | Value | Status |
|---|---|---|
| Team name | FieldShift | filled |
| Local Event | Florianópolis, Brazil (Founder Haus, Jurerê Internacional) | filled |
| Challenge | Field Shift: Adapting Farms with NASA Data | filled |
| Members (max 6, all confirmed at the same Local Event, none on the waitlist) | `[PENDING: the 6 names exactly as on the Members tab — checked by FLIGHT logged in]` | to verify |

---

## 1. Project Name

> *Official prompt:* "What is the name of your project?"

`[PENDING D-001: product name]`

## 2. High-Level Project Summary

> *Official prompt:* "What did you develop? How does it address the challenge? Why is it important?"

`[PENDING D-001: summary written by the team — what was developed, how it addresses the challenge, why it matters. Start with the one-line differentiator from D-001.]`

## 3. Link to Project Demo

> *Official prompt:* a 7-slide presentation (including title and introductory slides) **or** a video of 30 seconds or less; the link "should not require a password, permission, or registration".

`[PENDING D-001: demo format (video or slides) and public URL]` — limits, labels and checks in [`demo-plan.md`](demo-plan.md).

## 4. Link to Final Project

> *Official prompt:* "a website [...] code repository, or platforms such as YouTube, Google Drive, GitHub [...] should not require a password, permission, or registration".

- Web app: https://fieldshift-spaceapp.vercel.app
- Code repository (public, Apache-2.0): https://github.com/FieldShift-SpaceApp/fieldshift
- Data & Methods (datasets, methods, limitations, use of AI): https://fieldshift-spaceapp.vercel.app/data-methods (source: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/content/methods)

## 5. Detailed Project Description

> *Official prompt:* "What exactly does it do? How does it work? What benefits does it have? What do you hope to achieve? What tools, coding languages, hardware, or software did you use".

`[PENDING D-001: what it does, for whom, how a user goes through it, benefits, what the team hopes to achieve]`

The parts below do not depend on the concept and can be pasted as they are.

**How the data pipeline works (built so far).** A Python 3.12 pipeline (`services/science`) downloads daily NASA POWER data for each site point (1981 to the last complete month), keeps the raw response with its request URL and access time, aggregates it to monthly values (a month gets a value only when every day is valid; gaps stay empty and are listed), computes reference evapotranspiration (ET0) with the FAO-56 Penman-Monteith method, and derives climate indices (heat and frost days, growing degree-days, water deficit as ET0 minus rain, extreme rain above the 95th percentile). A `fieldshift validate --all` check runs in CI over every data file. Every value written carries a provenance record: dataset, version, access date, method and known limitations. The web app (Next.js, static) reads those files at build time and shows each number with its source and data type (satellite-observed, modeled, computed or user-provided). Data contracts between pipeline and app are generated JSON Schema and TypeScript types, checked in CI.

`[PENDING D-001: concept-specific stages (model, ranking, user inputs) once they exist in code]`

**Limitations and uncertainty.**
- NASA POWER values are a **regional signal**: each value is the POWER grid cell that contains the site point (meteorology about 0.5° × 0.625°, radiation 1° × 1°), not a field measurement, and it is not downscaled.
- POWER values are **modeled** (reanalysis-based for meteorology and soil wetness), not direct observations, and are labeled as such.
- POWER soil wetness (`GWETTOP`, `GWETROOT`, `GWETPROF`) is a 0–1 fraction of saturation from a land-surface model, not volumetric soil moisture.
- Months with any missing day are left empty, never filled in.
- `EVPTRNS` is not used (in MERRA-2 it is the transpiration energy flux only); ET0 is computed with FAO-56 instead.
- The heat threshold (35 °C) and the growing degree-day base (10 °C) are generic defaults until the agronomist sets them per site and crop; the provenance record says when a default is used.
- The water deficit (ET0 minus rain) is a climate indicator, not a soil water balance (no runoff, soil storage or crop coefficient).
- `[PENDING D-001: limitations of the concept-specific stages]`

Full list, per method: Data & Methods page (link in field 4).

**Use statement.** This tool supports, and does not replace, the judgment of farmers and agronomists. It explores options; it does not prescribe actions or promise yields, profit or carbon credits.

**Tools, languages and software.** Python 3.12 (uv, pydantic, httpx, PyYAML, pytest, Ruff); TypeScript, Next.js 16, React 19, Tailwind CSS 4, shadcn/Radix UI; Vitest, Testing Library and Playwright for tests; GitHub Actions CI with gitleaks secret scanning. No hardware. Full list with versions and licenses in field 8.

## 6. Use of Super Intelligence (SI)

> *Official prompt:* "Did you utilize any Super Intelligence (SI) tools and software in preparing your solution? If yes, how did you use them?" The guide says this answer is for data collection and is not shown to judges; SI indicators inside the project are.

**Answer: Yes.**

We used SI tools as assistants for research, code, documentation and review. **Origin of the idea, stated as it happened:** the team generated the starting ideas at a human ideation meeting on 14 November (transcribed in the team workspace), and the farmer on the team described the real winter decision in an interview. At the team lead's request, an SI tool (Claude Code) then helped **compare and synthesize concepts from those human ideas** and from data the team had verified, and drafted the pitch text. The team chose the final concept and wrote the one-line statement in its own words (decision record `D-001` in `DECISIONS.md`). `[PENDING D-001: names and time of the decision; quote the human ideas the concept builds on (e.g. analog years); confirm the wording with the Local Lead if possible]`

- **Code (SI-generated, human-directed):** Claude Code (Anthropic) wrote most of the code in the repository under the team's instructions: the NASA POWER ingestion and monthly aggregation, the FAO-56 ET0 computation, the climate indices and data validation, the data contracts and their code generation, the web app components and pages, the tests and the CI workflow. Every SI-assisted file carries an "SI-assisted" header naming the tool and the reviewer, and every SI-assisted pull request has a row in `SI-USAGE.md`. Codex (OpenAI) was used to review one planning document.
- **Text (SI-generated, human-directed):** Claude Code and Claude (Anthropic) drafted the documentation (README, methods, glossary, related work, resources and licenses, this submission text) and the team's internal planning documents (research notes, requirements, architecture). Research used Claude Code with the Firecrawl CLI and web search to read official pages; facts were checked against their sources and the sources are cited.
- **Data:** no number shown in the project is produced by an SI model. Numbers come from NASA POWER and from deterministic code (FAO-56); SI wrote and ran that code. Data files produced this way are declared in `SI-USAGE.md` and in each dataset's `provenance.json`.
- **Demo audio and visuals:** the demo video uses an **SI-generated (synthetic) narration voice** `[PENDING: tool name]` and **illustrative cards** `[PENDING: tool name, or "made by hand"]`. The voice is acknowledged in the video's description text, in its file metadata and in an on-screen caption; every SI-generated image or card carries a visible "AI-generated" watermark, and illustrative cards that do not show real data are labeled "Illustrative". No NASA logo, flag or mission insignia appears in SI-generated content. `[PENDING: confirm after the video is final — see demo-plan.md]`
- **Human review:** `[PENDING: names of the people who reviewed SI-generated code and text — SI-USAGE.md column "Reviewed by"]`

Full log with dates, tools and files: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/SI-USAGE.md

## 7. NASA Data

> *Official prompt:* "Provide specific details about what NASA data and resources you used. To be eligible for a Global Award, you must use at least one NASA data or resource."

**NASA POWER (Prediction Of Worldwide Energy Resources), NASA Langley Research Center** — https://power.larc.nasa.gov/
- **Product:** POWER Daily API, version 2.10.3, community `AG` (agroclimatology), point endpoint.
- **Variables used:** `T2M`, `T2M_MAX`, `T2M_MIN`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `PRECTOTCORR`, `PS` (meteorology and radiation), modeled soil wetness `GWETTOP`, `GWETROOT`, `GWETPROF` and modeled land evaporation `EVLAND`.
- **Upstream NASA products (served through POWER):** MERRA-2 reanalysis (meteorology and soil wetness, about 0.5° × 0.625°) and CERES SYN1deg (solar radiation, 1° × 1°), per the [POWER methodology](https://power.larc.nasa.gov/docs/methodology/).
- **Period:** daily, 1981 to the last complete month (radiation from 1984).
- **How it is used:** monthly climate series and FAO-56 reference evapotranspiration (ET0) for each site, and climate indices derived from them (heat and frost days, growing degree-days, water deficit, extreme rain). `[PENDING D-001: what the concept does with these series]`
- **Access and terms:** open, no account; NASA Earth science data use guidance. Citation, as requested by the [POWER referencing guide](https://power.larc.nasa.gov/docs/referencing/):
  - "The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division."
  - "The data was obtained from the POWER Project's Daily 2.10.3 version on `[PENDING: access date of the submitted site data, YYYY/MM/DD, from data/sites/<id>/output/provenance.json]`."

`[PENDING D-001: any other NASA dataset adopted (candidates are listed in RESOURCES.md) — add it here only when code reads it and RESOURCES.md marks it "selected"]`

## 8. Space Agency Partner Data and Other References

> *Official prompt:* "List all of the data, resources, and tools used in your project. Resources should include any code, text, and images (even if they are open source or freely available)".

**Space Agency Partner data:** none used so far. `[PENDING D-001: partner datasets adopted, if any]`

**Other data:** none used so far. `[PENDING D-001: non-NASA datasets adopted, each with provider, URL and license from RESOURCES.md; only rows whose license column is not "check"]`

**Methods and references**
- Allen, R. G., Pereira, L. S., Raes, D., Smith, M. (1998). *Crop evapotranspiration — Guidelines for computing crop water requirements.* FAO Irrigation and Drainage Paper 56. FAO, Rome. https://www.fao.org/4/x0490e/x0490e00.htm (FAO publication) — daily ET0 from NASA POWER.
- Zhang, X. et al. (2011). Indices for monitoring changes in extremes based on daily temperature and precipitation data. *WIREs Climate Change* 2, 851–870. https://doi.org/10.1002/wcc.147 — and ETCCDI, definitions of the 27 core indices, https://etccdi.pacificclimate.org/list_27_indices.shtml — heat/frost days and extreme rain (R95p, R95pTOT).
- McMaster, G. S., Wilhelm, W. W. (1997). Growing degree-days: one equation, two interpretations. *Agricultural and Forest Meteorology* 87, 291–300. https://doi.org/10.1016/S0168-1923(97)00027-0 — growing degree-days.
- Hyndman, R. J., Fan, Y. (1996). Sample quantiles in statistical packages. *The American Statistician* 50(4), 361–365. https://doi.org/10.1080/00031305.1996.10473566 — 95th percentile threshold.
- Related work and its sources: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/content/related-work.md
- Method references (one file per method): https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/content/methods

**Code libraries and tools** (versions pinned in `package-lock.json` and `services/science/uv.lock`)

| Tool / library | Version | License |
|---|---|---|
| Next.js | 16.4.6 | MIT |
| React / React DOM | 19.3.1 | MIT |
| TypeScript | 6.0.3 | Apache-2.0 |
| Tailwind CSS (+ @tailwindcss/turbopack) | 4.3.5 | MIT |
| shadcn (CLI) | 4.23.0 | MIT |
| radix-ui | 1.8.1 | MIT |
| lucide-react (icons) | 1.73.0 | ISC |
| class-variance-authority | 0.7.1 | Apache-2.0 |
| cn | 0.5.2 | MIT |
| tw-animate-css | 1.4.0 | MIT |
| zustand | 5.1.0 | MIT |
| react-markdown + remark-gfm | 10.1.0 + 4.0.1 | MIT |
| gray-matter | 4.0.3 | MIT |
| yaml | 2.9.1 | ISC |
| json-schema-to-typescript | 16.0.0 | MIT |
| ESLint + eslint-config-next | 9.39.5 + 16.4.6 | MIT |
| Vitest | 5.1.0 | MIT |
| Vite + @vitejs/plugin-react | 8.3.8 + 6.3.0 | MIT |
| Testing Library (react, dom) | 16.3.3, 10.4.2 | MIT |
| jsdom | 29.1.1 | MIT |
| @types/node, @types/react, @types/react-dom (DefinitelyTyped) | 24.19.2, 19.3.0, 19.3.0 | MIT |
| Playwright | 1.65.1 | Apache-2.0 |
| Node.js | 24.x | MIT |
| Python | 3.12 | PSF-2.0 |
| uv (incl. `uv_build`) | 0.11.3 | MIT OR Apache-2.0 |
| pydantic | 2.14.3 | MIT |
| httpx | 0.28.1 | BSD-3-Clause |
| PyYAML | 6.0.3 | MIT |
| pytest | 9.2.0 | MIT |
| Ruff | 0.17.5 | MIT |
| gitleaks | 8.30.1 | MIT |
| GitHub Actions | — | service terms |

**Fonts and images**
- Geist and Geist Mono fonts (Vercel), loaded through `next/font/google` — SIL Open Font License 1.1.
- App icon: `apps/web/src/app/icon.svg`, three geometric bars drawn as SVG code for this project with Claude Code (declared in `SI-USAGE.md`); no third-party mark, no NASA logo. It replaced the `create-next-app` default favicon (Next.js mark).
- `[PENDING: every image, card, icon and music track used in the app, slides or demo video, with source and license]`

**SI tools** (details in field 6): Claude Code and Claude (Anthropic), Codex (OpenAI), Firecrawl CLI. `[PENDING: voice and image tools used in the demo]`

Every direct dependency of `package.json` (root, `apps/web`, `packages/contracts`) and `services/science/pyproject.toml`, and the Geist fonts, has a row in `RESOURCES.md` (preflight B8, run 2).

---

## Final declarations (checkboxes on the form)

- [ ] Terms and Conditions and Privacy Policy accepted.
- [ ] "I confirm that the submitted project represents my team's original work and that all external resources including code, text and images (even if they are open source or freely available) used in the project are listed in the References field" — tick only after field 8 has no `[PENDING]` left.
