# Team rotation evidence: public reproduction of team research numbers (Cruz Alta, RS)

> **SI-assisted:** the analyses are **FieldShift team research** (the team's internal research on rotations, Cruz Alta, November 2026); the scripts here are a minimal English port written with Claude Code (Anthropic), run against the public sources listed, and each result was compared with the team's table before anything was committed. No number below was produced by the AI. Human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

## Why this folder exists

The farmer-facing app (https://fieldshift-spaceapp.vercel.app) once showed three numbers from the team's internal research. A number on the app or the submission page must be reproducible from public sources by anyone. This folder reproduces them with the smallest code that does it and says, for each, whether the public run matches the team's table. **Only (c) is used in the app today** (`/rotations`, read 2026-11-15); (a) and (b) were removed from the app and are kept here under "What did not hold".

| # | Result | Used in the app? | Team table | Public run here | Status |
|---|---|---|---|---|---|
| c | Gross revenue per hectare, wheat + soybean **R$ 7,312/ha** against soybean + fallow **R$ 4,828/ha** (2025 reais, mean of 2002–2025) | **yes** (`/rotations`) | 7,312 / 4,828 | **7,312 / 4,828** (`results/system_revenue_cruz_alta.csv`) | **matches** |
| b | Share of the heavy rain (days ≥ 25 mm) that falls on soil with no living plant: fallow + soybean 79%, wheat + soybean 44%, autumn cover + wheat + soybean 30%, black oat cover + soybean 52% | **not used in the app** | 79 / 44 / 30 / 52% | 79 / 44 / 30 / 52% (`results/heavy_rain_on_soil_without_live_plants.csv`) | matches the team table, but **calendar model only** (see below) |
| a | Hot days (Tmax ≥ 32 °C, December–March) at Cruz Alta, NASA NEX-GDDP-CMIP6, change against each model's 1995–2014: +11 to +13 days in 2021–2040 and +22 to +29 in 2041–2060 | **not used in the app** | ssp245 2021–2040 +10.7, ssp585 +13.0; ssp245 2041–2060 +22.0, ssp585 +29.1 (30 models) | not reproduced | **not reproduced, not cited** |

## (c) Gross revenue per hectare of a winter–summer system — used in the app (`/rotations`)

**Script:** [`revenue.py`](revenue.py). **Inputs:** `results/ibge_pam_1612_cruz_alta_value.csv` (IBGE PAM, SIDRA table 1612: value of production and harvested area of soybean and wheat, Cruz Alta 4306106, 2001–2025) and `results/ibge_ipca_1737_annual_mean.csv` (IBGE IPCA index, SIDRA table 1737, variable 2266, annual mean of the monthly index), both fetched by `fetch_inputs.py`.

**Method.** Revenue of a crop in year *y* = value of production ÷ harvested area, in 2025 reais (× IPCA mean 2025 ÷ IPCA mean of *y*). Agricultural year *Y* = winter of *Y*−1 + summer of *Y*: soybean + winter fallow = soybean(*Y*); wheat + soybean = soybean(*Y*) + wheat(*Y*−1). Mean over *Y* = 2002–2025.

| System | Years | Mean (R$/ha, 2025) | CV | Worst year |
|---|---|---|---|---|
| soybean + winter fallow | 24 | **4,828** | 45% | 1,102 (2005) |
| wheat + soybean | 24 | **7,312** | 38% | 2,657 (2005) |

**Read it as gross revenue, not margin:** production costs are not subtracted (wheat costs money to grow), and municipal value of production ÷ area is an average over all farms. It says that wheat adds revenue on the same hectare, not that it adds profit.

## What did not hold / calendar model only

> **Warning (team research, 15 November):** Calendar model only; satellite measurement (residue-landsat, storms-bare-soil) shows total-year exposure does not fall with a winter crop; protection in Oct–Nov comes from straw. The winter crop covers July–September and leaves the field without a living plant in October–November, under straw; see [`../residue-landsat/`](../residue-landsat/README.md) (probable bare soil 0.3% of cropland in the median early-November since 2005) and [`../storms-bare-soil/`](../storms-bare-soil/README.md). The (b) numbers are kept and labelled; they are not evidence that a winter crop protects the soil.

### (b) Heavy rain on soil with no living plant — calendar model only, not used in the app

> Calendar model only; satellite measurement (residue-landsat, storms-bare-soil) shows total-year exposure does not fall with a winter crop; protection in Oct–Nov comes from straw.

**Script:** [`exposure.py`](exposure.py). **Input:** `results/imerg_daily_cruz_alta.csv`, daily GPM IMERG V07 at Cruz Alta (mean of a 0.1° box centred on the site point −28.70, −53.56), 1 July 2000 – 30 June 2025, fetched by [`fetch_inputs.py`](fetch_inputs.py) from SERVIR ClimateSERV (dataset 226), the same service and box the team used. The public fetch of 2026-11-15 is **identical** to the team's daily series on all 9,091 days with data (largest difference 0.0 mm).

**Method.** For each agricultural year (1 April – 31 March; 2002–2025 used, 24 years, because 2001 lacks April–June 2000) a crop calendar gives the fraction of the ground under a living plant on each day: it rises linearly from sowing to 80% of the vegetative stage, stays at 1 through flowering and maturation, and is 0 otherwise. Straw counts as **no living plant**. The index is the rain of the days with ≥ 25 mm times (1 − living fraction), summed over all years, divided by all rain of the days with ≥ 25 mm. Sowing dates and stage lengths are in the script (`SEQUENCES`, `CROPS`): **assumptions of the team's research, to be validated by an agronomist**.

| Sequence (agricultural year April → March) | Days per year without a living plant | % of rain on days ≥ 25 mm without a living plant | ≥ 20 mm | ≥ 50 mm |
|---|---|---|---|---|
| winter fallow + soybean (1 Nov) | 253 | **79** | 78 | 83 |
| wheat (15 Jun) + soybean (20 Nov) | 145 | **44** | 43 | 50 |
| autumn cover (10 Apr) + wheat + soybean (20 Nov) | 97 | **30** | 29 | 33 |
| black oat cover (1 May) + soybean (1 Nov) | 149 | **52** | 51 | 54 |
| canola (1 May) + soybean (5 Nov) | 125 | 43 | 42 | 47 |
| black oat cover (1 May) + early maize (1 Sep) | 145 | 37 | 37 | 34 |
| winter fallow + early maize (1 Sep) | 249 | 64 | 64 | 63 |

**Read it as** a relative exposure index between calendars, not a soil-loss estimate: it ignores straw cover (which protects the soil; see `analysis/storms-bare-soil` and `analysis/residue-landsat`), rain intensity within the day, slope and soil. One rain cell (0.1°) stands for the municipality.

### (a) Hot days in the soybean season, NASA NEX-GDDP-CMIP6 — not reproduced, not used in the app

**Not reproduced yet; do not cite this number.** The team's research holds the result table but not the script that computed it, and its raw projections were read through an authenticated Google Earth Engine project, which a public reproduction cannot assume. A public re-implementation was tried on 15 November 2026: it reads the daily `tasmax` of the 0.25° cell nearest Cruz Alta from NEX-GDDP-CMIP6 v2.0 on the NASA NCCS THREDDS server (NCSS point subsetting, no account), one request per model, scenario and year. The server lists 35 models, **30** of them with `historical`, `ssp245` and `ssp585` `tasmax` (the same count as the team's table), which means about 3,100 file-years; the server's throughput fell from about 25 to about 4 file-years per minute, and the run was stopped after 910 file-years (5 complete models), before the code freeze. The partial run is **not** a reproduction and no number from it is reported. To finish it after the event: read the same cell from the AWS Open Data copy (`s3://nex-gddp-cmip6`, anonymous) or let the NCSS run complete, then compare with the team's medians (10.7 / 13.0 / 22.0 / 29.1 days). The number was removed from the app; until a public run matches, it is not cited anywhere.

## Data and terms

| Source | What | NASA? | Terms | Committed here |
|---|---|---|---|---|
| GPM IMERG V07 daily (NASA GES DISC; Huffman et al. 2023, [doi:10.5067/GPM/IMERG/3B-HH/07](https://doi.org/10.5067/GPM/IMERG/3B-HH/07)), via SERVIR ClimateSERV (https://climateserv.servirglobal.net/) | daily rain at Cruz Alta, 2000–2025 | **NASA** | NASA data, open, no restriction; citation requested | yes, the daily series (148 KB) with the request URLs in its header |
| IBGE PAM, SIDRA table 1612 | value of production and harvested area, soybean and wheat, Cruz Alta | no (IBGE) | public federal data; cite IBGE | yes, the municipality-year table |
| IBGE IPCA, SIDRA table 1737 (variable 2266) | consumer price index, annual mean 2000–2025 | no (IBGE) | public federal data; cite IBGE | yes, annual means |

Not used here: CHIRPS (the team's research used it only as an alternative rain source in its sensitivity runs).

## Reproduce

```bash
python -I analysis/team-rotation-evidence/fetch_inputs.py ~/.cache/fieldshift/team-rotation-evidence analysis/team-rotation-evidence/results
python -I analysis/team-rotation-evidence/exposure.py analysis/team-rotation-evidence/results/imerg_daily_cruz_alta.csv analysis/team-rotation-evidence/results
python -I analysis/team-rotation-evidence/revenue.py analysis/team-rotation-evidence/results
```

Standard library only (Python 3.12). ClimateSERV jobs take a few minutes each.

## Credit

FieldShift team research (the team's internal research on rotations in Cruz Alta). This folder ports only what is needed to reproduce these three results; the team's other results are not republished here.
