# Submission page draft

> **SI-assisted:** written with Claude Code (Anthropic) from `RESOURCES.md`, `SI-USAGE.md`, `content/methods/`, `analysis/*/README.md`, `data/sites/cruz-alta/output/*.json`, the norm texts (IN SPA/MAPA 2/2025, Portaria SPA/MAPA 209/2026, Resolução CGSR 111/2026), the team's verified numbers and the official 2026 Project Submission Guide; human review pending. The product **name** and the **one-line statement** are not written here (rule C1): they stay as placeholders for the team (list below).

Owner: FLIGHT. This is the text to paste into the Space Apps project page. Fields are in the official order of the [Project Submission Guide](https://www.spaceappschallenge.org/resources/project-submission-guide/) (version of 2026-11-13, read 2026-11-14). Compliance status of each item: [`preflight.md`](preflight.md). Demo rules and script skeleton: [`demo-plan.md`](demo-plan.md).

**Direction:** the adopted direction of 15 November (team lead, after the pivot jury): the app compares three winter strategies after soybean (a wheat-like cereal every winter, a cover crop every winter, or alternating; fallow only as a reference) and adds a **ZarcNM pre-check** read with Landsat/HLS and NASADEM. The team confirms it in D-001.

## Before submitting, fill (only people can)

Every other bracket has been removed. These six placeholders remain, each in capitals inside square brackets where it appears:

1. `[PRODUCT NAME]` — the team (D-001): field 1 and the first line of field 5.
2. `[ONE-LINE STATEMENT]` — the team, in its own words (D-001): first line of fields 2 and 5.
3. `[MEMBERS]` — FLIGHT, logged in: the 6 names exactly as on the Members tab (table below).
4. `[REVIEWERS]` — the people who reviewed SI-generated code and text (field 6; `SI-USAGE.md` column "Reviewed by").
5. `[DEMO LINK]` — the uploaded demo video, tested logged out (field 3).
6. `[APP SOURCE URL]` — the public repository of the farmer-facing app, once published (fields 4 and 6).

## How to use this draft

- Paste only the text **inside each "Paste" block**. "Notes (do not paste)" are for the team.
- **Links (team lead's decision, 15 November):** https://fieldshift-spaceapp.vercel.app is now the **farmer-facing app** (the product; routes `/start`, `/`, `/soil-level`, `/rotations`, `/my-farm`, `/globe`, `/sources`, `/about`). The earlier pipeline pages (`/data-methods`, `/glossary`, `/sites/cruz-alta`) stay online at https://fieldshift-data.vercel.app. The farmer-facing app's **source code is still private**: do not link its repository; field 4 says "app source to be published" with `[APP SOURCE URL]`.
- The Landsat/HLS analysis (PR #54, `analysis/residue-landsat`) is merged (`7b7ca4f`), so its numbers are written in the present tense.
- Field 6 demo variant chosen: captions only, no synthetic voice (round 5).
- Tense rule: present tense only for what is on `main` or published. Never leave a bracket in the submitted page.

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
| Members (max 6, all confirmed at the same Local Event, none on the waitlist) | `[MEMBERS]` | to verify |

---

## 1. Project Name

> *Official prompt:* "What is the name of your project?"

**Paste:**

`[PRODUCT NAME]`

## 2. High-Level Project Summary

> *Official prompt:* "What did you develop? How does it address the challenge? Why is it important?"

**Paste:**

`[ONE-LINE STATEMENT]`

Every year, after the soybean harvest, a farmer in Rio Grande do Sul, Brazil, chooses what the field does in winter. We compare three strategies: a **wheat-like cereal every winter**, a **cover crop every winter** (black oat with vetch), or **alternating** the two. Fallow (no winter crop) is kept only as a reference: NASA HLS shows it on just 0.3–0.6% of Cruz Alta's cropland in each winter of 2020–2025. Since the 2026/27 season that choice also counts for crop insurance. Under Brazil's **ZarcNM** zoning (Portaria SPA/MAPA 209/2026 for soybean in Rio Grande do Sul), a soybean field is placed in one of four soil-management levels, NM1 to NM4, and in the 2026 pilot the federal subsidy on the soybean insurance premium goes from 20% at NM1 to 40% at NM4 (Resolução CGSR 111/2026) — a small pilot, with R$ 1 million for soybean shared by four states. The rule behind the levels (IN SPA/MAPA 2/2025) asks for field slope from 30 m products "such as NASADEM or equivalent" and for NDVI and NDTI time series at 30 m, recommending **Landsat, Sentinel-2 or the harmonized HLS product**; MODIS is accepted for fields over 100 ha.

We developed an open, reproducible **pre-check** of the winter strategies against that published rule, for Cruz Alta. It implements the rule's indicator table and override rules in tested code, and estimates the three indicators that depend on the winter and that satellites and agronomy can read — years without tillage, straw cover before sowing and crop diversity. The other three indicators need a soil test, and contour sowing has to be confirmed on the field, so the result is a range, never a class: if the soil tests reach the top level, a cover crop every winter lands in **NM3–NM4** (35–40% subsidy) and a wheat-like cereal every winter in **NM2–NM3** (30–35%); alternating takes the wheat result in wheat winters and the cover result in cover winters; the fallow reference stays at **NM1–NM2** (20–30%). It tells the farmer whether the soil tests and paperwork are worth paying for; it does not replace the official classification. The farmer-facing app shows this as a "Soil level" screen next to the three strategies, with this winter's El Niño odds and the sources of every number.

The same pre-check runs on **every rural property of Cruz Alta** in the public rural-property registry (CAR): 1,263 of the 1,286 properties that the satellites can assess (98%) could reach NM3 or above on the satellite side if the soil test is at the top level and contour sowing is confirmed, and 1,284 have a mean slope of 3% or more. In the capital of no-till, the satellite side is rarely the bottleneck: **the soil analysis and the contour-sowing check are**.

NASA data carry the evidence. Forty years of NASA/USGS Landsat and NASA HLS imagery show what happened to Cruz Alta's cropland in early spring: the share with a probable bare-soil signature was 5.7% in the median year of 1984–1994 and 0.3% in the median year since 2005; the same cropland shows 20.0% on 4 November 1991 (Landsat 5) and 0.3% on 20 October 2026 (HLS). Most cropland without green cover in that window is now straw. NASA HLS also reads the winter of every 30 m field: in 2020–2025 a wheat-like cereal took 26–53% of the cropland and a cover crop 31–66%, and only 5.2% of the pixels kept the same path in all seven winters of 2020–2026. NASADEM slope puts 87.4% of the cropland at 3% or more, where the rule asks for contour sowing. NASA GPM IMERG shows why cover matters: September–November days with ≥ 50 mm of rain average 4.4 in El Niño years, against 2.6 in neutral and 1.4 in La Niña years (1998–2025), and in the first half of November, when 68% of the cropland has no green cover (mostly straw; Copernicus Sentinel-2), 44% of years have such a day. In 18 municipalities around Cruz Alta, wheat yield fell below 75% of its trend in 53% of municipal harvests in El Niño winters, against 3.5% in La Niña winters (8 and 5 winters, 1981–2025). In 2023, the last El Niño winter, the state's wheat output fell from 5.3 to 2.6 million tonnes; Rio Grande do Sul planted 1.16 million hectares of wheat in 2025, 46% of Brazil's.

Why it matters: the official rule rewards deep roots and drought resilience; our data add a second benefit, measured from space: in October–November, when the storms come, the field is protected by **straw**, not by a living plant (probable bare soil fell to 0.3% of the cropland; Landsat/HLS and Sentinel-2). It is a method, not a Cruz Alta anecdote: the same code, with no tuning, pre-checked every farm of a second municipality (Júlio de Castilhos: 1,527 farms assessed, 1,508 or 99% could reach NM3+ on the satellite side if the soil test agrees, in about 13 minutes), and the team's rotation-risk method passed all four pre-written criteria in 5 of 7 neighbouring municipalities (the other two passed 3 of 4). We also report what did not hold: two pre-registered tests found **no sign that winter cover made soybean more drought-resilient** (municipal yields before and after 1995, and 30 m canopy in the 2021/22 and 2022/23 droughts). And the rule is new: in Paraná's first pilot season (2025/26, 29 production areas, about 2,400 ha), only about 5% of the area reached NM4 and 57% was NM2 (MAPA, 17 November 2025). Everything is open: every number opens its source, every analysis reruns from public endpoints, and the tool supports, and does not replace, the judgment of farmers and agronomists.

**Notes (do not paste):**
- Norm wording checked on the extracted texts: IN 2/2025 item 6.3 "tais como NASADEM ou equivalentes de resolução superior"; item 6.4 "recomendando-se o uso dos satélites Landsat, Sentinel-2 ou produtos harmonizados (HLS)"; item 6.4-I accepts MODIS at 250 m for fields over 100 ha. Do **not** say the rule names NASA data "as proof".
- CGSR 111/2026 percentages and the R$ 1 million budget were read on the Legismap transcription, not on the DOU PDF; the four states (PR, SC, RS, MS) are from Agrolink.
- Sources: ZarcNM ranges `analysis/zarcnm-precheck/results/precheck.json`; every CAR property `analysis/farm-reports/README.md` ("Results") and `results/farm_reports.json`; winter paths and fallow share `analysis/rotation-fingerprint/README.md` ("Answer"); NASADEM slope `analysis/residue-landsat/results/nasadem_slope_classes.json`; drought nulls `analysis/drought-resilience/README.md` and `analysis/rotation-drought-test/README.md`; heavy rain `data/sites/cruz-alta/output/enso-rain-signal.json`; November cover and storms `analysis/storms-bare-soil/README.md`; wheat `analysis/enso-wheat/README.md`; scale `analysis/scale/results/scale.json`; second municipality `analysis/farm-reports/README.md` ("Second municipality: Júlio de Castilhos") and `results/julio-de-castilhos/`; seven cities `analysis/seven-cities/README.md` ("Result") and `results/team_criteria_by_city.csv`; Landsat/HLS `analysis/residue-landsat/README.md`.
- Paraná pilot: primary source MAPA news "Manejo sustentável impulsiona subvenção do seguro rural para até 35% na soja", 17/11/2025, https://www.gov.br/agricultura/pt-br/assuntos/noticias/2025/manejo-sustentavel-impulsiona-subvencao-do-seguro-rural-para-ate-35-na-soja (read 2026-11-15: 29 areas, about 2,400 ha; NM4 ~5%, NM3 27%, NM2 57%, NM1 11%; subsidy 20/25/30/35% at the time). One regional outlet reports 28 areas; quote MAPA's 29.
- Alternating strategy: the pre-check has no separate NM range for it (no field trial of this exact alternation was found); do not invent one.
- Landsat caveats to keep: 1991 is the series high (22.1% for the year's median; the 4 November scene shows 20.0%), not a typical year; the 2026 scene is three weeks earlier in the season; no field calibration, so no hectares or % straw cover; the satellite does not prove that no-till caused the drop.
- Vetoes respected: "53% of municipal harvests", never "of winters"; "no green cover (mostly straw)", never "bare" for the NDVI calendar; no "credit rose"; no "+36% hot days"; no claim of a 2026 wheat failure.

## 3. Link to Project Demo

> *Official prompt:* a 7-slide presentation (including title and introductory slides) **or** a video of 30 seconds or less; the link "should not require a password, permission, or registration".

**Paste:** `[DEMO LINK]`

**Notes (do not paste):** the demo is a **28-second video** (28.2 s by `ffprobe`; 1920×1080, H.264, no audio track): a real screen recording of the published farmer-facing app (`/globe`, home, `/start`) with **burned-in English captions**, **no voice**, no music, no AI-generated images, no people and no NASA logo. The captions and the assembly were scripted with Claude Code (SI-assisted, declared in field 6 and in the file's metadata). File: `demo-28s.mp4` in the team's demo folder (not in the repo). Before pasting: upload as YouTube Unlisted/Public or Drive "Anyone with the link", open the link in a private window, and have a person who did not make it watch it on a phone.

## 4. Link to Final Project

> *Official prompt:* "a website [...] code repository, or platforms such as YouTube, Google Drive, GitHub [...] should not require a password, permission, or registration".

**Paste:**

- **App (the product):** https://fieldshift-spaceapp.vercel.app — app source to be published: `[APP SOURCE URL]`

Evidence (7 links):
1. Data & Methods (pipeline, provenance, every dataset and method): https://fieldshift-data.vercel.app/data-methods
2. ZarcNM pre-check (rules, tests, results): https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/zarcnm-precheck
3. Every farm of Cruz Alta, one soil pre-check from NASA data, and the same code in a second municipality and in 7 cities without tuning: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/farm-reports · https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/seven-cities
4. Forty years of Landsat and HLS (straw, not bare soil): https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/residue-landsat
5. Every field's winter from space (rotation fingerprint, NASA HLS): https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/rotation-fingerprint
6. What did not hold (pre-registered null tests, NASA's Prithvi model, a calendar model): https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/drought-resilience · https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/rotation-drought-test · https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/nasa-ai-prithvi · https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/analysis/team-rotation-evidence
7. Code repository (public, Apache-2.0; every analysis reruns from public sources): https://github.com/FieldShift-SpaceApp/fieldshift

**Notes (do not paste):** test every link logged out before submitting. Do not link the private team workspace or the farmer-facing app's private repository. Its code must be public before submitting (the official rule asks for publicly accessible materials); until then keep `[APP SOURCE URL]`. Field 4 keeps at most 7 evidence links (jury round 6); the other analyses (policy-targeting, field-calibration, enso-wheat, storms-bare-soil, ground-truth-proagro, scale) and the site page are reachable from Data & Methods and the repository. Read 2026-11-15 (anonymous `curl`): the app no longer says "as proof", but `/sources` says "the satellite data it names (NASADEM; Landsat, Sentinel-2 or HLS)"; the faithful wording is "recommends Landsat, Sentinel-2 or HLS" (item 6.4) and "such as NASADEM or equivalent" (item 6.3) — fix in the app.

## 5. Detailed Project Description

> *Official prompt:* "What exactly does it do? How does it work? What benefits does it have? What do you hope to achieve? What tools, coding languages, hardware, or software did you use".

**Paste:**

`[PRODUCT NAME]` — `[ONE-LINE STATEMENT]`

**The decision.** In the Planalto Médio of Rio Grande do Sul, soybean fills the summer and the farmer chooses what follows it in winter. We compare three strategies: a wheat-like cereal every winter (income, exposed to the weather), a cover crop every winter such as black oat with vetch (protects the soil, costs money, earns nothing directly), or alternating the two. Fallow (no cost, no protection) is only a reference: NASA HLS finds it on 0.3–0.6% of Cruz Alta's cropland in each winter of 2020–2025. The choice comes months before winter.

Two things now ride on it. **Insurance:** since 2026/27, Rio Grande do Sul soybean has a ZarcNM zoning (Portaria SPA/MAPA 209/2026). IN SPA/MAPA 2/2025 places each field in a management level NM1–NM4 from the mean of six indicators — base saturation, calcium and aluminium saturation from a soil test, plus years without tillage, straw cover before sowing and crop diversity over three years — with override rules (for example, two indicators at level 1, two consecutive soybean crops, or a slope of 3% or more without contour sowing force NM1). In the 2026 pilot the federal subsidy on the soybean premium is 20, 30, 35 or 40% for NM1 to NM4 (Resolução CGSR 111/2026), with a budget of R$ 1 million for soybean in four states. For the satellite part, the rule asks for slope from 30 m products "such as NASADEM or equivalent", and for NDVI and NDTI series at 30 m, "recommending Landsat, Sentinel-2 or harmonized products (HLS)"; MODIS at 250 m is accepted for fields over 100 ha. **Weather:** wheat is where El Niño hurts — in 18 municipalities around Cruz Alta, 1981–2025, wheat yield fell below 75% of its own trend in 53.3% of municipal harvests in El Niño winters (73 of 137), against 3.5% in La Niña winters (3 of 86); these are 8 El Niño and 5 La Niña winters, and the difference holds in a winter-level permutation test (p = 0.003).

**What it does today (public).**
1. **ZarcNM pre-check** (`analysis/zarcnm-precheck`, summarized on Data & Methods). A rules module transcribes the indicator table (Table 1) and the override rules (item 3.2.1) of IN 2/2025, with the item number next to each rule and every ambiguous reading marked and tested; Portaria 209/2026's soil-depth cap is added. For each winter path it estimates the three management indicators, and prints the NM range that follows for each level of the soil tests. Output: `results/precheck.json`.
2. **Every farm, one pre-check** (`analysis/farm-reports`). The same rule run on every rural property of Cruz Alta in the public registry (CAR), reading straw cover and the last bare-soil spring from Landsat/HLS, the winter fingerprint from HLS and the slope from NASADEM; aggregates, a map and one anonymous example report are published, never the property codes.
3. **Site page for Cruz Alta** (https://fieldshift-data.vercel.app/sites/cruz-alta): the NASA POWER record (January 1981 to October 2026) as recent monthly rain and temperature, climate indices for 1991–2020 and the team's ground check against local stations; every underlined number opens its source (dataset, version, access date, data type, limitations).
4. **Data & Methods page** (https://fieldshift-data.vercel.app/data-methods): one section per method with references and limitations, the full list of datasets and licences, and the log of AI use.
5. **Site data files** (`data/sites/cruz-alta/output/`), validated in CI against versioned data contracts: NASA POWER series and indices, heavy rain by ENSO phase from three sources, the February-forecast scorecard, a calendar of cropland without green cover, a 2023 replay and the 2026 season so far.
6. **Soil-test vouchers** (`analysis/policy-targeting`, app `/policy`): with a public budget for soil tests, which properties should get one so that each real unlocks the most subsidy, or reaches the most small farms; compared with first come, first served.
7. **Field calibration** (`analysis/field-calibration`, app `/calibrate`): a 20-minute rope-transect protocol and code that turns each farmer's straw count into a sharper satellite straw ruler (Embrapa Documentos 454 as the prior). No Cruz Alta field has been measured yet; the slot is empty, not invented.
8. **Team research, reproduced in public** (`analysis/team-rotation-evidence`): the gross revenue per hectare of wheat + soybean against soybean + fallow (IBGE), and a crop-calendar model of the heavy rain that falls on soil without a living plant, both matching the team's tables. The calendar model is labelled "calendar model only" and is not used here as evidence of protection: measured by satellite, a winter crop does not lower the year's exposure (it is green in July–September and leaves the field without a living plant in October–November, under straw).
9. **NASA's AI tested** (`analysis/nasa-ai-prithvi`): the NASA/IBM Prithvi foundation model run on Cruz Alta's winter 2024 in HLS.
10. **Reproducible analyses**, each rerun from public sources with one command: El Niño and wheat losses; storms meet soil (heavy rain on cropland without green cover, and a straw clock); ground truth (insured wheat losses to excess rain against NASA IMERG); the scale of the problem; forty years of Cruz Alta cropland in Landsat and HLS (green, straw or probable bare soil in every spring since 1984, plus NASADEM slope); the winter of every 30 m field in NASA HLS (rotation fingerprint); and two pre-registered drought tests that came back null.

**The farmer-facing app** (https://fieldshift-spaceapp.vercel.app, built with the team's agronomist) puts the winter choice on one screen for Cruz Alta: the three strategies side by side (soil effect, weather risk, and money only where a source gives a value), a **Soil level** screen with the six ZarcNM indicators, the NM range and subsidy band of each path and the warning "pre-check, not an official classification", a farm view, a globe that flies from NASA Blue Marble down to the Landsat and HLS classes and NASADEM slope of Cruz Alta, next winter's El Niño odds from dated forecasts and how often February forecasts got the winter right, the November storm signal, the 2026 season so far, and a sources page that separates NASA, partner (ESA) and other data.

**How it works.**
- **Indicator estimates.** *Years without tillage*: assumed eight or more years of continuous no-till for every path (level 4); the norm dates the last tillage from sudden changes in the NDVI/NDTI series (item 6.8). *Straw cover before sowing*: straw left on 1, 16 and 30 November by the straw clock (single exponential with the half-lives measured in the Cruz Alta no-till trial) converted to % cover with published mass-to-cover coefficients (Gregory 1982, as quoted by McCool et al. 2006). *Crop diversity*: the norm's table applied to each path's three-year calendar. Base saturation, calcium and aluminium saturation are not observable from satellite and stay open.
- **Pipeline** (`services/science`, Python 3.12). Downloads NASA POWER daily data for each site point, keeps the raw response with its request URL and access time, aggregates to monthly values (gaps stay empty), computes FAO-56 reference evapotranspiration and climate indices, and builds the complement files from GPM IMERG (through the POWER API), the NOAA Oceanic Niño Index, NASA GMAO GEOS-S2S and IRI forecasts, Sentinel-2/MODIS cover tables, an ANA rain gauge and IBGE yields. Every value carries a provenance record naming the owners to credit (NASA, partner agency, other public source); `fieldshift validate --all` checks every data file in CI.
- **Web app** (Next.js, static): reads the data files at build time; no number is typed by hand.
- **Validation.** NASA POWER and IMERG checked against INMET station A853 and ANA gauge 2853015 (daily rain correlation with A853: 0.85 IMERG, 0.78 POWER; 0.92 monthly); POWER's maximum temperature runs +1.84 °C above the station in January–February since about 2019, so we do not claim a rise in hot days. Across 2013–2025, wetter September–November springs in NASA IMERG went with more insured wheat area paid by Proagro for excess rain in the 18 municipalities (Spearman ρ = 0.69, permutation p = 0.006, 13 years; 0.61 without 2023); the metric chosen before the test, days with ≥ 50 mm, was weaker (ρ = 0.41, p = 0.085), and we report both.

**What the data say (verified).**
- **ZarcNM pre-check, Cruz Alta:** with the three soil tests at level 4, soybean–cover crop NM3–NM4 (35–40%), soybean–wheat NM2–NM3 (30–35%), soybean–fallow NM1–NM2 (20–30%). With soil tests at level 3 the ranges are NM2–3, NM3 and NM1–2; at level 1 every path is NM1. Fallow has crop diversity at level 1 whatever happens, so one more indicator at level 1 gives NM1; read literally, soybean–fallow–soybean is also "two consecutive soybean crops". The cover crop reaches NM4 only with at least 60% straw cover before sowing.
- **Forty years of Landsat and HLS:** in late October to mid November, cropland with a probable bare-soil signature (no green and a low tillage index, NDTI) was 5.7% in the median year of 1984–1994 and has stayed at or below 2.2% every year since 1995 (0.3% in the median year since 2005). The same cropland at 30 m: 20.0% probable bare soil on 4 November 1991 (Landsat 5 TM; the highest year of the series) and 0.3% on 20 October 2026 (HLS S30). Since 1995 most cropland without green cover in that window is straw (11–74% of the cropland per year). The IBGE census agrees: no-till covered about 84% (2006) and 108% (2017) of the summer-crop area of Cruz Alta.
- **Every farm of Cruz Alta:** of the 1,554 active properties in the CAR, 1,286 have all three satellite indicators; **1,263 of them (98%; 102,774 ha of cropland)** could reach NM3 or above on the satellite side if the soil test is at the top level (level 4) and contour sowing is confirmed (1,223 if the soil tests are at level 3). **1,284 of the 1,286** have a mean cropland slope of 3% or more (NASADEM), so contour sowing must be confirmed on almost every farm. The bottleneck is the soil analysis and the contour check, not the satellite history. The years-without-tillage reading is the most threshold-sensitive result (96 to 578 properties with a bare-soil signature since 2019, depending on the threshold).
- **Same code, second municipality and seven cities (no tuning):** in Júlio de Castilhos (RS, 1,906 properties in the CAR), 1,527 have all three satellite indicators and **1,508 (99%; 121,336 ha)** could reach NM3 or above on the satellite side under the same conditions; all 1,527 need the contour check. The scene steps took about 10 minutes and the rest about 2.5 minutes on a home connection. What moved is again the threshold-sensitive tillage reading, not the pre-check. Separately, the team's rotation-risk method (soil-water model against IBGE yields, wheat vs fallow water balance, Landsat/HLS cover in the storm months, IMERG heavy rain by El Niño phase) passed all four criteria, written before running, in **5 of 7** neighbouring municipalities; Ijuí and São Luiz Gonzaga passed 3 of 4 (`analysis/seven-cities`).
- **Every field's winter (NASA HLS, 1.17 million 30 m pixels, 2020–2026):** a wheat-like cereal on 25.6–53.3% of the cropland per year (mean 39.9%, against 40.7% for IBGE's winter grains; year-to-year agreement weak, r = 0.41), a cover crop on 31–66%, fallow on 0.3–0.6% (2020–2025); only 5.2% of the pixels kept one path in all seven winters. Read with the rule's diversity indicator (2023–2025), 66.5% of the cropland meets the satellite-visible part of level 3. These are phenological classes without field labels.
- **NASADEM slope:** 87.4% of Cruz Alta cropland has a slope of 3% or more, where the rule requires contour sowing on at least 75% of the area (IN 2/2025 item 3.2.1-I); the DEM shows where the rule applies, not whether a field complies.
- **Two pre-registered tests, both null.** (1) Soybean did not become less sensitive to summer drought after winter cover became the rule: +21.5% of trend per standard deviation of summer rain in 1982–1994 against +17.1% in 1995–2025 (change −4.5 points, 95% interval −24.3 to +19.2, permutation p = 0.61). (2) At 30 m in NASA HLS, soybean after a cover crop did not keep more canopy than after a wheat-like cereal in the 2021/22 and 2022/23 droughts (difference −0.008 NDVI, 95% interval −0.011 to −0.005, inside the year-to-year noise of ±0.006); it confirms the team's earlier natural experiment. We do not claim drought protection from winter cover.
- **Where a public real goes furthest (soil-test vouchers):** testing every assessed property would cost R$ 1.55 million. With R$ 100 thousand and half of the soil tests favourable, targeting for subsidy brings 3,565 ha to NM3+ against 3,233 ha first come (about 10% more), because the satellite side is rarely the bottleneck; "small first" reaches 454 small properties instead of 61, for 30% less subsidy unlocked. These are expected values under stated assumptions (contour confirmed, R$ 488/ha premium).
- **NASA's foundation model, honestly:** the published Prithvi crop model (fine-tuned on US crops) gives no useful winter class in Cruz Alta (Cohen's kappa −0.01, chance); a linear probe on its features reproduces our rule classes on 65.6–69.7% of the pixels, but the same probe on the raw HLS bands does better (82.7%). Without fine-tuning on Brazilian labels it adds nothing over the raw bands for this question.
- **The rule in practice:** in Paraná's first pilot season (2025/26), 29 production areas (about 2,400 ha) were classified: about 5% of the area in NM4, 27% NM3, 57% NM2 and 11% NM1 (MAPA, 17 November 2025). A pre-check that says which fields can reach NM3–NM4 addresses the level most fields did not reach.
- **November storms:** cropland without green cover (mostly straw; Sentinel-2 10 m, NDVI < 0.25) peaks at 67.6% (1–15 November) and 75.6% (16–30 November), median 2019–2025; in 1–15 November 44% of years have a day with ≥ 50 mm in NASA IMERG (95% interval 27–63%). The straw clock gives, on 1 November, 3.1–8.2 t/ha for black oat desiccated in September–October, 2.6–4.1 t/ha for harvested wheat and no winter straw for fallow — arithmetic from measured half-lives, not a field measurement.
- **Heavy rain at wheat harvest, by ENSO phase** (mean September–November days with ≥ 50 mm, Cruz Alta): NASA GPM IMERG 4.4 / 2.6 / 1.4 (El Niño / neutral / La Niña, 1998–2025); ANA gauge 4.0 / 2.2 / 1.5 and NASA POWER 1.9 / 1.1 / 0.9 (1982–2025).
- **ENSO phase is defined per question, so numbers differ between analyses:** the wheat result uses the winter's ONI for June–August (≥ +0.5 °C El Niño, ≤ −0.5 °C La Niña; 53% against 3.5% of municipal harvests), and the harvest heavy-rain result uses the ONI phase of September–November (NOAA's operational five-season rule; 4.4 against 1.4 days). The same year can fall in different phases under the two definitions.
- **Forecasts in February** do not beat "always neutral" on the winter's ENSO phase (NASA GMAO GEOS-S2S: 0.56 against 0.71, 41 years), so only odds and track records are shown.
- **2026 so far:** 1 September–11 November 2026, NASA POWER at Cruz Alta recorded 935 mm and 5 days with ≥ 50 mm, against 537 mm and 1.2 days in an average El Niño year over the same days; NOAA's ONI for August–October 2026 is +2.46 °C.
- **Scale:** Rio Grande do Sul planted 1.16 million ha of wheat in 2025 (46% of Brazil's) on about 20,000 farms (2017 Census of Agriculture); in 2023 its wheat output fell from 5.3 to 2.6 million t and Proagro approved R$ 2.07 billion in wheat claims.

**Benefits.**
- Turns a new, technical insurance rule into a question a farmer can ask before winter: which path keeps my field at a good level, and is the soil test worth paying for?
- Reads the data the rule itself recommends (Landsat/HLS imagery, an elevation model such as NASADEM), farm by farm, and is honest about what it cannot see (3 of 6 indicators, contour sowing) and about tests that came back null.
- Puts two separate soil benefits side by side: the rule's (roots and drought) and straw cover in October–November, when the storms come (measured by satellite).
- Open and reproducible: every number traces to its source; anyone can rerun the analyses.

**What we hope to achieve.** That farmers, agronomists and cooperatives in southern Brazil use the same open evidence when they choose the winter after soybean, and that a field's management history read from NASA data becomes something the farmer can check, not only something an accredited agent files. Next steps: read declared field polygons instead of whole CAR properties; check the straw-cover estimate against field transects and the Embrapa method (Franchini et al. 2023); have the agronomist set crop thresholds per site; add more municipalities with the same pipeline.

**Limitations and uncertainty.**
- **A pre-check, not a classification.** The official level comes only from Embrapa's SINM, after accredited agents register the field and its soil analyses. Three of six indicators need a soil test; contour sowing on slopes of 3% or more and the useful soil depth are assumed compliant, and either can force NM1. Years without tillage is assumed (8+ years).
- **Straw cover has no field calibration:** straw mass comes from one trial's half-lives, the mass-to-cover coefficients are US wheat measurements, and no NDTI threshold was calibrated against field cover here. NDVI cannot separate straw from bare soil. The Landsat/HLS "probable bare soil" class uses a threshold chosen by the team; kaolinite-rich soils can make bare soil look like straw, wet soil changes the index, sensors differ, and no TM/OLI pair exists to check the 1980s level directly.
- **Winter classes and farm reports have no field labels:** the HLS winter paths are phenological rules; a cover crop and an early cereal can be confused; the CAR outlines overlap and are whole properties, not fields.
- **The subsidy pilot is small** (R$ 1 million for soybean in four states) and its percentages were read on a transcription of the resolution. Per hectare, moving from NM1 (20%) to NM2–NM4 (30–40%) is worth ≈ R$ 49–98/ha a year, an estimate using the RS average soybean premium R$ 488/ha (PSR 2024); the real premium varies by farm, insurer and year (Cruz Alta's average was R$ 408/ha).
- The rule justifies the levels by root depth and drought risk, not by storms; the November storm benefit is our own, separate argument, and it comes from straw: measured by satellite, a winter crop does not lower the year's exposure of the soil without a living plant (`analysis/residue-landsat`, `analysis/storms-bare-soil`). The heavy-rain shares per winter calendar in `analysis/team-rotation-evidence` are a calendar model only and are not cited as evidence.
- NASA POWER and IMERG values are regional signals (one grid cell around the site point), not field measurements; POWER is modeled. The El Niño–wheat result rests on 8 El Niño and 5 La Niña winters; yield is municipal; the association is statistical. Forecast samples are tiny. IMERG through POWER stopped on 14 September 2026 at access, so the 2026 window uses NASA POWER.
- Full list, per method: Data & Methods page (field 4).

**Use statement.** This tool supports, and does not replace, the judgment of farmers and agronomists. It explores options; it does not prescribe actions, certify a management level, or promise yields, subsidies, profit or carbon credits.

**Tools, languages and software.** Python 3.12 (uv, pydantic, httpx, PyYAML, NumPy, Matplotlib, xarray/netCDF4, pytest, Ruff); TypeScript, Next.js 16, React 19, Tailwind CSS 4, shadcn/Radix UI; Vitest, Testing Library and Playwright; GitHub Actions CI with gitleaks secret scanning; Vercel hosting. The Landsat/HLS/NASADEM analyses also use rasterio, pystac-client and the Microsoft Planetary Computer STAC; the Prithvi test uses PyTorch on a laptop CPU. The farmer-facing app also uses Leaflet with OpenStreetMap tiles and NASA GIBS map tiles, and its NDVI map was prepared with Google Earth Engine. No hardware. Full list with versions and licences in field 8.

**Notes (do not paste):**
- Sources: ZarcNM `analysis/zarcnm-precheck/README.md` and `results/precheck.json`; every farm `analysis/farm-reports/README.md` ("Results"); winter paths `analysis/rotation-fingerprint/README.md` ("Answer"); NASADEM `analysis/residue-landsat/results/nasadem_slope_classes.json`; nulls `analysis/drought-resilience/README.md` ("Answer") and `analysis/rotation-drought-test/README.md` ("Results"); ground truth `analysis/ground-truth-proagro/README.md`; scale `analysis/scale/README.md`, the second municipality in `analysis/farm-reports/README.md` ("Second municipality: Júlio de Castilhos") and the seven cities in `analysis/seven-cities/README.md` ("Result"); Landsat/HLS `analysis/residue-landsat/README.md` ("Answer" and "Before and after"); Paraná pilot as in field 2; vouchers `analysis/policy-targeting/README.md` ("Results"); Prithvi `analysis/nasa-ai-prithvi/README.md` ("Answer in one paragraph"); per-hectare estimate = R$ 488/ha × (30% − 20%) to × (40% − 20%), premium from MAPA's PSR open data (SISSER), RS soybean 2024, as used in `analysis/policy-targeting`. The rest as in field 2.
- The app description follows the live app's routes (`/`, `/soil-level`, `/rotations`, `/my-farm`, `/globe`, `/sources`; anonymous `curl`, 2026-11-15). Delete any screen that is not in the version submitted.

## 6. Use of Super Intelligence (SI)

> *Official prompt:* "Did you utilize any Super Intelligence (SI) tools and software in preparing your solution? If yes, how did you use them?" The guide says this answer is for data collection and is not shown to judges; SI indicators inside the project are.

**Paste:**

**Answer: Yes.**

We used SI tools as assistants for research, code, documentation, analysis and review. **Origin of the idea, stated as it happened:** the team generated the starting ideas at a human ideation meeting on 14 November (transcribed in the team workspace), and the farmer on the team described the real winter decision in an interview. At the team lead's request, an SI tool (Claude Code) then helped **compare and synthesize concepts from those human ideas** and from data the team had verified, and drafted the pitch text. The **ZarcNM direction** — scoring the three winter paths against Brazil's soil-management rule and reading it with Landsat/HLS and NASADEM — was also synthesized with Claude Code at the team lead's request, from two of the team's human ideas ("adapt the rotation to the year's forecast" and "validate with data what farmers already do") and from the farmer's account of the decision; an AI-assisted mock jury compared it with other options. The team adopted it and wrote the one-line statement in its own words (decision record `D-001` in `DECISIONS.md`).

- **Code (SI-generated, human-directed):** Claude Code (Anthropic) wrote most of the code in the repository under the team's instructions: NASA POWER ingestion and monthly aggregation, FAO-56 ET0, climate indices and data validation, the complement datasets (GPM IMERG via POWER, forecast archives, bare-soil calendar, 2023 replay, 2026 season so far), the data contracts and their code generation, the web app pages, the ZarcNM rules module and its tests, the analysis folders, the tests and the CI workflow. Every SI-assisted file carries an "SI-assisted" header naming the tool and the reviewer, and every SI-assisted pull request has a row in `SI-USAGE.md`. Codex (OpenAI) was used to review planning documents, the pitch draft and one pull request. The farmer-facing app was also built with Claude Code; its SI log is published with its source (`[APP SOURCE URL]`).
- **Rules from the norm (SI-transcribed, human review pending):** the ZarcNM rules were transcribed by Claude Code from the official texts (IN SPA/MAPA 2/2025, Portaria SPA/MAPA 209/2026), with the item number next to each rule and each ambiguous reading marked and tested; the team's agronomist is asked to confirm the readings.
- **Analyses (SI-run, human-directed):** Claude Code ported the team's verification scripts to English and ran them and the new analyses against the public sources. The complement datasets, "storms meet soil", "straw, not bare soil" (Landsat/HLS), the rotation fingerprint, the farm reports, the two drought tests and the ZarcNM pre-check were requested by the team lead; as for the whole project, the team generated the starting ideas at a human ideation meeting; at the team lead's request, SI helped compare and synthesize options from those ideas and verified data; the team chose the direction (D-001). The ported team research in `analysis/team-rotation-evidence/` is credited to the FieldShift team research.
- **Text (SI-generated, human-directed):** Claude Code and Claude (Anthropic) drafted the documentation (README, methods, glossary, related work, resources and licences, analysis write-ups, this submission text) and the team's internal planning documents. Research used Claude Code with the Firecrawl CLI and web search to read official pages and norms; facts were checked against their sources and the sources are cited.
- **Data:** no number shown in the project is produced by an SI model. Numbers come from NASA, ESA Copernicus and other public sources through deterministic code (FAO-56, counts, percentiles, permutation tests, exponential decay, the norm's own tables) or are transcribed from cited publications and norms; SI wrote and ran that code. Data files produced this way are declared in `SI-USAGE.md` and in each dataset's `provenance.json`.
- **Images:** the app icon (`icon.svg`, SVG code written by Claude Code) and the static charts of the analyses (drawn by Matplotlib scripts written by Claude Code from the computed results) are declared in `SI-USAGE.md`. No NASA logo, flag or mission insignia appears in any SI-generated content.
- **Demo:** the demo video has **no narration voice and no synthetic audio** (no audio track at all), no music and no AI-generated images: it is a screen recording of the published app with burned-in English captions. **The captions and the assembly (scene order, timing, crossfades) were scripted with Claude Code (Anthropic), SI-assisted**; this is stated in the video file's metadata and in `SI-USAGE.md`.
- **Human review:** `[REVIEWERS]`

Full log with dates, tools and files: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/SI-USAGE.md

**Notes (do not paste):** the first part of the origin paragraph is the text approved in PR #40; the ZarcNM sentence is new. Human ideas: H11 and H12 of the ideation transcript of 14 November (team workspace); the farmer's account: his interview. The pivot jury (`coordenacao/pivo/JURI-PIVO.md`, team workspace) was organized with AI. The demo variant is "captions only": `ffprobe` shows no audio track in `demo-28s.mp4` (checked 2026-11-15). If any voice or AI image is added later, declare it here and watermark it.

## 7. NASA Data

> *Official prompt:* "Provide specific details about what NASA data and resources you used. To be eligible for a Global Award, you must use at least one NASA data or resource."

**Paste:**

**1. NASA POWER (Prediction Of Worldwide Energy Resources), NASA Langley Research Center** — https://power.larc.nasa.gov/
- **Product:** POWER Daily API, version 2.10.3, community `AG` (agroclimatology), point endpoint; accessed 2026-11-14.
- **Variables:** `T2M`, `T2M_MAX`, `T2M_MIN`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `PRECTOTCORR`, `PS`, modeled soil wetness `GWETTOP`, `GWETROOT`, `GWETPROF`, and modeled land evaporation `EVLAND`.
- **Upstream NASA products (served through POWER, not accessed directly):** MERRA-2 reanalysis (meteorology and soil wetness, about 0.5° × 0.625°) and CERES SYN1deg (solar radiation, 1° × 1°), per the [POWER methodology](https://power.larc.nasa.gov/docs/methodology/).
- **Period:** daily, 1 January 1981 to 31 October 2026 for the Cruz Alta site series (radiation valid from 1984); `PRECTOTCORR` through 11 November 2026 for the 2026 season so far.
- **Used for:** the monthly climate series and FAO-56 reference evapotranspiration on the site page; climate indices; the check series of heavy rain by ENSO phase and of the storms analysis; the 2026 season so far (935 mm and 5 days ≥ 50 mm, 1 September–11 November); rain in the days before each Landsat/HLS scene.
- **Citation** ([POWER referencing guide](https://power.larc.nasa.gov/docs/referencing/)): "The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division." "The data was obtained from the POWER Project's Daily 2.10.3 version on 2026/11/14."

**2. NASA GPM IMERG (Integrated Multi-satellitE Retrievals for GPM), NASA GES DISC** — https://gpm.nasa.gov/data/imerg
- **Product:** daily precipitation `IMERG_PRECTOT`, read through the NASA POWER Daily API v2.10.3 in UTC days (POWER does not state the IMERG run; the product of record is IMERG Final V07). 0.1° grid.
- **Period:** 1998–2025 for heavy rain by ENSO phase and for the 18-municipality ground truth (2013–2025 years used); 2001–2025 for the storms analysis. For 2026, POWER served IMERG only up to 14 September 2026 at access (the GES DISC copies need an Earthdata login, which the pipeline does not use), so the 2026 window is reported with NASA POWER.
- **Used for:** the main heavy-rain signal (September–November days ≥ 50 mm at Cruz Alta: 4.4 El Niño, 2.6 neutral, 1.4 La Niña); heavy-rain days by half-month in "storms meet soil"; the ground truth against Proagro excess-rain claims (ρ = 0.69 for spring total rain, 2013–2025); ground check against INMET A853.
- **Citation:** Huffman, G. J., Stocker, E. F., Bolvin, D. T., Nelkin, E. J., & Tan, J. (2023). GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V07 [Data set]. NASA Goddard Earth Sciences Data and Information Services Center. https://doi.org/10.5067/GPM/IMERG/3B-HH/07 — served by NASA POWER (citation of item 1 also applies).

**3. Landsat Collection 2 Level-2 surface reflectance (USGS/NASA)** — Landsat 4–5 TM, 7 ETM+, 8 OLI and 9 OLI-2, WRS-2 path/row 223/080 and 222/080, red, NIR, SWIR1, SWIR2 and QA band, spring (20 October–20 November) and autumn (April–May) scenes 1984–2026, read anonymously through the Microsoft Planetary Computer STAC (collection landsat-c2-l2); no imagery committed, only per-scene class shares. Used for the 40-year series of green, straw and probable bare soil (NDVI and NDTI) on Cruz Alta cropland and the 1991 panel of the before/after map. Public domain. Citation: Earth Resources Observation and Science (EROS) Center. (2020). Landsat 4-5 Thematic Mapper Level-2, Collection 2 [Data set]. U.S. Geological Survey. https://doi.org/10.5066/P9IAXOVV · EROS Center. (1999). Landsat 7 Enhanced Thematic Mapper Plus Level-2, Collection 2 [Data set]. U.S. Geological Survey. https://doi.org/10.5066/P9C7I13B · EROS Center. (2013). Landsat 8-9 Operational Land Imager / Thermal Infrared Sensor Level-2, Collection 2 [Data set]. U.S. Geological Survey. https://doi.org/10.5066/P9OGBGM6

**4. HLS v2.0, Harmonized Landsat and Sentinel-2, L30 and S30 (NASA LP DAAC)** — 30 m surface reflectance, MGRS tiles T22JBP and T22JBN, same bands and windows, 2017/2020–2026, read through the Microsoft Planetary Computer STAC (hls2-l30, hls2-s30); per-scene class shares only. Used for the recent years of the series and the 2026 panel (HLS S30, 20 October 2026: 0.3% probable bare soil). Citation: Neigh, C., Ju, J., Roger, J.-C., Skakun, S., Vermote, E., Claverie, M., Dungan, J., Yin, Z., Freitag, B., & Justice, C. (2021). HLS Operational Land Imager Surface Reflectance and TOA Brightness Daily Global 30m v2.0 [Data set]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/HLS/HLSL30.002 · Neigh, C., et al. (2021). HLS Sentinel-2 Multi-spectral Instrument Surface Reflectance Daily Global 30m v2.0 [Data set]. NASA LP DAAC. https://doi.org/10.5067/HLS/HLSS30.002

**5. NASA MODIS Vegetation Indices, MOD13Q1 (Terra) and MYD13Q1 (Aqua), version 061, NASA LP DAAC** — https://lpdaac.usgs.gov/products/mod13q1v061/ · https://lpdaac.usgs.gov/products/myd13q1v061/
- **Product:** NDVI, 250 m, 16-day composites; valid observations of pixels with at least 80% cropland, read through the Microsoft Planetary Computer STAC collection `modis-13Q1-061` (anonymous access); 2019–2025, by fortnight.
- **Used for:** the MODIS line of the bare-soil calendar and of the storms chart, beside Sentinel-2 (MODIS shows far less "no green" than Sentinel-2 because the 16-day composite keeps the greenest day).
- **Citation:** Didan, K. (2021). MODIS/Terra Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 [Data set]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/MODIS/MOD13Q1.061 · Didan, K. (2021). MODIS/Aqua Vegetation Indices 16-Day L3 Global 250m SIN Grid V061 [Data set]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/MODIS/MYD13Q1.061

**6. NASA GMAO GEOS-S2S seasonal forecasts** — NMME files: https://ftp.cpc.ncep.noaa.gov/NMME/ENSO/NASA_GEOS5v2/
- **Product:** ensemble-mean Niño-3.4 forecasts of the NMME member `NASA_GEOS5v2` (GEOS-S2S), February starts, target June–August, 1982–2022 (hindcasts before 2011); and the "NASA GMAO" line of the IRI ENSO forecast plume, February issues 2003–2025.
- **Used for:** the forecast scorecard — GEOS-S2S hit rate 0.56 against 0.71 for "always neutral" (41 years). Only skill metrics and the per-year February values of the NASA member are committed.
- **Citation:** Molod, A., et al. (2020). GEOS-S2S Version 2: The GMAO High-Resolution Coupled Model and Assimilation System for Seasonal Prediction. *Journal of Geophysical Research: Atmospheres*, 125(5). https://doi.org/10.1029/2019JD031767 · NMME: Kirtman, B. P., et al. (2014). The North American Multimodel Ensemble. *Bulletin of the American Meteorological Society*, 95(4), 585–601. https://doi.org/10.1175/BAMS-D-12-00050.1

**7. NASADEM Merged DEM Global 1 arc second V001 (NASA JPL, distributed by NASA LP DAAC)** — https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001
- **Product:** elevation at 1 arc-second (about 30 m), tile `NASADEM_HGT_s29w054`, read anonymously through the Microsoft Planetary Computer STAC (collection `nasadem`), reprojected to UTM 22S at 30 m; percent slope from the elevation gradient.
- **Used for:** the slope test of the ZarcNM rule (IN 2/2025 item 3.2.1-I; the norm asks for a 30 m product "such as NASADEM or equivalent", item 6.3): 87.4% of Cruz Alta cropland has a slope of 3% or more (`analysis/residue-landsat/results/nasadem_slope_classes.json`); the mean cropland slope of every CAR property (`analysis/farm-reports`: 1,284 of 1,286 assessed properties at 3% or more); the slope layer of the app's globe.
- **Citation:** NASA JPL. (2020). NASADEM Merged DEM Global 1 arc second V001 [Data set]. NASA Land Processes Distributed Active Archive Center. https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001

**8. NASA GIBS (Global Imagery Browse Services), NASA ESDIS** — https://www.earthdata.nasa.gov/technology/global-imagery-browse-services-gibs
- **Product:** WMTS tiles from `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best`: Blue Marble Next Generation (the globe that opens the app's `/globe` screen) and the HLS true-color layer of the date shown (20 October 2026).
- **Used for:** the visual globe of the farmer-facing app, flying from the whole planet down to Cruz Alta; no number is computed from these tiles.
- **Credit:** "We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS)."

**NASA SRTM GL1** (30 m) read through the Open Topo Data API at 25 points about 5 km apart, for the elevation range around the site in the farmer-facing app — https://www.opentopodata.org/datasets/srtm/ (public domain). The farmer-facing app also reads MOD13Q1 NDVI 2000–2025 through Google Earth Engine for its NDVI map.

**9. Prithvi geospatial foundation models (NASA and IBM, Hugging Face `ibm-nasa-geospatial`)** — https://huggingface.co/ibm-nasa-geospatial
- **Product:** Prithvi-EO-1.0-100M multi-temporal crop classification (Li et al. 2023, https://doi.org/10.57967/hf/0954) and the Prithvi-EO-2.0-100M-TL encoder (Szwarcman et al. 2024, https://arxiv.org/abs/2412.02732), both Apache-2.0; HLS multi-temporal crop classification validation chips (CC BY 4.0) only to check our re-implementation.
- **Used for:** a test of NASA's AI on Cruz Alta's winter 2024 in HLS (`analysis/nasa-ai-prithvi`). Result, reported as found: no useful winter class without fine-tuning on Brazilian labels; raw HLS bands do better.

All NASA data used are open, with no restriction on use ([NASA Earth science data use guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance)). Dataset names appear as plain text; no NASA logo or insignia is used.

**Notes (do not paste):**
- Items are numbered 1–9 in the order they were added; renumber freely when pasting. NASA NEX-GDDP-CMIP6 is not listed: its hot-day number was removed from the app and is not used anywhere.
- Access times in `data/sites/cruz-alta/output/provenance.json` (POWER, IMERG, MODIS, GEOS) and in `analysis/residue-landsat/results/residue_landsat.json` and `nasadem_slope_classes.json`.
- Landsat C2, HLS and NASADEM DOIs and citations resolved by DOI content negotiation on 2026-11-15 (the Landsat DOI pages answer 403 to `curl`; open them once in a browser).
- Not listed because no public code or analysis reads them: MERRA-2/CERES directly (only through POWER), SMAP, GLDAS, GRACE, VIIRS, MCD12Q1/Q2, MOD16, ECOSTRESS, GFSAD, OPERA. GIBS is used only by the app's globe (tiles, no numbers; checked in the live app's code on 2026-11-15). Copernicus DEM: not used anywhere.
- GIBS acknowledgement sentence as given on NASA's GIBS technology page (found 2026-11-15).
- The GMAO subseasonal page in `RESOURCES.md` serves a login form, so it is not linked here.

## 8. Space Agency Partner Data and Other References

> *Official prompt:* "List all of the data, resources, and tools used in your project. Resources should include any code, text, and images (even if they are open source or freely available)".

**Paste:**

**Space Agency Partner data (ESA, Copernicus)**
- **Copernicus Sentinel-2 L2A**, 10 m, tile 22JBP, one scene per fortnight, 2019–2025, read through the Element 84 Earth Search STAC (https://earth-search.aws.element84.com/v1, collection `sentinel-2-l2a`): share of cropland with NDVI < 0.25 per fortnight (bare-soil calendar and storms analysis). Sentinel-2 MSI data also enter through NASA HLS S30, 2020–2026. Terms: Copernicus Sentinel Data Legal Notice (free use with attribution). Credit: "Contains modified Copernicus Sentinel data [2019-2026]" (2026 through HLS S30).
- **ESA WorldCover 2021 v200**, 10 m, class 40 (cropland), mask of the Sentinel-2, Landsat/HLS and NASADEM analyses — https://esa-worldcover.org/ — CC BY 4.0. Credit: "ESA WorldCover project 2021 / Contains modified Copernicus Sentinel data (2021) processed by ESA WorldCover consortium."

**Norms (Brazil) read for the ZarcNM pre-check**
- **Instrução Normativa SPA/MAPA nº 2, de 8 de julho de 2025** (ZarcNM management levels: indicators, Table 1, override rules, remote-sensing requirements in items 6.3–6.8), DOU 09/07/2025, ed. 127, section 1, p. 3.
- **Portaria SPA/MAPA nº 209, de 30 de junho de 2026** (ZarcNM soybean, Rio Grande do Sul, 2026/27; soil-depth cap, item 2.4), DOU 03/07/2026 — https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico/portarias/safra-vigente/rio-grande-do-sul
- **Resolução CGSR nº 111, de 28 de abril de 2026** (2026 ZarcNM pilot: soybean premium subsidy 20/30/35/40% for NM1–NM4; R$ 1 million for soybean), read on the Legismap transcription — https://legismap.com.br/leis-e-normas/resolucao-cgsr-n-111-de-28-04-2026 ; states of the pilot as reported by Agrolink (7 Aug 2026).
- MAPA, PSR open data (SISSER), CC BY — soybean premium per hectare, Rio Grande do Sul 2024 (R$ 488/ha average; Cruz Alta R$ 408/ha), for the per-hectare estimate and the voucher analysis — https://dados.agricultura.gov.br/dataset/baefdc68-9bad-4204-83e8-f2888b79ab48
- MAPA news, "Manejo sustentável impulsiona subvenção do seguro rural para até 35% na soja", 17 November 2025 (results of Paraná's first ZarcNM pilot season) — https://www.gov.br/agricultura/pt-br/assuntos/noticias/2025/manejo-sustentavel-impulsiona-subvencao-do-seguro-rural-para-ate-35-na-soja

**Other data** (each used in the public code, data files or analyses; licence or terms as stated by the provider)
- **NOAA Climate Prediction Center** — Oceanic Niño Index (https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt, ERSSTv5); ENSO Diagnostic Discussions (March–June 2023; 12 November 2026). US government work, public domain.
- **NOAA CPC North American Multi-Model Ensemble (NMME)** — Niño-3.4 forecasts of 6 models, 1982–2022, skill metrics only (https://www.cpc.ncep.noaa.gov/products/NMME/); public domain (NOAA NWS); cite Kirtman et al. (2014).
- **IRI, Columbia University** — ENSO forecast plume, objective probabilities and official CPC/IRI table, February issues 2003–2026, read from the archive figures (https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/). Page licence CC BY 4.0.
- **IBGE** — Municipal Agricultural Survey (PAM), SIDRA 1612 (wheat and soybean yield of 18 municipalities 1981–2025; state and national wheat area and production); Census of Agriculture 2017, SIDRA 6957 (farms with wheat); Census of Agriculture 2006 (SIDRA 849) and 2017 (SIDRA 6855), no-till area of Cruz Alta; localities API and municipal mesh 2022. https://sidra.ibge.gov.br · https://servicodados.ibge.gov.br — public federal data; cite IBGE.
- **Banco Central do Brasil (BCB)** — SICOR rural credit data matrix (`CusteioMunicipioProduto`, wheat operating credit of 18 municipalities, 2013 →), **ODbL** (derived `results/credit_sicor.json` stays under ODbL); IPCA from SGS series 433; Proagro data matrix, "regiao" view (Rio Grande do Sul wheat claims, 2023) and "evento" view (claims by cause, 18 municipalities, 2013–2026), https://www.bcb.gov.br/estabilidadefinanceira/proagro — reproduction allowed with the source cited.
- **CAR, Cadastro Ambiental Rural** (Serviço Florestal Brasileiro), public SICAR GeoServer WFS, layer `sicar:sicar_imoveis_rs` (rural-property outlines of Cruz Alta, no owner fields), read at run time — https://geoserver.car.gov.br/geoserver/sicar/wfs ; no licence stated by the service, so outlines and codes are not redistributed; only aggregates, an unlabeled map and one anonymous example are published.
- **ANA** (Brazil's National Water and Sanitation Agency), HidroWeb — daily rain of gauge 2853015 (Três Capões), 1982–2025 (https://www.snirh.gov.br/hidroweb/); reproduction allowed with the source cited.
- **INMET** (Brazil's National Institute of Meteorology) — stations A853 (Cruz Alta), A883 and A886, ground check (https://portal.inmet.gov.br/dadoshistoricos); freely disseminated; no raw files committed.
- **FAOSTAT** — wheat area harvested 2020–2024 (scale analysis). "FAO. FAOSTAT: Crops and livestock products. Accessed on 14 November 2026. Licence: CC-BY-4.0."
- **UCSB Climate Hazards Center, CHIRPS** v3.0, through SERVIR ClimateSERV, in the satellite-vs-ground comparison (Funk et al. 2026, https://doi.org/10.1038/s41597-026-07096-4).
- **MAPA ZARC** 2022/2023 risk table: wheat sowing window at Cruz Alta in the 2023 replay — Creative Commons Attribution.
- **CONAB** — production costs (two derived values for the 2023 wheat margin), https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao — site content CC BY-ND 3.0; cite CONAB.
- **Embrapa** — De Mori, C. (2007), Comunicado Técnico 207 (black oat cost); Santos, H.P. et al. (ed.) (2019), *Sistemas de produção para cereais de inverno: três décadas de estudos* (initial straw) — cite Embrapa.
- **Emater/RS-Ascar**, Informativo Conjuntural n. 1942 and n. 1945 (2026 wheat harvest, short quotes); 2025 harvest progress as reported by Revista Cultivar.
- **Atlas Digital de Desastres no Brasil** (MIDR/SEDEC), drought records 1991–2025, fetched at run time; no terms found, derived counts quoted, not committed.
- **Access services:** Element 84 Earth Search (Sentinel-2), Microsoft Planetary Computer (MODIS, Landsat C2, HLS, NASADEM, WorldCover), SICAR GeoServer WFS, NASA GIBS WMTS, NOAA CPC FTP, ANA HidroWeb web service, IBGE SIDRA API, BCB Olinda OData and file lists, FAOSTAT bulk download.
- Farmer-facing app, additional sources: ISRIC SoilGrids 2.0 (CC BY 4.0); MapBiomas Brazil Collections 11 and 9 (CC BY 4.0); IBGE IPCA, SIDRA 1737; Open Topo Data API (SRTM); OpenStreetMap map tiles (© OpenStreetMap contributors, ODbL); Google Earth Engine (MODIS NDVI map); IRI objective ENSO probabilities issued October 2026; NOAA CPC/IRI official probabilities of 12 November 2026.

**Methods and literature**
- Franchini, J. C., Debiasi, H., Balbinot Junior, A. A., Farias, J. R. B., Monteiro, J. E. B. A., Santos, E. L., Sartori, A. A. C., Leonardo, H. C. L. (2023). *Sensoriamento remoto para avaliar o histórico de culturas, cobertura do solo com palha e tempo sem revolvimento do solo em áreas agrícolas, para uso no Zarc Níveis de Manejo.* Documentos 454. Embrapa Soja, Londrina. https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1156802/1/DOC-454.pdf — Embrapa's remote-sensing method for the same three ZarcNM indicators (prior art; all rights reserved, cited only).
- McCool, D. K. et al. (2006). Residue characteristics for wind and water erosion control. 14th ISCO Conference — quoting Gregory, J. M. (1982), *Transactions of the ASAE* 25, 1333–1337 (straw mass to % cover).
- Allen, R. G., Pereira, L. S., Raes, D., Smith, M. (1998). *Crop evapotranspiration.* FAO Irrigation and Drainage Paper 56. https://www.fao.org/4/x0490e/x0490e00.htm
- Zhang, X. et al. (2011). Indices for monitoring changes in extremes. *WIREs Climate Change* 2, 851–870. https://doi.org/10.1002/wcc.147 — and ETCCDI core indices.
- McMaster, G. S., Wilhelm, W. W. (1997). Growing degree-days. *Agricultural and Forest Meteorology* 87, 291–300. https://doi.org/10.1016/S0168-1923(97)00027-0
- Hyndman, R. J., Fan, Y. (1996). Sample quantiles in statistical packages. *The American Statistician* 50(4), 361–365. https://doi.org/10.1080/00031305.1996.10473566
- Wilks, D. S. (2011). *Statistical Methods in the Atmospheric Sciences*, 3rd ed., ch. 8. https://doi.org/10.1016/C2017-0-03921-6
- Tucker, C. J. (1979). Red and photographic infrared linear combinations for monitoring vegetation. *Remote Sensing of Environment* 8, 127–150. https://doi.org/10.1016/0034-4257(79)90013-0
- Campos, B. H. C. et al. (2011). *Revista Brasileira de Ciência do Solo* 35(3). https://doi.org/10.1590/S0100-06832011000300017 — straw half-lives at Cruz Alta.
- Aita, C., Giacomini, S. J. (2003). *Revista Brasileira de Ciência do Solo* 27(4), 601–612. https://www.redalyc.org/pdf/1802/180214026004.pdf
- Van Deventer et al. (1997), NDTI, Photogrammetric Engineering & Remote Sensing 63(1), 87–93; Hively et al. (2021), Remote Sensing 13, 3718, https://doi.org/10.3390/rs13183718; Beeson et al. (2020), Remote Sensing 12, 2665, https://doi.org/10.3390/rs12162665; Daughtry et al. (2005), Agronomy Journal 97, 864–871, https://doi.org/10.2134/agronj2003.0291; Quemada & Daughtry (2016), Remote Sensing 8, 660, https://doi.org/10.3390/rs8080660; Roy et al. (2016), Remote Sensing of Environment 185, 57–70, https://doi.org/10.1016/j.rse.2015.12.024; Claverie et al. (2018), Remote Sensing of Environment 219, 145–161, https://doi.org/10.1016/j.rse.2018.09.002; Zheng et al. (2012, 2014); Otsu (1979).
- Molod et al. (2020); Kirtman et al. (2014); Huffman et al. (2023); Didan (2021); EROS Center (Landsat C2); Neigh et al. (2021, HLS); NASA JPL (2020, NASADEM) — full entries in field 7. Funk et al. (2026), CHIRPS v3, *Scientific Data* 13, 718.
- Related work: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/content/related-work.md · Method references: https://github.com/FieldShift-SpaceApp/fieldshift/tree/main/content/methods

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
| Matplotlib (analysis figures) | 3.10.7 | Matplotlib License (PSF-based) |
| xarray + netCDF4 (analysis, NMME files) | as resolved, recorded in `analysis/enso-wheat/results/run_info.json` | Apache-2.0 / MIT |
| rasterio (analysis) | 1.4.3 | BSD-3-Clause |
| pystac-client (analysis) | 0.9.0 | Apache-2.0 |
| planetary-computer (analysis) | 1.0.0 | MIT |
| pytest | 9.2.0 | MIT |
| Ruff | 0.17.5 | MIT |
| gitleaks | 8.30.1 | MIT |
| GitHub Actions | — | service terms |
| Vercel (hosting) | — | service terms |

Farmer-facing app libraries: Next.js 16.4.6, React 19.3.0, Tailwind CSS 4.3.3, Leaflet 1.9.x (BSD-2-Clause), TypeScript 5, ESLint 9; Python scripts with the Google Earth Engine API.

**Fonts and images**
- Geist and Geist Mono fonts (Vercel), loaded through `next/font/google` — SIL Open Font License 1.1.
- App icon: `apps/web/src/app/icon.svg`, SVG code written for this project with Claude Code (declared in `SI-USAGE.md`); no third-party mark, no NASA logo.
- Analysis charts (`analysis/storms-bare-soil/results/storms-bare-soil.png`, `analysis/ground-truth-proagro/results/ground-truth-proagro.png`, `analysis/residue-landsat/results/residue-landsat.png` and `residue-before-after.png`, `analysis/rotation-fingerprint/results/*.png` and `.gif`, `analysis/farm-reports/results/farm-reports-map.png` and `example-report.png`): drawn by the team's Matplotlib scripts (written with Claude Code) from computed results; sources in their footers; no logo.
- App screenshots in `apps/web/docs/screenshots/`: captures of our own app.
- Demo video: a screen recording of our own published app (no slides, no music, no stock or AI-generated image, no voice). Map imagery seen in it is credited on screen as in the app (NASA GIBS / Blue Marble, NASA HLS, NASA/USGS Landsat; OpenFreeMap map tiles, © OpenMapTiles, © OpenStreetMap contributors, ODbL). Captions are set in the Segoe UI system font.

**SI tools** (details in field 6): Claude Code and Claude (Anthropic), Codex (OpenAI), Firecrawl CLI. No voice or image generation tool was used in the demo (captions and assembly scripted with Claude Code).

**Notes (do not paste):**
- Norm citations from the extracted DOU texts in the team workspace; CGSR 111/2026 only from the Legismap transcription (say so if asked).
- Embrapa DOC 454: title, authors, series and year read from the PDF's cover and catalog pages on 2026-11-15; the PDF says "Todos os direitos reservados", so it is cited, not copied.
- "Contains modified Copernicus Sentinel data [2019-2026]": 2026 comes from HLS S30 (#54, merged).
- Copernicus DEM is not used; do not add it.

---

## Final declarations (checkboxes on the form)

- [ ] Terms and Conditions and Privacy Policy accepted.
- [ ] "I confirm that the submitted project represents my team's original work and that all external resources including code, text and images (even if they are open source or freely available) used in the project are listed in the References field" — tick only after the six placeholders at the top are filled.
