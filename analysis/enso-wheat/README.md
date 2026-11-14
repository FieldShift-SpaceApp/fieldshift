# ENSO and wheat losses in the Planalto Médio (Rio Grande do Sul, Brazil)

> **SI-assisted:** scripts ported to English and this text written with Claude Code (Anthropic) from the team's independent verification of 2026-11-14; every number below was produced by running the scripts in this folder against the public sources, not by the AI. Human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

This folder holds the analysis behind the team's El Niño and wheat numbers, so anyone can rerun it from the public endpoints with one command. Method summary for the app: [`content/methods/enso-wheat.md`](../../content/methods/enso-wheat.md).

## Question

In the 18 wheat and soybean municipalities of the Planalto Médio (Cruz Alta and neighbours), is a low-yield wheat season more frequent in winters of El Niño than in winters of La Niña? How strong is that evidence, and does it hold when the criterion changes?

## Answer in one paragraph

From 1981 to 2025, wheat yield fell below 75% of the municipality's own trend in **53.3% of the municipal seasons of El Niño winters (73 of 137)**, against **3.5% in La Niña winters (3 of 86)** and 17.2% in neutral winters (96 of 557). These are **8 El Niño winters and 5 La Niña winters**, not 137 and 86 independent cases: neighbouring municipalities fail together. Treating the winter as the unit, the difference survives a permutation test (**p = 0.003**). In the 2023 El Niño winter, wheat fell below the threshold in **14 of the 18 municipalities**. The direction of the result holds in all 12 robustness variants (threshold 70/75/80%, linear or quadratic trend, 1981–2025 or 1990–2025). The "soybean after La Niña" and disaster-record contrasts do **not** hold as rates (see Limitations).

## Data

| Source | Endpoint used | What it gives | Terms | Committed here? |
|---|---|---|---|---|
| IBGE localities API | `servicodados.ibge.gov.br/api/v1/localidades/estados/43/municipios` | IBGE codes of the 18 municipalities, matched by name (no code typed by hand) | public federal data; cite IBGE | no (fetched at run time) |
| IBGE PAM, SIDRA table 1612 | `apisidra.ibge.gov.br/values/t/1612/n6/<codes>/v/112/p/all/c81/2713,2716` | average yield (kg/ha) of soybean (2713) and wheat (2716), every year | public federal data; cite IBGE | derived per municipality-year: `results/municipality_year.csv` |
| NOAA CPC Oceanic Niño Index | `www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` | ONI by 3-month season; the JJA (June–August) value sets the winter phase | US government work, public domain | values used are in `results/wheat_soy_enso.json` |
| NOAA CPC ENSO Diagnostic Discussions, Mar–Jun 2023 | `www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_disc_<mon>2023/ensodisc.shtml` | ENSO Alert System status and synopsis | public domain | `results/cpc_alerts_2023.json` |
| BCB SICOR, rural credit data matrix | OData `olinda.bcb.gov.br/olinda/servico/SICOR/versao/v2/odata/CusteioMunicipioProduto`; IPCA from BCB SGS series 433 | operating credit (value and financed area) for wheat, oat, barley and canola by municipality, 2013 → | ODbL 1.0 | `results/credit_sicor.json` (**ODbL**: a database derived from SICOR) |
| Atlas Digital de Desastres no Brasil (MIDR/SEDEC) | consolidated CSV v1.1 of 2026-08-06, `atlasdigital.mdr.gov.br/arquivos/2026/BD_Atlas_1991_2025_v1.1_2026.08.06_Consolidado.csv` (86 MB) | municipal disaster records 1991–2025 | **license not declared** on the download page | **no**: written to `<raw>/derived/` only; the counts are quoted below |
| IRI ENSO forecast archive and quick looks; NOAA CPC NMME (optional part) | see [`forecast_skill/fetch_forecasts.py`](forecast_skill/fetch_forecasts.py) | ENSO forecasts issued in January–March for the following JJA | IRI page CC BY 4.0 (values read from its figures); NMME: no license text found | skill metrics only: `results/forecast_skill_metrics.csv`, `results/forecast_skill.json` (no per-year NMME values) |

Raw downloads go to `~/.cache/fieldshift/enso-wheat/` (or `--raw DIR`) and are never committed. Each result file records the URL and access time (UTC) of its sources. The numbers in this README come from the run of **2026-11-14** (UTC access times in each result file and in `results/run_info.json`).

## Criterion

- **Municipalities (18):** Cruz Alta, Ijuí, Passo Fundo, Santo Ângelo, Carazinho, Panambi, Tupanciretã, Palmeira das Missões, Santa Bárbara do Sul, Júlio de Castilhos, Ibirubá, Não-Me-Toque, Condor, Ajuricaba, Boa Vista do Cadeado, Fortaleza dos Valos, Pejuçara, Saldanha Marinho.
- **Low-yield season ("loss"):** yield < **75% of the municipality's own linear trend**, fitted with `numpy.polyfit` on the valid years of the window (1981–2025), the year itself included; at least 10 valid years.
- **ENSO phase of the winter:** ONI of JJA **≥ +0.5 = El Niño**, **≤ −0.5 = La Niña**, otherwise neutral. El Niño winters: 1982, 1987, 1991, 1997, 2002, 2009, 2015, 2023. La Niña winters: 1988, 1998, 1999, 2010, 2022.
- **Wheat** is matched with the JJA of the same year; **soybean** of harvest Y+1 with the JJA of Y (the summer after the winter).
- **Coverage:** 780 of 810 possible wheat municipality-years (30 are SIDRA `...`, municipality not yet created: Boa Vista do Cadeado 1981–2000, Saldanha Marinho 1981–1988, Fortaleza dos Valos 1981–1982).
- **Permutation test by winter:** the phase labels are shuffled between winters (the municipalities of a winter stay together), 20,000 draws, fixed seed 20261114; statistic = % loss in El Niño − % loss in La Niña; two-sided.

## Results

### Wheat by winter phase (base case)

| Winter (ONI JJA) | Winters | Municipal seasons | Losses | % | Median yield / trend |
|---|---|---|---|---|---|
| El Niño (≥ +0.5) | 8 | 137 | 73 | **53.3%** | 0.735 |
| strong El Niño (≥ +1.0) | 5 | 69 | 38 | 55.1% | 0.702 |
| Neutral | 32 | 557 | 96 | 17.2% | 1.014 |
| La Niña (≤ −0.5) | 5 | 86 | 3 | **3.5%** | 1.205 |

Permutation by winter: difference 49.8 percentage points, **p = 0.0031** (45 winters).

### Winter by winter (losses / municipalities with data)

| Winter | Phase | Wheat, same year | Soybean, next harvest |
|---|---|---|---|
| 1982 | El Niño | 15/15 | 0/16 |
| 1987 | El Niño | 0/16 | 9/16 |
| 1991 | El Niño | 7/17 | 0/17 |
| 1997 | El Niño | 7/17 | 0/17 |
| 2002 | El Niño | 12/18 | 0/18 |
| 2009 | El Niño | 1/18 | 0/18 |
| 2015 | El Niño | 17/18 | 0/18 |
| 2023 | El Niño | 14/18 | 0/18 |
| 1988 | La Niña | 0/16 | 0/17 |
| 1998 | La Niña | 2/17 | 1/17 |
| 1999 | La Niña | 1/17 | 4/17 |
| 2010 | La Niña | 0/18 | 0/18 |
| 2022 | La Niña | 0/18 | 15/18 |

The loss was regional (half of the municipalities or more) in 4 of the 8 El Niño winters (1982, 2002, 2015, 2023). Without the worst winter (2015) the El Niño rate is 47.1%; without the two worst (2015 and 1982), 39.4%.

### Robustness (% loss El Niño vs La Niña; neutral in brackets)

| Series | Window | Trend | Threshold 70% | Threshold 75% | Threshold 80% |
|---|---|---|---|---|---|
| Wheat | 1981–2025 | linear | 45.3 vs 1.2 (12.2) | **53.3 vs 3.5** (17.2) | 62.0 vs 4.7 (20.8) |
| Wheat | 1981–2025 | quadratic | 48.2 vs 1.2 (11.5) | 51.1 vs 3.5 (16.9) | 60.6 vs 4.7 (21.2) |
| Wheat | 1990–2025 | linear | 46.2 vs 0.0 (12.8) | 49.1 vs 4.3 (17.1) | 66.0 vs 5.7 (21.7) |
| Wheat | 1990–2025 | quadratic | 47.2 vs 0.0 (12.8) | 50.9 vs 4.3 (16.5) | 63.2 vs 5.7 (21.5) |
| Soybean Y+1 | 1981–2025 | linear | 5.1 vs 18.4 (18.0) | 6.5 vs 23.0 (20.4) | 8.0 vs 34.5 (25.6) |
| Soybean Y+1 | 1981–2025 | quadratic | 5.8 vs 17.2 (17.6) | 6.5 vs 26.4 (20.9) | 8.0 vs 33.3 (25.9) |
| Soybean Y+1 | 1990–2025 | linear | 0.0 vs 22.9 (19.6) | 0.0 vs 32.9 (22.1) | 0.0 vs 38.6 (27.3) |
| Soybean Y+1 | 1990–2025 | quadratic | 0.0 vs 21.4 (19.1) | 0.0 vs 32.9 (22.1) | 0.0 vs 41.4 (26.8) |

For wheat, El Niño stays far above neutral and La Niña below it in all 12 variants. For soybean the size of the contrast depends on whether 1987 and 2022 are in the window.

### 2023 and Cruz Alta

- **2023 (El Niño, ONI JJA +1.00):** wheat below 75% of trend in **14 of 18** municipalities; 11 of 18 at 70% and 16 of 18 at 80%. Panambi (0.751) and Não-Me-Toque (0.726) sit on the edge.
- **Cruz Alta:** wheat below 75% of trend in 5 of its 8 El Niño winters (1982, 1997, 2002, 2015, 2023); 1997 (0.746) and 2002 (0.745) by a hair. 2009 enters the El Niño group with ONI JJA = +0.50 exactly.
- **Was the signal visible before sowing?** The observed ONI was already at El Niño level in January–April in only 2 of the 8 winters (1987, 2015; JFM +1.13 and +0.65). In 2023 the JFM value was −0.33.

### Credit and alerts in 2023 (context, not evidence of a decision)

- **NOAA CPC** issued an **El Niño Watch on 13 April 2023** (62% chance of El Niño in May–July) and the **El Niño Advisory on 8 June 2023**; in March the status was "Final La Niña Advisory".
- **Wheat operating credit (SICOR, 18 municipalities):** financed area of January–October 2023 was +2.3% over 2022 (155,964 vs 152,465 ha), but the full-year **value was +0.5% nominal and −3.1% real** (BRL of Dec/2025, IPCA) and the full-year area −0.5%. So "credit stayed stable", not "credit rose". SICOR values for recent months may be revised by the source.

## Limitations

1. **The effective sample is the number of winters, not of municipal seasons.** 8 El Niño and 5 La Niña winters; the 18 municipalities share the weather and fail together. The 53.3% describes how widespread the loss was; the statistical evidence rests on the winter-level test (p = 0.003). Say "53% of municipal wheat seasons (8 El Niño winters, 18 municipalities)", never "53% of El Niño winters".
2. **The result depends on a few winters.** 1982, 2002, 2015 and 2023 carry most of the losses; 1987 had 0 of 16 and 2009 had 1 of 18.
3. **The soybean "inversion" does not hold as a rate.** The 6.5% (9/138) after El Niño vs 23.0% (20/87) after La Niña comes from single seasons: all 9 El Niño cases are 1987/88, and 15 of the 20 La Niña cases are 2022/23. Without 2022 the La Niña rate falls to 7.2%, below neutral (20.4%). The winter-level permutation gives **p = 0.40**: indistinguishable from chance. 2022/23 can be told as a **case** (soybean failed in 15 of 18 municipalities), not as a rate.
4. **The disaster Atlas does not hold as a rate either.** Municipal drought records ("Estiagem e Seca") in the soybean window (Nov–Apr) after La Niña vs after El Niño: 45.8% (33/72) vs 1.9% (2/108), counting all 18 municipalities in every year (47.1% counting only municipalities already created). 18 of the 33 La Niña cases are 2022 (18 of 18). **Without 2022: 15/54 = 27.8%, the same as neutral (27.3%).** The Atlas starts in 1991 (4 La Niña and 6 El Niño winters), records are municipal emergency decrees and not specific to soybean, and the propensity to register changed over time.
5. **The ONI is revised** when NOAA updates the ERSST base. 2009 enters with JJA = +0.50 exactly; a 0.01 revision removes it from the El Niño group. Since 2026 CPC verifies its outlooks with the relative index (RONI); this analysis uses the ONI.
6. **Forecasts issued in February do not beat "always neutral" on the phase.** See the next section. A strong historical link between El Niño and wheat losses does not by itself make the season predictable at sowing time.
7. **Yield is municipal (IBGE PAM), not field-level**, and the trend is a simple linear (or quadratic) fit. The association is statistical; this analysis does not establish the agronomic cause.
8. **Licenses:** IBGE data carry no CC licence (cite IBGE); the Atlas licence is not declared, so its derived counts are not committed; SICOR derivatives stay under ODbL.

## Forecast skill (optional part): do January–March forecasts get the JJA phase right?

Truth: ONI JJA with the same ±0.5 rule. Forecast phase: El Niño if the forecast Niño-3.4 anomaly is ≥ +0.5, La Niña if ≤ −0.5 (plume and NMME ensemble means); the most likely category for probability forecasts. "Always neutral" is the hit rate of someone who always says neutral. Full table (45 rows, every model) in `results/forecast_skill_metrics.csv`.

| Source | Issued | Years (n) | Phase hit rate (always neutral) | El Niño hits / observed | False alarm ratio, El Niño | r |
|---|---|---|---|---|---|---|
| CPC/IRI official consensus | Feb | 2014–2026 (13) | **0.69 (0.69)** | 1/3 | 0.00 | — |
| CPC/IRI official consensus | Mar | 2014–2026 (13) | 0.77 (0.69) | 2/3 | 0.33 | — |
| IRI objective probability | Feb | 2004–2026 (23) | 0.70 (0.74) | 3/4 | 0.40 | — |
| IRI plume, mean of all models | Feb | 2003–2026 (24) | **0.75 (0.75)** | 3/4 | 0.40 | 0.59 |
| IRI plume, NASA GMAO | Feb | 2003–2026 (24) | 0.50 (0.75) | 4/4 | 0.60 | 0.54 |
| NMME mean of 6 models (incl. NASA GEOS) | Feb | 1982–2022 (41) | 0.63 (0.71) | 5/7 | 0.38 | 0.75 |

- **February forecasts do not beat "always neutral" on the phase**: the official consensus ties it (0.69), the IRI plume mean ties it (0.75), the others fall below. The official February outlook favoured El Niño in only 1 of the 3 El Niño winters since 2014 (2023); it missed 2015 and 2026.
- **The chance of El Niño does rise in the right years**: the official February outlook gave on average 47% to El Niño in winters that became El Niño, against 23% in the others (IRI objective: 52% against 26%).
- **La Niña winters are almost never forecast** in January–March by the IRI plume mean (0 of 2).
- **The sample is tiny** (3 to 7 El Niño winters per source): one case moves a rate by 25 to 50 points; no confidence interval was computed.
- **How the values were read:** IRI plume and probability values are read from the coordinates of the archive SVG figures (about 0.01 °C precision; the y axis is calibrated on the 0 and ±0.5 reference lines because some 2003 figures have swapped tick labels); the IRI server regenerates the figures today, and they differ from the text published at the time by up to 4 points. The official table comes from the IRI quick looks (2014–2025; 2012–2013 return 404) and, for 2026, only from the favoured category in the CPC synopsis. NMME 1982–2010 is hindcast; the first target month of the NMME files was inferred from the shape of the annual cycle (14 of 18 model/month combinations agree), not from documentation. The ONI is used as truth, although CPC now verifies its outlooks with the RONI.

## Reproduce

From the repository root, with [uv](https://docs.astral.sh/uv/):

```bash
# main analysis (wheat, soybean, credit, Atlas, CPC alerts): downloads ~90 MB on the first run, a few minutes
uv run --with httpx==0.28.1 --with numpy==2.5.4 python -I analysis/enso-wheat/reproduce.py

# everything, including the forecast-skill part (~700 small files, one connection at a time)
uv run --with httpx==0.28.1 --with numpy==2.5.4 --with xarray --with netCDF4 \
  python -I analysis/enso-wheat/reproduce.py --forecasts
```

`reproduce.py` runs, in order:

| Step | Script | Output (`results/` unless noted) |
|---|---|---|
| 1 | [`fetch_sources.py`](fetch_sources.py) | raw IBGE, SIDRA, ONI and Atlas files in the raw folder, with access log |
| 2 | [`wheat_soy_enso.py`](wheat_soy_enso.py) | `wheat_soy_enso.json` (24 variants, per winter, permutation, 2023, Cruz Alta, coverage), `municipality_year.csv` (base case) |
| 3 | [`credit_sicor.py`](credit_sicor.py) | `credit_sicor.json` (ODbL) |
| 4 | [`disaster_atlas.py`](disaster_atlas.py) | `<raw>/derived/disaster_atlas.json` (not committed) |
| 5 | [`cpc_alerts_2023.py`](cpc_alerts_2023.py) | `cpc_alerts_2023.json` |
| 6–7 | [`forecast_skill/`](forecast_skill/) (`--forecasts`) | `forecast_skill_metrics.csv`, `forecast_skill.json`; per-forecast values in `<raw>/forecasts/forecasts_jja.csv` |

`results/run_info.json` records the run time and library versions. The scripts are linted with Ruff (`ruff.toml` here); they are outside the `services/science` package and its CI job.

### Check against the team's verification

The run of 2026-11-14 reproduced, to the last digit, the numbers of the team's independent verification (private planning repository, same day): 53.3% (73/137) vs 3.5% (3/86); p = 0.0031 for wheat and 0.4013 for soybean; 14/18 in 2023 (11 and 16 at 70% and 80%); all 24 variants; the 1,545 municipality-year rows; SICOR +2.3% / +0.5% / −3.1% / −0.5%; Atlas 33/72, 2/108 and 15/54; CPC Watch 13 April and Advisory 8 June 2023. The forecast-skill part reproduced all 45 rows of the team's metrics table (681 NMME files and the IRI archive downloaded again on 2026-11-14; the same 15 IRI requests failed as in the original: 2002–2003 figures return HTTP 500 and the 2012–2013 quick looks return 404). The original's snapshot of the current outlook for JJA 2027 (October/November 2026 issues) was not ported: it is not part of the skill measurement and changes every month.
