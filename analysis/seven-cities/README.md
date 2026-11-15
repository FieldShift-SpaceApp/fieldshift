# Seven cities: does the method hold outside Cruz Alta?

> **SI-assisted:** the test, its criteria and its results are **FieldShift team research** (the team's internal research on rotations, 15 November 2026). The scripts here are an English port written with Claude Code (Anthropic); the anonymously reproducible part was re-run from the committed public inputs and compared with the team's tables before anything was committed. No number below was produced by the AI. Human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

## Question

**Does the method hold, without tuning, in 6 neighbouring municipalities?** The team built its rotation-risk method in Cruz Alta (RS, Brazil). To see whether it is a method or a Cruz Alta anecdote, the same code, thresholds, crop calendars and costs were run, unchanged, in Cruz Alta and six municipalities of the same region that already had the data downloaded. The pass criteria were **written before running**.

| Municipality | IBGE code | Point used for daily weather (lat, lon) |
|---|---|---|
| Cruz Alta | 4306106 | −28.70, −53.56 |
| Ijuí | 4310207 | −28.32, −53.89 |
| Jóia | 4311155 | −28.77, −54.15 |
| São Miguel das Missões | 4319158 | −28.67, −54.52 |
| São Luiz Gonzaga | 4318903 | −28.42, −54.89 |
| Espumoso | 4307500 | −28.86, −52.83 |
| Júlio de Castilhos | 4311205 | −29.26, −53.65 |

## Criteria (written before running)

The method "works" in a municipality if:

| # | What it tests | Pass rule |
|---|---|---|
| C1 | The soil water model tracks the real soybean yield of the municipality | correlation between the modelled water satisfaction of soybean in flowering–grain fill (soybean after winter fallow) and the detrended log of the IBGE PAM yield, 2002–2025, **r ≥ 0.60** |
| C2 | The Cruz Alta conclusion "a winter crop does not change the water available to the next soybean" repeats | water-short years (water satisfaction < 0.70) of soybean after wheat minus soybean after fallow, in years out of 10: **\|difference\| ≤ 0.5** |
| C3 | The satellite pattern of soil cover repeats | after a green winter, **≤ 1 in 10** heavy rains (≥ 25 mm/day) of July–September fall on fields with little living plant (NDVI < 0.5), **and** October–November is more exposed after a green winter than after a low-green winter |
| C4 | El Niño brings more very heavy rain at the wheat harvest | more September–November days with ≥ 50 mm (GPM IMERG) in El Niño years than in the other years |

## Result

**5 of 7 municipalities pass all 4 criteria; Ijuí and São Luiz Gonzaga pass 3 of 4** (both fail C2). Checked in `results/team_criteria_by_city.csv` (column `criteria_passed`) and, for C1, C2 and C4, by the public re-run in `results/reproduced_by_city.csv`.

| Municipality | C1 r (≥ 0.60) | C2 wheat − fallow, years in 10 (\|·\| ≤ 0.5) | C3 Jul–Sep after green winter, per 10 heavy rains; Oct–Nov green vs low-green | C4 days ≥ 50 mm, El Niño vs others | Passed |
|---|---|---|---|---|---|
| Cruz Alta | 0.83 | 4.6 − 4.6 = 0.0 | 0.1; 6.7 vs 3.9 | 7.5 vs 2.2 | **4/4** |
| Ijuí | 0.78 | 2.9 − 4.2 = **−1.3** | 0.0; 6.5 vs 6.3 | 7.8 vs 2.8 | **3/4** |
| Jóia | 0.84 | 5.0 − 4.6 = +0.4 | 0.0; 5.9 vs 3.9 | 7.8 vs 2.6 | **4/4** |
| São Miguel das Missões | 0.84 | 5.4 − 5.8 = −0.4 | 0.1; 6.6 vs 2.9 | 8.0 vs 3.0 | **4/4** |
| São Luiz Gonzaga | 0.69 | 5.8 − 5.0 = **+0.8** | 0.1; 6.9 vs 2.1 | 6.5 vs 3.2 | **3/4** |
| Espumoso | 0.70 | 4.2 − 4.6 = −0.4 | 0.0; 5.8 vs 2.1 | 8.8 vs 1.9 | **4/4** |
| Júlio de Castilhos | 0.75 | 5.4 − 5.0 = +0.4 | 0.0; 5.0 vs 3.5 | 6.5 vs 2.4 | **4/4** |

C2 failing means the *conclusion* did not travel there, not that the model broke: in Ijuí soybean after wheat (sown later, 20 November) is water-short 1.3 fewer years in 10 than after fallow; in São Luiz Gonzaga 0.8 more.

### Per-city table

| Municipality | Annual rain (mm, IMERG 2000–2025) | Dec–Feb rain (mm) | Soybean yield (kg/ha, 2021–2025) | Soybean area (1,000 ha) | % of soybean pixel-years with a low-green winter | r model × observed yield | Sep–Nov days ≥ 50 mm, El Niño × other years | Median wheat margin (R$/ha) | Median soybean margin (R$/ha) |
|---|---|---|---|---|---|---|---|---|---|
| Cruz Alta | 2,047 | 437 | 2,652 | 93 | 6.3 | 0.83 | 7.5 × 2.2 | −852 | 1,722 |
| Ijuí | 2,084 | 473 | 2,286 | 40 | 1.1 | 0.78 | 7.8 × 2.8 | −1,196 | 915 |
| Jóia | 2,091 | 459 | 1,928 | 81 | 3.6 | 0.84 | 7.8 × 2.6 | −1,137 | 502 |
| São Miguel das Missões | 2,142 | 481 | 1,886 | 73 | 8.6 | 0.84 | 8.0 × 3.0 | −945 | 1,016 |
| São Luiz Gonzaga | 2,125 | 491 | 1,809 | 82 | 10.9 | 0.69 | 6.5 × 3.2 | −634 | 1,139 |
| Espumoso | 1,999 | 429 | 2,375 | 52 | 0.7 | 0.70 | 8.8 × 1.9 | −879 | 1,812 |
| Júlio de Castilhos | 1,988 | 424 | 2,257 | 104 | 4.4 | 0.75 | 6.5 × 2.4 | −406 | 1,488 |

Source: `results/team_summary_by_city.csv`. Margins: value of production ÷ planted area (IBGE PAM, municipality; years with ≥ 200 ha), in December-2025 reais (IBGE IPCA; wheat at November, soybean at April of the harvest year), minus the CONAB operating cost per hectare for the Cruz Alta / Passo Fundo region (the same cost for all seven), 2001–2025, 25 years each. Wheat lost money in 20 to 23 of the 25 years in every municipality; soybean in 5 to 10.

### Straw signal in October–November (satellite)

After a green winter, the fields without living plants in October–November show a higher crop-residue index (NDTI, MODIS MCD43A4) than after a low-green winter, in all seven municipalities. April is the control month (after the soybean harvest the previous winter should not matter). From `results/straw_summary_by_city.csv` (`straw_summary.py` over the committed team table):

| Municipality | Oct: mean NDTI difference (years > 0 / years) | Nov | Apr (control) |
|---|---|---|---|
| Cruz Alta | +0.048 (23/23) | +0.028 (22/23) | +0.002 (13/23) |
| Ijuí | +0.025 (12/12) | +0.015 (10/12) | +0.005 (10/12) |
| Jóia | +0.048 (23/23) | +0.029 (23/23) | +0.003 (14/23) |
| São Miguel das Missões | +0.051 (23/23) | +0.029 (21/23) | +0.005 (15/23) |
| São Luiz Gonzaga | +0.053 (23/23) | +0.035 (23/23) | +0.006 (18/23) |
| Espumoso | +0.030 (17/18) | +0.015 (14/18) | −0.001 (9/18) |
| Júlio de Castilhos | +0.046 (23/23) | +0.040 (23/23) | +0.011 (20/23) |

In Júlio de Castilhos the April control also shows a difference (20 of 23 years), so the result there is less clean.

### What repeated, what changed

- **Repeated in all seven:** the water model tracks real soybean yield (r 0.69–0.84); soybean is water-short in 4 to 6 years in 10; a winter crop covers the soil in July–September and leaves the field without a living plant in October–November, with a straw signal; wheat does not pay its operating cost in 8 or 9 years in 10; El Niño brings more very heavy rain at the wheat harvest.
- **Changed from city to city:** how much soybean earns (median margin R$ 502 to R$ 1,812 per hectare); how much cropland stays without a winter crop (0.7% to 10.9% of pixel-years); the water advantage of early maize; the effect of wheat on soybean water (C2).
- **Lesson:** the method travels; the conclusions do not. Every new place needs its own run, even a neighbour.

## Note on the ENSO phase definition

The days ≥ 50 mm here use the ENSO phase of the **June–August ONI** of the same year (El Niño ≥ +0.5 °C; El Niño years 2002, 2009, 2015 and 2023) and compare El Niño with **all other years** of 2000–2024, which is why Cruz Alta gives **7.5 × 2.2**. The app and [`data/sites/cruz-alta/output/enso-rain-signal.json`](../../data/sites/cruz-alta/output/enso-rain-signal.json) use the **September–November ONI** phase (NOAA's five-season rule), compare El Niño with **La Niña** over 1998–2025, and give **4.4 × 1.4**: different questions, so different numbers; the same year can fall in different phases under the two definitions.

## Correction of 15 November 2026 (team research)

An earlier team number, the share of heavy rain falling on soil without a living plant **per rotation strategy** (79% with winter fallow against 44% with wheat), came **only from a crop-calendar model**. Measured by satellite, exposure does **not** fall over the whole year: a winter crop covers July–September and leaves the field without a living plant in October–November, under straw. The satellite columns of this test (C3 and the straw table) are that measurement; the calendar-model number is not used here. See [`../team-rotation-evidence/`](../team-rotation-evidence/README.md).

## Reproducibility: what was re-run and what was not

| Part | Status | How |
|---|---|---|
| C1, C2, C4; annual and Dec–Feb rain; soybean yield, area and winter-grain ratio 2021–2025 (16 columns) | **re-run, identical** to the team tables in all 16 columns and 7 municipalities | `reproduce.py` + `water_balance.py` over `inputs/` |
| ENSO phase (June–August ONI) | **re-checked against NOAA CPC**: same ONI values and phases for 2000–2024 | `oni_phase.py` (downloads `oni.ascii.txt`, no account) |
| Daily inputs (NASA POWER, GPM IMERG) | **re-downloaded, identical** for all seven points (see "Re-download check" below) | `fetch_inputs.py` (no account) |
| C3 and % low-green winter pixel-years | **not re-run here**; read from the team table | needs the team's ~1 km MODIS MOD13Q1 NDVI cubes with a MapBiomas soybean mask (built in the team research; the MapBiomas mask comes from Google Earth Engine) |
| Straw signal (NDTI) | **requires Google Earth Engine account; not reproducible anonymously.** Code ported (`straw_ndti_gee.py`, not run here); result committed (`results/team_straw_ndti_seven_cities.csv`) and aggregated anonymously by `straw_summary.py` | MODIS MCD43A4 + MOD13Q1 + MapBiomas Collection 11 in Earth Engine |
| Wheat and soybean margins | **not re-run here** | needs CONAB production-cost sheets; CONAB content is CC BY-ND 3.0 and outside the federal open-data decree, so the cost series is not committed ([`RESOURCES.md`](../../RESOURCES.md)); only the team's median margins are reported |

Run (Python 3.12, from this folder):

```bash
uv run --no-project --with pandas --with numpy python reproduce.py   # prints "mismatching columns: 0"
uv run --no-project --with pandas python oni_phase.py
uv run --no-project --with pandas python straw_summary.py
uv run --no-project --with pandas python fetch_inputs.py all          # slow: 14 ClimateSERV jobs
```

### Re-download check

Run of 2026-11-15 (`fetch_inputs.py all`, no account): the fresh downloads are **identical** to the committed inputs for all seven municipalities. NASA POWER (Tmax, Tmin, Tmean, relative humidity, wind at 2 m, radiation): 9,131 days per point, largest difference 0.00. GPM IMERG V07 via ClimateSERV: 9,091 days with data in both per point (about 0.4% of days have no IMERG value), largest difference 0.00 mm. So the whole chain for C1, C2 and C4 is reproducible anonymously, from the public services to the pass/fail result.

## Limitations

- **Same region, same crops, same assumed calendar.** Sowing dates and stage lengths are assumptions of the team research, to be validated by an agronomist; the altitude of Cruz Alta (410 m) is used for all seven; one CONAB cost region for all. A different climate or production system (Cerrado, irrigated land) has **not** been tested.
- **Few El Niño years.** Under the June–August ONI only 4 of 25 years are El Niño; C4 rests on 4 years per municipality.
- **One rain cell per municipality.** Daily IMERG is the mean of a 0.1° box around one point; POWER is a ~0.5° cell.
- **C1 thresholds near the line.** São Luiz Gonzaga (0.69) and Espumoso (0.70) pass C1 with little room.
- **Satellite sees green and straw, not grain.** "Little living plant" (NDVI < 0.5) is not bare soil: there can be straw. Ijuí and Espumoso have few low-green-winter pixels (12 and 18 years with both groups in the straw table).
- **Yields and margins are municipal averages.** IBGE PAM yield is a rounded estimate; CONAB cost is for a high-technology farm.
- The test shows that the method's checks repeat in neighbouring municipalities; it does not show that any rotation raises yield.

## Files

| File | What it is |
|---|---|
| `water_balance.py` | FAO-56 Penman-Monteith ET0 and the one-bucket soil water balance per crop sequence (ported, formulas unchanged) |
| `reproduce.py` | re-runs C1, C2, C4 and the climate/yield columns and compares them with the team tables |
| `oni_phase.py` | checks the June–August ONI phases against NOAA CPC |
| `fetch_inputs.py` | re-downloads POWER and IMERG for the seven points and compares with `inputs/` |
| `straw_ndti_gee.py` | straw (NDTI) extraction in Earth Engine (needs an account; not run here) |
| `straw_summary.py` | aggregates the committed straw table per municipality |
| `inputs/daily_imerg_power_seven_cities.csv` | daily GPM IMERG V07 (ClimateSERV, 0.1° box) and NASA POWER (Tmax, Tmin, Tmean, RH, wind 2 m, radiation), 1 Jul 2000 – 30 Jun 2025, as used by the team research |
| `inputs/ibge_pam_soy_seven_cities.csv` | IBGE PAM (SIDRA 1612): soybean planted area and yield, and the area of winter grains of the previous winter (wheat, oat, barley, rye, triticale, canola) ÷ soybean planted area, harvests 2002–2025 |
| `results/team_criteria_by_city.csv` | team table of the criteria (C1–C4 and pass count) |
| `results/team_summary_by_city.csv` | team summary per municipality (rain, yield, satellite cover, ENSO, margins) |
| `results/team_enso_phase_oni_jja.csv` | June–August ONI and phase per year, 2000–2024 |
| `results/team_straw_ndti_seven_cities.csv` | team Earth Engine output, NDTI by municipality, winter year, month and winter state |
| `results/reproduced_by_city.csv` | public re-run (16 columns) |
| `results/straw_summary_by_city.csv` | straw aggregation per municipality |

## Sources

- NASA GPM IMERG V07 daily (Huffman et al., doi:10.5067/GPM/IMERG/3B-HH/07), via SERVIR ClimateSERV (dataset 226), https://climateserv.servirglobal.net/
- NASA POWER Daily API, community AG, https://power.larc.nasa.gov/ ("The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division.")
- NASA MODIS MOD13Q1 v061 (doi:10.5067/MODIS/MOD13Q1.061) and MCD43A4 v061 (doi:10.5067/MODIS/MCD43A4.061)
- MapBiomas Collection 11 land cover (soybean class 39), https://brasil.mapbiomas.org/ (CC BY 4.0)
- NOAA CPC Oceanic Niño Index, https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt
- IBGE PAM (SIDRA table 1612) and IPCA (SIDRA table 1737), https://sidra.ibge.gov.br/
- CONAB production costs (operating cost, Cruz Alta / Passo Fundo), https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao (not redistributed)
- FAO-56 (Allen et al. 1998); Franchini et al. (2012) for the 75 mm water capacity and the 0.70 threshold; crop coefficients as cited by Battisti, Sentelhas & Pilau (2012)
