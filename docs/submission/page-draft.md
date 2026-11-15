# Submission page draft

> **SI-assisted:** written with Claude Code (Anthropic) from `RESOURCES.md`, `SI-USAGE.md`, `content/methods/`, `analysis/*/README.md`, `data/sites/cruz-alta/output/*.json`, the team's verified numbers and the official 2026 Project Submission Guide; human review pending. The product **name** and the **one-line statement** are not written here (rule C1): they stay `[PENDING D-001: …]` for the team.

Owner: FLIGHT. This is the text to paste into the Space Apps project page. Fields are in the official order of the [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) (version of 2026-11-13, read 2026-11-14). Compliance status of each item: [`preflight.md`](preflight.md). Demo rules and script skeleton: [`demo-plan.md`](demo-plan.md).

## How to use this draft

- Paste only the text **inside each "Paste" block**. "Notes (do not paste)" are for the team.
- `[PENDING D-001: …]` = only the team writes it (name and one-line statement).
- `[IF PUBLISHED: …]` = describes the agronomist's farmer-facing app, which is **not public yet**. If it is published before submitting, keep the text and remove the brackets (and fill its URL in field 4); if not, delete the whole bracketed passage. Never leave a bracket in the submitted page.
- `[CHOOSE]` = pick one variant, delete the other.
- Tense rule: what is public today (repo, live app, analyses, data files) is in the present tense. Nothing else is.

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

**Paste:**

`[PENDING D-001: product name]`

## 2. High-Level Project Summary

> *Official prompt:* "What did you develop? How does it address the challenge? Why is it important?"

**Paste:**

`[PENDING D-001: one-line statement]`

In southern Brazil, the winter after soybean is a bet placed months ahead: the farmer chooses wheat, a cover crop or fallow while the soybean is still in the field. In the Planalto Médio of Rio Grande do Sul (18 municipalities around Cruz Alta), wheat yield fell below 75% of its own trend in **53% of municipal harvests in El Niño winters, against 3.5% in La Niña winters** (8 El Niño and 5 La Niña winters, 1981–2025; the difference holds in a winter-level permutation test, p = 0.003). In 2023, the last El Niño winter, the state's wheat output fell from 5.3 to 2.6 million tonnes and Brazil's public crop-guarantee programme, Proagro, approved R$ 2.07 billion in wheat claims. Rio Grande do Sul planted 1.16 million hectares of wheat in 2025, 46% of Brazil's, on about 20,000 farms (2017 Census of Agriculture).

NASA data show the mechanism. **NASA GPM IMERG** counts, at Cruz Alta, an average of **4.4 days with ≥ 50 mm of rain in September–November of El Niño years, against 2.6 in neutral and 1.4 in La Niña years** (1998–2025) — the wheat harvest window. A rain gauge on the ground and NASA POWER rank the three phases the same way. And the soil is **barest in November — when storms still come**: Copernicus Sentinel-2 (ESA) shows 68% of Cruz Alta's cropland without green cover in the first half of November (median 2019–2025), and IMERG has a ≥ 50 mm day in that half-month in 44% of years.

We developed an open, reproducible evidence base for this decision, and a web app that shows it. A Python pipeline turns NASA POWER, GPM IMERG, MODIS and NASA GMAO GEOS-S2S data — with ESA Sentinel-2 and Brazilian public data (IBGE, ANA, Central Bank, NOAA ENSO index) — into site data files in which every number carries its source, version, access date, method and limitations. The live app shows the Cruz Alta climate from NASA POWER with a ground check against local weather stations, and a Data & Methods page with every method and limitation. Two analyses rerun from the public sources with one command: El Niño and wheat losses, and "storms meet soil" (heavy rain on cropland with no green, plus a "straw clock" of how much winter residue still covers the ground in November). `[IF PUBLISHED: The farmer-facing app puts the decision on one screen: next winter's El Niño odds from dated forecasts, how often February forecasts got the winter right, the heavy-rain signal, and three rotations — soybean–wheat, soybean–cover crop, soybean–fallow — with their soil effect, weather risk, and money only where a source gives a value.]`

Why it matters: the decision is made before winter, and forecasts issued in February do not beat "always neutral" on the winter's ENSO phase (NASA GEOS-S2S: 0.56 against 0.71, 41 years). So we never show a yes/no forecast: we show odds, each forecast's own track record, and local history. And it is happening now: from 1 September to 11 November 2026, NASA POWER recorded 935 mm and five days with ≥ 50 mm at Cruz Alta, against 537 mm and 1.2 days in an average El Niño year over the same days. The tool supports, and does not replace, the judgment of farmers and agronomists.

**Notes (do not paste):**
- Every number above is in the public repo (`analysis/enso-wheat/README.md`, `data/sites/cruz-alta/output/enso-rain-signal.json`, `analysis/storms-bare-soil/README.md`, `forecast-scorecard.json`, `now-2026.json`) **except the scale sentence** (5.3 → 2.6 Mt, R$ 2.07 bn, 1.16 Mha, 46%, ~20,000 farms). That sentence was verified by the team with a script against IBGE SIDRA 1612/6957 and the BCB Proagro matrix on 2026-11-14, but the script lives only in the private team workspace. If someone asks "where is this reproduced?", the answer today is "primary sources in field 8". Either publish that script before submitting or accept this.
- Vetoes respected: "53% of municipal harvests", never "of winters"; no "soybean flips after La Niña" rate; no "credit rose"; no "+36% hot days"; no "soil exposed in winter"; no claim of a 2026 wheat failure (IBGE publishes it in 2027).
- 2026: say "NASA POWER", not IMERG (IMERG via POWER stops on 2026-09-14 at access).

## 3. Link to Project Demo

> *Official prompt:* a 7-slide presentation (including title and introductory slides) **or** a video of 30 seconds or less; the link "should not require a password, permission, or registration".

**Paste:** `[PENDING: demo URL — format and checks in demo-plan.md]`

## 4. Link to Final Project

> *Official prompt:* "a website [...] code repository, or platforms such as YouTube, Google Drive, GitHub [...] should not require a password, permission, or registration".

**Paste:**

- Web app: https://fieldshift-spaceapp.vercel.app
  - Cruz Alta site page (NASA POWER climate, indices, ground check, source of every number): https://fieldshift-spaceapp.vercel.app/sites/cruz-alta
  - Data & Methods (datasets, methods, limitations, use of AI): https://fieldshift-spaceapp.vercel.app/data-methods
- Code repository (public, Apache-2.0): https://github.com/FieldShift-SpaceApp/fieldshift
- Reproducible analysis, El Niño and wheat losses: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/enso-wheat
- Reproducible analysis, storms meet soil: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/storms-bare-soil
- Site data files (with provenance): https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/data/sites/cruz-alta/output
- `[IF PUBLISHED: Farmer-facing app: <public URL>]`

**Notes (do not paste):** all public links above returned HTTP 200 to an anonymous `curl -L` in preflight run 3. Do not link the private team workspace or the agronomist's private repository. If the farmer-facing app is published, its URL must open logged out and its code must be public (e.g. merged into the public repo; PR #35 is open from the agronomist's fork).

## 5. Detailed Project Description

> *Official prompt:* "What exactly does it do? How does it work? What benefits does it have? What do you hope to achieve? What tools, coding languages, hardware, or software did you use".

**Paste:**

`[PENDING D-001: product name]` — `[PENDING D-001: one-line statement]`

**The decision.** In the Planalto Médio of Rio Grande do Sul, Brazil, soybean fills the summer and the farmer chooses what follows it in winter: wheat (income, but exposed to the weather), a cover crop such as black oat (protects the soil, costs money, earns nothing directly) or fallow (no cost, no protection). The choice, and the credit that funds it, comes months before winter. Wheat is where El Niño hurts: in 18 municipalities around Cruz Alta, 1981–2025, wheat yield fell below 75% of its own trend in 53.3% of municipal harvests in El Niño winters (73 of 137), against 3.5% in La Niña winters (3 of 86) and 17.2% in neutral winters. These are 8 El Niño and 5 La Niña winters, not 223 independent cases (neighbouring municipalities fail together), so the evidence rests on a winter-level permutation test (p = 0.003); the direction holds in all 12 robustness variants (threshold 70/75/80%, linear or quadratic trend, 1981–2025 or 1990–2025). In 2023 wheat fell below the threshold in 14 of the 18 municipalities. NOAA issued its El Niño Watch on 13 April 2023 and the El Niño Advisory on 8 June 2023; regional wheat operating credit that year was stable (full-year value −3.1% in real terms).

**What it does today (public).**
1. **Site page for Cruz Alta** (`/sites/cruz-alta`): the NASA POWER record (January 1981 to October 2026) as recent monthly rain and temperature, climate indices for 1991–2020 (heat and frost days, growing degree-days, FAO-56 reference evapotranspiration, water deficit, extreme rain), a metric/imperial switch, and the result of the team's ground check against local stations. Every underlined number opens its source: dataset, version, access date, data type (modeled, computed, satellite-observed) and limitations.
2. **Data & Methods page** (`/data-methods`): one section per method, with references and limitations, including the El Niño–wheat analysis, heavy rain by ENSO phase, forecast skill, the bare-soil calendar, the 2026 season so far and "storms meet soil"; the full list of datasets and licences; and the log of AI use.
3. **Site data files** (`data/sites/cruz-alta/output/`), validated in CI against versioned data contracts: the NASA POWER series and indices; heavy-rain days in September–November by ENSO phase from three sources; the February-forecast scorecard; a calendar of cropland without green cover; a 2023 replay (NOAA alerts, the ZARC sowing window, wheat failures, credit); and the 2026 season so far.
4. **Two reproducible analyses**, each rerun from the public sources with one command, with question, criterion, results, robustness and limitations: `analysis/enso-wheat` and `analysis/storms-bare-soil`.

`[IF PUBLISHED: **The farmer-facing app** (built with the team's agronomist) puts the evidence for the winter choice on one screen for Cruz Alta: (1) **This winter** — the chance of El Niño for next June–August from dated forecasts (NOAA CPC/IRI official, IRI model-based), side by side, never a yes/no, next to what El Niño winters did to wheat here, and an open "arithmetic, not a model" scenario; (2) **The NASA link** — heavy-rain days at wheat harvest by ENSO phase, IMERG first, with NASA POWER and the rain gauge as checks; (3) **How often the February forecast got the winter right** — hit rate, El Niño caught, false alarms, each against "always neutral"; (4) **Rotations** — soybean–wheat, soybean–cover crop and soybean–fallow side by side: soil effect, weather risk, and money only where a source gives a value, with buttons that reorder the options by the farmer's priority (soil, cash, risk); (5) **Bare soil** — when cropland has no green, and the straw each rotation leaves in November; plus climate, soil, cover crops, land use, an NDVI map and a sources page that splits NASA, partner (ESA) and other data. Every number carries a tag that opens its source.]`

**How it works.**
- **Pipeline** (`services/science`, Python 3.12). Downloads daily NASA POWER data for each site point (1981 to the last complete month), keeps the raw response with its request URL and access time, aggregates to monthly values (a month gets a value only when every day is valid; gaps stay empty and are listed), computes reference evapotranspiration with FAO-56 Penman-Monteith and derives climate indices (ETCCDI-style heat and frost days, growing degree-days, water deficit as ET0 minus rain, extreme rain above the 95th percentile). A second command builds the complement files: it reads GPM IMERG through the POWER API, the NOAA Oceanic Niño Index, the NASA GMAO GEOS-S2S and IRI forecast archives, the Sentinel-2/MODIS cover tables, an ANA rain gauge and IBGE yields. Every value written carries a provenance record, including which owners to credit (NASA, partner agency, other public source). `fieldshift validate --all` checks every data file in CI.
- **Data contracts.** Pydantic models export JSON Schema and TypeScript types; CI fails if pipeline and app drift.
- **Web app** (Next.js, static). Reads the data files at build time and shows each number with its source and data type; no number is typed by hand into the app.
- **Analyses** (`analysis/`). Standalone scripts that download the sources at run time, write small results with access times, and reuse the pipeline's loaders by import; each result file records where its numbers came from.
- **Validation.** NASA POWER and IMERG were checked against INMET station A853 and ANA rain gauge 2853015 at Cruz Alta: daily rain correlation with A853 is 0.85 for IMERG and 0.78 for POWER (0.92 monthly). POWER smooths heavy rain and, in January–February, its daily maximum temperature runs +1.84 °C above the station since about 2019 (+0.41 °C in 2008–2018), so we do not claim a rise in hot days. The September–November heavy-rain days recomputed by the storms analysis match the published file in every year for all three sources.

**What the data say (verified).**
- **Heavy rain at harvest, by ENSO phase** (mean days per year with ≥ 50 mm, September–November, Cruz Alta): NASA GPM IMERG 4.4 / 2.6 / 1.4 (El Niño / neutral / La Niña, 1998–2025); ANA rain gauge 4.0 / 2.2 / 1.5 and NASA POWER 1.9 / 1.1 / 0.9 (1982–2025). All three rank the phases the same way; POWER counts about half as many days because a 0.5° cell smooths storms.
- **Forecasts in February:** none beats "always neutral" on the winter's ENSO phase. NASA GMAO GEOS-S2S (NMME, 1982–2022): hit rate 0.56 against 0.71, 4 of 7 El Niño winters caught. The official NOAA CPC/IRI outlook ties "always neutral" (0.75, 2014–2025), but its El Niño probability does rise in the right years: on average 47% in winters that became El Niño against 23% in the others. That is why only odds are shown.
- **Storms meet soil:** cropland without green cover (Sentinel-2 10 m, NDVI < 0.25) peaks at 67.6% (1–15 November) and 75.6% (16–30 November), median 2019–2025; 1–15 November is the most exposed half-month (a ≥ 50 mm day in 44% of years, 95% interval 27–63%). In 2019–2025, 5 of 57 IMERG heavy-rain days with a scene in the same half-month fell when at least half of the cropland had no green, all in November. "No green" is not "bare": in November much of it is straw. With the half-lives measured in the Cruz Alta no-till trial (black oat 124 days, wheat 139 days), black oat desiccated in September–October still leaves 3.1–8.2 t/ha on 1 November, harvested wheat 2.6–4.1 t/ha, and winter fallow no winter straw — arithmetic from measured half-lives, not a field measurement.
- **2026 so far:** 1 September–11 November 2026, NASA POWER at Cruz Alta: 935 mm and 5 days with ≥ 50 mm (189 mm on 4 November), against 537 mm and 1.2 days in an average El Niño year and 405 mm and 1.0 day in neutral years over the same days (1998–2025); 2023 had 840 mm and 3 days. NOAA's ONI for August–October 2026 is +2.46 °C. Emater/RS-Ascar reports that intense rain interrupted the 2026 wheat harvest; the official 2026 yield is not published yet.

**Benefits.**
- Puts the El Niño signal, its NASA evidence and each forecast's track record in front of the farmer and agronomist **before** the winter choice and its credit, instead of after the harvest.
- Honest about uncertainty: odds and track records, never certainty; every limitation is written next to the number.
- Reproducible and open: anyone can rerun the analyses from public endpoints; every number traces to its source.
- Site-agnostic pipeline: a new point needs one `site.yaml` file; NASA POWER and IMERG are global.

**What we hope to achieve.** That the winter choice in southern Brazil's soybean belt is made with the season's odds and the soil in view, with farmers, agronomists and cooperatives using the same evidence before credit is signed. Next steps: the agronomist sets crop thresholds per site; more municipalities and sites with the same pipeline; the signal matters beyond Brazil too — Rio Grande do Sul, Argentina, Uruguay and Australia together grow wheat on about 10% of the world's wheat area, and in Uruguay El Niño brings the same excess-rain mechanism as in southern Brazil (in Australia it means drought instead).

**Limitations and uncertainty.**
- NASA POWER and IMERG values are **regional signals**: one grid cell around the site point (POWER meteorology about 0.5° × 0.625°, radiation 1° × 1°; IMERG 0.1°), not field measurements, not downscaled.
- POWER values are **modeled** (reanalysis-based); POWER soil wetness is a 0–1 fraction of saturation from a land-surface model, not volumetric soil moisture. `EVPTRNS` is not used; ET0 is computed with FAO-56. Months with a missing day are left empty.
- The heat threshold (35 °C) and growing degree-day base (10 °C) are generic defaults until the agronomist sets them per crop; the water deficit is a climate indicator, not a soil water balance.
- The El Niño–wheat result rests on **8 El Niño and 5 La Niña winters**, and four winters (1982, 2002, 2015, 2023) carry most of the losses. Yield is municipal (IBGE), the trend is a simple fit, and the association is statistical, not an agronomic cause.
- Forecast samples are tiny (2 to 7 El Niño winters per source); the scorecard scores the ocean forecast, not farm outcomes. The ONI is revised by NOAA.
- NDVI cannot separate straw from bare soil; the straw clock uses half-lives from one long-term trial and initial straw from other sites; management windows are scenarios. Seven years of Sentinel-2 against 25 years of rain; 50 mm is a convention, not an erosion threshold.
- IMERG through the POWER API is reported in UTC days without its run (Early, Late, Final) and stopped on 14 September 2026 at access, so the 2026 window uses NASA POWER and has no ground check yet.
- Full list, per method: Data & Methods page (field 4).

**Use statement.** This tool supports, and does not replace, the judgment of farmers and agronomists. It explores options; it does not prescribe actions or promise yields, profit or carbon credits.

**Tools, languages and software.** Python 3.12 (uv, pydantic, httpx, PyYAML, NumPy, Matplotlib, xarray/netCDF4, pytest, Ruff); TypeScript, Next.js 16, React 19, Tailwind CSS 4, shadcn/Radix UI; Vitest, Testing Library and Playwright; GitHub Actions CI with gitleaks secret scanning; Vercel hosting. `[IF PUBLISHED: The farmer-facing app also uses Leaflet with OpenStreetMap tiles, and its NDVI map was prepared with Google Earth Engine.]` No hardware. Full list with versions and licences in field 8.

**Notes (do not paste):**
- Sources of each number: ENSO–wheat, 2023 alerts and credit: `analysis/enso-wheat/README.md`. Heavy rain by phase: `enso-rain-signal.json`. Forecast skill: `forecast-scorecard.json` (`scores`), official 47%/23%: `analysis/enso-wheat/README.md`. Storms and straw: `analysis/storms-bare-soil/README.md`. 2026: `now-2026.json`. Ground check: `content/methods/satellite-vs-ground.md` and the live site page. "About 10% of the world's wheat area" (AR + UY + AU + BR, FAOSTAT 2024) and the Uruguay/Australia mechanisms: team workspace research of 2026-11-14 (FAOSTAT, Díaz de Ackermann et al. 1998, Potgieter et al. 2005), not in the public repo — drop the sentence if the team prefers only public-repo numbers.
- The `[IF PUBLISHED]` app description follows the agronomist app's README and its home screen on `localhost:3200` (2026-11-14 ~22h BRT). Before keeping it, open the published URL and delete any screen that is not there.

## 6. Use of Super Intelligence (SI)

> *Official prompt:* "Did you utilize any Super Intelligence (SI) tools and software in preparing your solution? If yes, how did you use them?" The guide says this answer is for data collection and is not shown to judges; SI indicators inside the project are.

**Paste:**

**Answer: Yes.**

We used SI tools as assistants for research, code, documentation, analysis and review. **Origin of the idea, stated as it happened:** the team generated the starting ideas at a human ideation meeting on 14 November (transcribed in the team workspace), and the farmer on the team described the real winter decision in an interview. At the team lead's request, an SI tool (Claude Code) then helped **compare and synthesize concepts from those human ideas** and from data the team had verified, and drafted the pitch text. The team chose the final concept and wrote the one-line statement in its own words (decision record `D-001` in `DECISIONS.md`). `[PENDING D-001: names and time of the decision; quote the human ideas the concept builds on (e.g. analog years); confirm the wording with the Local Lead if possible]`

- **Code (SI-generated, human-directed):** Claude Code (Anthropic) wrote most of the code in the repository under the team's instructions: NASA POWER ingestion and monthly aggregation, FAO-56 ET0, climate indices and data validation, the complement datasets (GPM IMERG via POWER, forecast archives, bare-soil calendar, 2023 replay, 2026 season so far), the data contracts and their code generation, the web app pages and components (including the Cruz Alta site page), the two analysis folders, the tests and the CI workflow. Every SI-assisted file carries an "SI-assisted" header naming the tool and the reviewer, and every SI-assisted pull request has a row in `SI-USAGE.md`. Codex (OpenAI) was used to review planning documents and the pitch draft. `[IF PUBLISHED: The farmer-facing app was also built with Claude Code; its own SI log is in its repository.]`
- **Analyses (SI-run, human-directed):** Claude Code ported the team's verification scripts to English and ran them and the new analyses against the public sources. The complement datasets and the "storms meet soil" analysis were requested by the team lead; their concept was synthesized with Claude Code from the team's research at his request, and the team chose them.
- **Text (SI-generated, human-directed):** Claude Code and Claude (Anthropic) drafted the documentation (README, methods, glossary, related work, resources and licences, analysis write-ups, this submission text) and the team's internal planning documents. Research used Claude Code with the Firecrawl CLI and web search to read official pages; facts were checked against their sources and the sources are cited.
- **Data:** no number shown in the project is produced by an SI model. Numbers come from NASA, ESA Copernicus and other public sources through deterministic code (FAO-56, counts, percentiles, permutation tests, exponential decay) or are transcribed from cited publications; SI wrote and ran that code. Data files produced this way are declared in `SI-USAGE.md` and in each dataset's `provenance.json`.
- **Images:** the app icon (`icon.svg`, three bars, SVG code written by Claude Code) and the static chart of the storms analysis (drawn by a Matplotlib script written by Claude Code from the analysis results) are declared in `SI-USAGE.md`. No NASA logo, flag or mission insignia appears in any SI-generated content.
- **Demo:** `[CHOOSE]`
  - *Variant A — synthetic voice:* the demo video uses an **SI-generated (synthetic) narration voice** (`[PENDING: tool name]`) and **illustrative cards** (`[PENDING: tool name, or "made by hand"]`). The voice is acknowledged in the video's description, in its file metadata and in an on-screen caption; every SI-generated card carries a visible "AI-generated" watermark, and cards that do not show real data are labeled "Illustrative".
  - *Variant B — captions only:* the demo has **no narration voice**; it uses burned-in English captions over screen recordings of the real app. `[PENDING: if any card or image in it was generated with SI, name the tool; each such card carries a visible "AI-generated" watermark — otherwise write "No SI-generated images or audio are used in the demo."]`
- **Human review:** `[PENDING: names of the people who reviewed SI-generated code and text — SI-USAGE.md column "Reviewed by"]`

Full log with dates, tools and files: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/SI-USAGE.md

**Notes (do not paste):** the origin-of-the-idea paragraph is the text approved in PR #40, unchanged. Variant B removes the audio-acknowledgement duty (preflight R4/C5) only if the final video really has no synthetic voice.

## 7. NASA Data

> *Official prompt:* "Provide specific details about what NASA data and resources you used. To be eligible for a Global Award, you must use at least one NASA data or resource."

**Paste:**

**1. NASA POWER (Prediction Of Worldwide Energy Resources), NASA Langley Research Center** — https://power.larc.nasa.gov/
- **Product:** POWER Daily API, version 2.10.3, community `AG` (agroclimatology), point endpoint; accessed 2026-11-14.
- **Variables:** `T2M`, `T2M_MAX`, `T2M_MIN`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `PRECTOTCORR`, `PS`, modeled soil wetness `GWETTOP`, `GWETROOT`, `GWETPROF`, and modeled land evaporation `EVLAND`.
- **Upstream NASA products (served through POWER, not accessed directly):** MERRA-2 reanalysis (meteorology and soil wetness, about 0.5° × 0.625°) and CERES SYN1deg (solar radiation, 1° × 1°), per the [POWER methodology](https://power.larc.nasa.gov/docs/methodology/).
- **Period:** daily, 1 January 1981 to 31 October 2026 for the Cruz Alta site series (radiation valid from 1984); `PRECTOTCORR` through 11 November 2026 for the 2026 season so far.
- **Used for:** the monthly climate series and FAO-56 reference evapotranspiration shown on the site page; climate indices (heat and frost days, growing degree-days, water deficit, extreme rain); the check series of heavy-rain days by ENSO phase (1982–2025) and of the storms analysis; the 2026 season so far (935 mm and 5 days ≥ 50 mm, 1 September–11 November).
- **Citation** ([POWER referencing guide](https://power.larc.nasa.gov/docs/referencing/)): "The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division." "The data was obtained from the POWER Project's Daily 2.10.3 version on 2026/11/14."

**2. NASA GPM IMERG (Integrated Multi-satellitE Retrievals for GPM), NASA GES DISC** — https://gpm.nasa.gov/data/imerg
- **Product:** daily precipitation `IMERG_PRECTOT`, read through the NASA POWER Daily API v2.10.3 in UTC days (POWER does not state the IMERG run; the product of record is IMERG Final V07). 0.1° grid. Accessed 2026-11-14.
- **Period:** 1998–2025 for heavy rain by ENSO phase; 2001–2025 for the storms analysis. For 2026, POWER served IMERG only up to 14 September 2026 at access (the GES DISC copies need an Earthdata login, which the pipeline does not use), so the 2026 window is reported with NASA POWER.
- **Used for:** the main heavy-rain signal — mean September–November days with ≥ 50 mm at Cruz Alta: 4.4 (El Niño), 2.6 (neutral), 1.4 (La Niña); heavy-rain days by half-month in "storms meet soil" (1–15 November: 44% of years); ground check against INMET A853 (daily r = 0.85).
- **Citation:** Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., & Tan, J. (2023). GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07 [Data set]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/GPM/IMERG/3B-HH/07 — served by NASA POWER (citation of item 1 also applies).

**3. NASA MODIS Vegetation Indices, MOD13Q1 (Terra) and MYD13Q1 (Aqua), version 061, NASA LP DAAC** — https://lpdaac.usgs.gov/products/mod13q1v061/ · https://lpdaac.usgs.gov/products/myd13q1v061/
- **Product:** NDVI, 250 m, 16-day composites; valid observations (reliability 0 or 1) of pixels with at least 80% cropland, read through the Microsoft Planetary Computer STAC collection `modis-13Q1-061` (anonymous access).
- **Period:** 2019–2025, grouped by fortnight.
- **Used for:** the MODIS line of the bare-soil calendar and of the storms chart, beside Sentinel-2 (MODIS shows far less "no green" than Sentinel-2 — about 12% against 76% in late November — because the 16-day composite keeps the greenest day).
- **Citation:** Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 [Data set]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/MODIS/MOD13Q1.061 · Didan, K. (2021). MODIS/Aqua Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 [Data set]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/MODIS/MYD13Q1.061

**4. NASA GMAO GEOS-S2S seasonal forecasts** — NMME files: https://ftp.cpc.ncep.noaa.gov/NMME/ENSO/NASA_GEOS5v2/
- **Product:** ensemble-mean Niño-3.4 forecasts of the NMME member `NASA_GEOS5v2` (GEOS-S2S), February starts, target June–August, 1982–2022 (hindcasts before 2011); and the "NASA GMAO" line of the IRI ENSO forecast plume, February issues 2003–2025. Accessed 2026-11-14.
- **Used for:** the forecast scorecard — ENSO-phase skill of February forecasts for the winter: GEOS-S2S hit rate 0.56 against 0.71 for "always neutral" (41 years), 4 of 7 El Niño winters caught. Only skill metrics and the per-year February values of the NASA member are committed.
- **Citation:** Molod, A., et al. (2020). GEOS-S2S Version 2: The GMAO High-Resolution Coupled Model and Assimilation System for Seasonal Prediction. *Journal of Geophysical Research: Atmospheres*, 125(5). https://doi.org/10.1029/2019JD031767 · NMME: Kirtman, B. P., et al. (2014). The North American Multimodel Ensemble. *Bulletin of the American Meteorological Society*, 95(4), 585–601. https://doi.org/10.1175/BAMS-D-12-00050.1

`[IF PUBLISHED: **5. NASA SRTM GL1** (Shuttle Radar Topography Mission, 30 m), read through the Open Topo Data API at 25 points about 5 km apart, for the elevation range around the site in the farmer-facing app — https://www.opentopodata.org/datasets/srtm/ (SRTM: NASA/USGS, public domain). The farmer-facing app also reads MOD13Q1 NDVI 2000–2025 through Google Earth Engine for its NDVI map.]`

All NASA data used are open, with no restriction on use ([NASA Earth science data use guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance)). Dataset names appear as plain text; no NASA logo or insignia is used.

**Notes (do not paste):**
- Access dates/times from `data/sites/cruz-alta/output/provenance.json`: POWER 2026-11-14 19:29 BRT, IMERG 20:39, MODIS 15:00, NMME GEOS 19:46.
- Not listed because no public code or analysis reads them: MERRA-2/CERES directly (only through POWER), SMAP, GLDAS, GRACE, HLS, VIIRS, MCD12Q1/Q2, MOD16, ECOSTRESS, GFSAD, SRTM/NASADEM (public repo), OPERA, GIBS, NEX-GDDP (all `candidate` in `RESOURCES.md`). Copernicus DEM: not used anywhere (grep of the repo and the agronomist app).
- The GMAO subseasonal page in `RESOURCES.md` (`gmao.gsfc.nasa.gov/cc/research/subseasonal/`) now shows a login form, so it is not linked here (drift, see preflight).

## 8. Space Agency Partner Data and Other References

> *Official prompt:* "List all of the data, resources, and tools used in your project. Resources should include any code, text, and images (even if they are open source or freely available)".

**Paste:**

**Space Agency Partner data (ESA, Copernicus)**
- **Copernicus Sentinel-2 L2A**, 10 m, tile 22JBP, one scene per fortnight, 2019–2025, read through the Element 84 Earth Search STAC (https://earth-search.aws.element84.com/v1, collection `sentinel-2-l2a`): share of cropland with NDVI < 0.25 per fortnight (bare-soil calendar and storms analysis). Terms: Copernicus Sentinel Data Legal Notice (free use with attribution). Credit: "Contains modified Copernicus Sentinel data [2019-2025]."
- **ESA WorldCover 2021 v200**, 10 m, class 40 (cropland), mask of the Sentinel-2 analysis — https://esa-worldcover.org/ — CC BY 4.0. Credit: "ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium."

**Other data** (each used in the public code, data files or analyses; licence or terms as stated by the provider)
- **NOAA Climate Prediction Center** — Oceanic Niño Index (https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt, ERSSTv5): ENSO phase of each year; ENSO Diagnostic Discussions (March–June 2023; 12 November 2026) and official probabilities. US government work, public domain.
- **NOAA CPC North American Multi-Model Ensemble (NMME)** — Niño-3.4 forecasts of 6 models, 1982–2022, for the skill metrics of `analysis/enso-wheat` (https://www.cpc.ncep.noaa.gov/products/NMME/); cite Kirtman et al. (2014). Only metrics are committed (no per-year values of non-NASA models).
- **IRI, Columbia University** — ENSO forecast plume, objective probabilities and official CPC/IRI table, February issues 2003–2026, read from the archive figures (https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/). Page licence CC BY 4.0.
- **IBGE** (Brazilian Institute of Geography and Statistics) — Municipal Agricultural Survey (PAM), SIDRA table 1612: wheat and soybean yield of 18 municipalities 1981–2025, and state/national wheat and soybean area and production; Census of Agriculture 2017, SIDRA table 6957 (farms with wheat); localities API and municipal mesh 2022 (site point and municipality codes). https://sidra.ibge.gov.br · https://servicodados.ibge.gov.br — public federal data; cite IBGE.
- **Banco Central do Brasil (BCB)** — SICOR rural credit data matrix (`CusteioMunicipioProduto`, wheat operating credit of 18 municipalities, 2013 →), https://dadosabertos.bcb.gov.br/dataset/matrizdadoscreditorural — **ODbL** (the derived `results/credit_sicor.json` stays under ODbL); IPCA from SGS series 433 (deflator); Proagro data matrix (wheat claims in Rio Grande do Sul, 2023 contracts), https://www.bcb.gov.br/estabilidadefinanceira/proagro.
- **ANA** (Brazil's National Water and Sanitation Agency), HidroWeb — daily rain of gauge 2853015 (Três Capões), 1982–2025, legacy web service `HidroSerieHistorica` (https://www.snirh.gov.br/hidroweb/): ground check of heavy-rain days. Public federal data; cite ANA.
- **INMET** (Brazil's National Institute of Meteorology) — automatic stations A853 (Cruz Alta), A883 and A886, https://portal.inmet.gov.br/dadoshistoricos: ground check of NASA POWER and IMERG (results on the site page and in Data & Methods). Public federal data; cite INMET.
- **UCSB Climate Hazards Center, CHIRPS** — v3.0 monthly and daily CHIRPS through SERVIR ClimateSERV, in the satellite-vs-ground comparison of Data & Methods (Funk et al. 2026, https://doi.org/10.1038/s41597-026-07096-4).
- **MAPA** (Brazil's Ministry of Agriculture), ZARC agricultural climate risk zoning, 2022/2023 risk table: wheat sowing window at Cruz Alta in the 2023 replay (https://dados.agricultura.gov.br/dataset/tabua-de-risco-zoneamento-agricola-de-risco-climatico) — Creative Commons Attribution.
- **CONAB** — production costs (wheat at Cruz Alta, 2023 margin, transcribed), https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao — cite CONAB.
- **Embrapa** — De Mori, C. (2007), Comunicado Técnico 207 (black oat cover-crop cost), https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/852400/1/pco207.pdf; Santos, H.P. et al. (ed.) (2019), *Sistemas de produção para cereais de inverno: três décadas de estudos* (initial straw), https://www.alice.cnptia.embrapa.br/alice/bitstream/doc/1111855/1/ID446652019LVSistemasdeproducao.pdf — cite Embrapa.
- **Emater/RS-Ascar**, Informativo Conjuntural n. 1942 (22 Oct 2026) and n. 1945 (12 Nov 2026), short quotes on the 2026 wheat harvest, https://www.emater.tche.br/site/info-agro/informativo_conjuntural.php; 2025 harvest progress as reported by Revista Cultivar (6 Nov and 11 Dec 2025).
- **Atlas Digital de Desastres no Brasil** (MIDR/SEDEC), consolidated CSV v1.1, drought records 1991–2025, fetched at run time by `analysis/enso-wheat` (https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml). No licence declared: derived counts are quoted, not committed.
- **Access services:** Element 84 Earth Search (Sentinel-2 on AWS), Microsoft Planetary Computer (MODIS STAC), NOAA CPC FTP (NMME files), ANA HidroWeb web service, IBGE SIDRA API, BCB Olinda OData.
- `[IF PUBLISHED: Farmer-facing app, additional sources: ISRIC SoilGrids 2.0 (CC BY 4.0); MapBiomas Brazil Collections 11 and 9 (CC BY 4.0); IBGE IPCA, SIDRA table 1737; Open Topo Data API (SRTM); OpenStreetMap map tiles (© OpenStreetMap contributors, ODbL); Google Earth Engine (MODIS NDVI map); IRI objective ENSO probabilities issued October 2026; NOAA CPC/IRI official probabilities of 12 November 2026.]`

**Methods and literature**
- Allen, R. G., Pereira, L. S., Raes, D., Smith, M. (1998). *Crop evapotranspiration — Guidelines for computing crop water requirements.* FAO Irrigation and Drainage Paper 56. https://www.fao.org/4/x0490e/x0490e00.htm
- Zhang, X. et al. (2011). Indices for monitoring changes in extremes based on daily temperature and precipitation data. *WIREs Climate Change* 2, 851–870. https://doi.org/10.1002/wcc.147 — and ETCCDI core indices, https://etccdi.pacificclimate.org/list_27_indices.shtml
- McMaster, G. S., Wilhelm, W. W. (1997). Growing degree-days: one equation, two interpretations. *Agricultural and Forest Meteorology* 87, 291–300. https://doi.org/10.1016/S0168-1923(97)00027-0
- Hyndman, R. J., Fan, Y. (1996). Sample quantiles in statistical packages. *The American Statistician* 50(4), 361–365. https://doi.org/10.1080/00031305.1996.10473566
- Wilks, D. S. (2011). *Statistical Methods in the Atmospheric Sciences*, 3rd ed., ch. 8 (forecast verification). https://doi.org/10.1016/C2017-0-03921-6
- Tucker, C. J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment* 8, 127–150. https://doi.org/10.1016/0034-4257(79)90013-0
- Campos, B. H. C. et al. (2011). Long-term C-CO2 emissions and carbon crop residue mineralization in an oxisol under different tillage and crop rotation systems. *Revista Brasileira de Ciência do Solo* 35(3). https://doi.org/10.1590/S0100-06832011000300017 — straw half-lives at Cruz Alta.
- Aita, C., Giacomini, S. J. (2003). Decomposição e liberação de nitrogênio de resíduos culturais de plantas de cobertura de solo solteiras e consorciadas. *Revista Brasileira de Ciência do Solo* 27(4), 601–612. https://www.redalyc.org/pdf/1802/180214026004.pdf
- Molod, A. et al. (2020), GEOS-S2S Version 2, https://doi.org/10.1029/2019JD031767; Kirtman, B. P. et al. (2014), NMME, https://doi.org/10.1175/BAMS-D-12-00050.1; Huffman, G. J. et al. (2023), IMERG V07, https://doi.org/10.5067/GPM/IMERG/3B-HH/07; Didan, K. (2021), MOD13Q1/MYD13Q1 V061 — full entries in field 7.
- Funk, C. et al. (2026). CHIRPS v3. *Scientific Data* 13, 718. https://doi.org/10.1038/s41597-026-07096-4
- Related work and its sources: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/content/related-work.md
- Method references (one file per method): https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/content/methods

**Code libraries and tools** (versions pinned in `package-lock.json` and `services/science/uv.lock`; analysis-only libraries pinned in the `uv run --with` commands)

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
| NumPy (analysis) | 2.5.4 | BSD-3-Clause |
| Matplotlib (analysis figure) | 3.10.7 | Matplotlib License (PSF-based) |
| xarray + netCDF4 (analysis, NMME files) | as resolved, recorded in `analysis/enso-wheat/results/run_info.json` | Apache-2.0 / MIT |
| pytest | 9.2.0 | MIT |
| Ruff | 0.17.5 | MIT |
| gitleaks | 8.30.1 | MIT |
| GitHub Actions | — | service terms |
| Vercel (hosting) | — | service terms |

`[IF PUBLISHED: Farmer-facing app libraries: Next.js 16.4.6, React 19.3.0, Tailwind CSS 4.3.3, Leaflet 1.9.x (BSD-2-Clause), TypeScript 5, ESLint 9; Python scripts with the Google Earth Engine API.]`

**Fonts and images**
- Geist and Geist Mono fonts (Vercel), loaded through `next/font/google` — SIL Open Font License 1.1.
- App icon: `apps/web/src/app/icon.svg`, three geometric bars drawn as SVG code for this project with Claude Code (declared in `SI-USAGE.md`); no third-party mark, no NASA logo.
- Chart `analysis/storms-bare-soil/results/storms-bare-soil.png`: drawn by the team's Matplotlib script (written with Claude Code) from the analysis results; credits NASA, ESA Copernicus and ANA in its footer; no logo.
- App screenshots in `apps/web/docs/screenshots/`: captures of our own app.
- `[PENDING: every image, card, icon and music track used in the slides or demo video, with source and licence]`

**SI tools** (details in field 6): Claude Code and Claude (Anthropic), Codex (OpenAI), Firecrawl CLI. `[PENDING: voice and image tools used in the demo, if any — see field 6 variant]`

**Notes (do not paste):**
- Every dataset row of `RESOURCES.md` whose "Feeds" column names public code, a public data file or a public analysis is here; `candidate` rows with "—" are not, because nothing reads them. Rows marked "analysis only (fieldshift-hq)" are included only where their results are published on Data & Methods (INMET, CHIRPS).
- Licence gaps that are **not** cosmetic (preflight R7/R8): ANA daily rain is committed (`input/ana-2853015-sep-nov-daily.csv`) while `RESOURCES.md` says "In git? check"; CONAB and NMME are "check"; the Atlas licence is not declared (only quoted counts). The page lists them honestly; the team decides whether that is enough.
- Copernicus DEM is not used (no code or analysis reads it); do not add it.

---

## Final declarations (checkboxes on the form)

- [ ] Terms and Conditions and Privacy Policy accepted.
- [ ] "I confirm that the submitted project represents my team's original work and that all external resources including code, text and images (even if they are open source or freely available) used in the project are listed in the References field" — tick only after field 8 has no `[PENDING]` or `[IF PUBLISHED]` left.
