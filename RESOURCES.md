# Resources

> **SI-assisted:** written with Claude Code (Anthropic) from the team's data source map (live access and license checks of 2026-11-14); human review pending. See [`SI-USAGE.md`](SI-USAGE.md).

Every dataset, resource and tool used by the project. Feeds the submission page ("NASA data used" + "all data, resources and tools") and the Data & Methods page (Story 1.4). Owners: EECOM (datasets) + SURGEON (agronomic sources). Methods live in [`content/methods/`](content/methods/).

**Status:** `selected` = will be used whatever the concept (Epic 2) · `candidate` = inventoried and tested, used only if the concept needs it (decided after `D-001` in [`DECISIONS.md`](DECISIONS.md)). When a candidate is adopted, change its status and fill "Feeds" in the same PR as the code that reads it. Never list a number in the app whose dataset is not here (AGENTS.md §2.5). **"Analysis only (fieldshift-hq), not yet in the app"** in "Feeds" = used in the team's analyses (scripts and tables in the private planning repository `FieldShift-SpaceApp/fieldshift-hq`, checked on 2026-11-14); no app code reads it yet, and no number from it is shown in the app except as cited text on the Data & Methods page.

**License rule (repo is Apache-2.0):** Apache-2.0 covers our code only. Data or derived data committed to the repo keeps its original license and must be attributed here. Column "In git?" says whether derived data may be committed: **yes** (open license, with attribution) · **no** (non-commercial, restricted or unclear: link to the source or fetch at run time, never commit) · **check** (license not confirmed: confirm on the provider's page before committing).

## NASA datasets

Terms for every NASA row unless stated otherwise: [NASA Earthdata data use guidance](https://www.earthdata.nasa.gov/engage/open-data-services-software-policies/data-use-guidance): data from NASA-led missions are CC0 unless marked; no restriction on use; citation strongly requested. Access legend: open = no account · Earthdata = free [Earthdata Login](https://urs.earthdata.nasa.gov).

| Dataset | Product / version | Variable | Resolution | Period | URL | Terms of use | Feeds | Status |
|---|---|---|---|---|---|---|---|---|
| **NASA POWER** | POWER Daily API v2.10.3, community `AG` (upstream: MERRA-2 for meteorology and soil wetness, CERES SYN1deg for radiation) | ingested by `fieldshift fetch power`: `T2M`, `T2M_MAX`, `T2M_MIN`, `T2MDEW`, `RH2M`, `WS2M`, `ALLSKY_SFC_SW_DWN`, `PRECTOTCORR`, `PS`, modeled soil wetness `GWETTOP`, `GWETROOT`, `GWETPROF` and modeled land evaporation `EVLAND` (contracts v1.1.0, issue #22) | meteorology 0.5° × 0.625°, radiation 1° × 1° ([methodology](https://power.larc.nasa.gov/docs/methodology/)); daily | 1981 → present (radiation from 1984-01 at the dev point; 1981–1983 is fill value) | https://power.larc.nasa.gov/ | open, no account. Cite both: "The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division." and "The data was obtained from the POWER Project's Daily 2.10.3 version on YYYY/MM/DD." (template from the [referencing guide](https://power.larc.nasa.gov/docs/referencing/), filled with the Daily API version returned on 2026-11-14); the project asks to be notified of publications and redistribution. **`EVPTRNS` is not used:** POWER labels it "Evapotranspiration Energy Flux" (MJ/m²/day), but in MERRA-2 `EVPTRNS` is the *transpiration* energy flux only; live checks on 2026-11-14 gave ~0 all year in the Florianópolis cell while the neighbouring cell gave ~10 MJ/m²/day and `EVLAND` gave ~4 mm/day (details in `services/science/README.md`). ET0 is computed with FAO-56 instead | monthly climate series, ET0 (FAO-56) and climate indices (heat/frost days, GDD, water deficit, P95 extremes) of each site, `data/sites/<id>/output/` (`fieldshift fetch power`; Story 2.2); DEV point in `data/dev/` | selected |
| MERRA-2 | `M2T1NXSLV` v5.12.4 | meteorological reanalysis (base of POWER) | ~0.5°, hourly | 1980 → | https://search.earthdata.nasa.gov/search?q=M2T1NXSLV | Earthdata | — | candidate |
| NEX-GDDP-CMIP6 | NCCS / AWS Open Data, v2.0 | downscaled climate projections (CMIP6; e.g. `tasmax` under SSP2-4.5) | 0.25° grid, daily (seen in a point test) | historical + SSP scenarios (span to confirm on the product page) | https://registry.opendata.aws/nex-gddp-cmip6/ | open; **CC0** (AWS Registry) | — | candidate |
| SMAP L3 | `SPL3SMP_E` | surface soil moisture (observed) | 9 km, daily | 2015 → | https://search.earthdata.nasa.gov/search?q=SPL3SMP_E | Earthdata | — | candidate |
| SMAP L4 | `SPL4SMGP` | surface and root-zone soil moisture | 9 km, 3-hourly | 2015 → | https://search.earthdata.nasa.gov/search?q=SPL4SMGP | Earthdata | — | candidate |
| GPM IMERG | Final / Late, daily and monthly; also served by the NASA POWER Daily API as `IMERG_PRECTOT` (daily, UTC; the API does not report the run or version) | precipitation | 0.1°, daily / monthly | 1998 → (Final to Sep 2025; Late to present) | https://search.earthdata.nasa.gov/search?q=GPM%20IMERG | Earthdata (via POWER: open, no account) | analysis only (fieldshift-hq), not yet in the app: `IMERG_PRECTOT` from the POWER API in the ground check against rain gauges at Cruz Alta, 1998–2025 ([method](content/methods/satellite-vs-ground.md)) | candidate |
| GLDAS Noah | `GLDAS_NOAH025_3H`, `GLDAS_NOAH025_M` | modeled soil moisture by layer, ET, runoff | 0.25°, 3-hourly / monthly | 2000 → | https://search.earthdata.nasa.gov/search?q=GLDAS_NOAH025_M | Earthdata | — | candidate |
| GRACE / GRACE-FO | JPL mascon | terrestrial water storage anomaly | ~300 km effective, monthly | 2002 → (gap 2017–18) | https://search.earthdata.nasa.gov/search?q=GRACE%20mascon%20JPL | Earthdata | — | candidate |
| MODIS vegetation indices | `MOD13Q1` (Terra), `MYD13Q1` (Aqua), v061; DOIs 10.5067/MODIS/MOD13Q1.061 and 10.5067/MODIS/MYD13Q1.061 (NASA LP DAAC) | NDVI, EVI | 250 m, 16-day | 2000 → | https://search.earthdata.nasa.gov/search?q=MOD13Q1 · read through the Microsoft Planetary Computer STAC, collection [`modis-13Q1-061`](https://planetarycomputer.microsoft.com/dataset/modis-13Q1-061) (anonymous access; Jul–Nov 2025 composites missing there on 2026-11-14) | Earthdata (or via AppEEARS); via Planetary Computer the NASA terms still apply | analysis only (fieldshift-hq), not yet in the app: winter cover and summer NDVI over Cruz Alta, tile h13v11 | candidate |
| VIIRS vegetation indices | `VNP13A1` | NDVI, EVI (MODIS continuity) | 500 m, 16-day | 2012 → | https://search.earthdata.nasa.gov/search?q=VNP13A1 | Earthdata | — | candidate |
| HLS | `HLSL30`, `HLSS30` | harmonized Landsat/Sentinel-2 reflectance (field-scale NDVI) | 30 m, 2–3 days | 2013 → | https://search.earthdata.nasa.gov/search?q=HLSL30 | Earthdata | — | candidate |
| MODIS land cover | `MCD12Q1` | annual land cover class | 500 m, annual | 2001 → | https://search.earthdata.nasa.gov/search?q=MCD12Q1 | Earthdata | — | candidate |
| MODIS phenology | `MCD12Q2` | green-up, peak, dormancy | 500 m, annual | 2001 → | https://search.earthdata.nasa.gov/search?q=MCD12Q2 | Earthdata | — | candidate |
| MODIS ET | `MOD16A2GF` | evapotranspiration | 500 m, 8-day | 2000 → | https://search.earthdata.nasa.gov/search?q=MOD16A2GF | Earthdata | — | candidate |
| ECOSTRESS | `ECO_L3T_JET` (ET), LST | evapotranspiration, land surface temperature | 70 m, irregular | 2018 → | https://search.earthdata.nasa.gov/search?q=ECOSTRESS | Earthdata | — | candidate |
| MODIS LST | `MOD11A2` | land surface temperature | 1 km, 8-day | 2000 → | https://search.earthdata.nasa.gov/search?q=MOD11A2 | Earthdata | — | candidate |
| GFSAD | `GFSAD30SACE`, `GFSAD1KCM` | cropland mask (South America); irrigated vs rainfed | 30 m (~2015) / 1 km (~2010) | static | https://search.earthdata.nasa.gov/search?q=GFSAD30SACE | Earthdata | — | candidate |
| SRTM / NASADEM | `SRTMGL1`, NASADEM | elevation → slope | 30 m | 2000 | https://search.earthdata.nasa.gov/search?q=SRTMGL1 | Earthdata | — | candidate |
| OPERA DSWx-HLS | `OPERA_L3_DSWX-HLS_V1` | surface water | 30 m | 2016 → | https://search.earthdata.nasa.gov/search?q=OPERA%20DSWx-HLS | Earthdata | — | candidate |
| GIBS / Worldview | WMTS imagery | ready-made map imagery (no numeric values) | tiles | varies | https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/gibs-api | open | — | candidate |
| NASA GMAO GEOS-S2S | GEOS-S2S seasonal forecasts: hindcasts 1982–2022 through the NMME (model label `NASA_GEOS5v2`) and real-time forecasts 2003–2026 through the IRI ENSO plume ("NASA GMAO"); GEOS-S2S-3 output listed on the NCCS datashare (not used for numbers) | Niño-3.4 forecast for June–August | index; 0.5° grid for the GEOS-S2S-3 files | 1982 → | https://gmao.gsfc.nasa.gov/cc/research/subseasonal/ | open (NCCS datashare, no account); GMAO calls the system "experimental"; NASA data use guidance | analysis only (fieldshift-hq), not yet in the app: skill of El Niño forecasts issued in January–March for the following winter | candidate |
| AppEEARS | service | point/area extraction of MODIS, VIIRS, SMAP and others | per product | per product | https://appeears.earthdatacloud.nasa.gov/ | Earthdata | — | candidate (fallback extraction path) |

Not a guaranteed path: ORNL MODIS Subsets returned HTTP 503 on 2026-11-14 (`D-000/CO-4`).

## Other data

| Dataset | Provider | URL | License / terms | In git? | Feeds | Status |
|---|---|---|---|---|---|---|
| ERA5 / ERA5-Land | ECMWF / Copernicus C3S | https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land | CC BY 4.0 (CDS catalog); free account and per-dataset license acceptance | yes | — | candidate |
| C3S / ESA CCI Soil Moisture | ESA / Copernicus C3S | https://climate.esa.int/en/projects/soil-moisture/ | CC BY 4.0 (C3S) | yes | — | candidate |
| ESA WorldCover | ESA | https://esa-worldcover.org/en/data-access | CC BY 4.0 | yes | — | candidate |
| Sentinel-2 L2A (Earth Search) | ESA Copernicus, via Element 84 | https://earth-search.aws.element84.com/v1 | Sentinel Data Legal Notice: free use with attribution "Contains modified Copernicus Sentinel data [year]" | yes | — | candidate |
| CHIRPS v3.0 (Funk et al. 2026, [doi:10.1038/s41597-026-07096-4](https://doi.org/10.1038/s41597-026-07096-4)) | UCSB Climate Hazards Center | https://www.chc.ucsb.edu/data/chirps3 · daily CHIRPS also read through [SERVIR ClimateSERV](https://climateserv.servirglobal.net/) (version not declared; not v3) | public domain / CC BY 4.0 (v2.0 is offline) | yes | analysis only (fieldshift-hq), not yet in the app: v3 monthly municipal mean of Cruz Alta 1981–2025; daily ClimateSERV series in the ground check ([method](content/methods/satellite-vs-ground.md)) | candidate |
| MapBiomas Collection 11 | MapBiomas | https://brasil.mapbiomas.org/download/ | CC BY 4.0; rasters only via Google Earth Engine (download suspended), municipal statistics as XLSX | yes | — | candidate |
| ZARC (agricultural climate risk zoning) | MAPA (Brazil) | https://dados.agricultura.gov.br/dataset/tabua-de-risco-zoneamento-agricola-de-risco-climatico | Creative Commons Attribution (CKAN metadata) | yes | analysis only (fieldshift-hq), not yet in the app: sowing windows and the frost criterion cited from the ZARC ordinances for Rio Grande do Sul (wheat, soybean, oat); Cruz Alta's ten-day periods not extracted yet | candidate |
| IBGE PAM / SIDRA | IBGE | https://servicodados.ibge.gov.br/api/v3/agregados/1612/metadados | public federal data; cite IBGE (no CC license seen) | yes, cite source | DEV only: `fieldshift fetch ibge-pam` (table 1612) for the Cruz Alta DEV candidate, `data/dev/dev-cruz-alta/`; analysis (fieldshift-hq): soybean and wheat yield, area and low-yield seasons | candidate |
| INMET weather stations | INMET | https://portal.inmet.gov.br/dadoshistoricos | public federal data; cite INMET (license not confirmed) | check | analysis only (fieldshift-hq), not yet in the app: automatic stations A853 (Cruz Alta, 2007–2025), A883 and A886 in the ground check ([method](content/methods/satellite-vs-ground.md)) | candidate |
| ANA HidroWeb (rain gauges) | ANA (Brazil's National Water and Sanitation Agency) / SGB-CPRM | https://www.snirh.gov.br/hidroweb/ · legacy web service https://telemetriaws1.ana.gov.br/ServiceANA.asmx (`HidroSerieHistorica`, no account) | public federal data; cite ANA (license not confirmed) | check | analysis only (fieldshift-hq), not yet in the app: daily rain of gauges 2853015, 2853005 and 2853014 (raw, consistency level 1) in the ground check | candidate |
| CONAB historical series | CONAB | https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/safras/series-historicas | public federal data; cite CONAB (license not confirmed) | check | — | candidate |
| CONAB production costs | CONAB | https://www.gov.br/conab/pt-br/atuacao/informacoes-agropecuarias/custos-de-producao | public federal data; cite CONAB (no formal license found on the page) | check | analysis only (fieldshift-hq), not yet in the app: wheat and soybean cost per hectare at Cruz Alta (series change method in 2022) | candidate |
| NOAA CPC ENSO: Oceanic Niño Index and official ENSO outlook | NOAA Climate Prediction Center | https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt · https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/enso_advisory/ensodisc.shtml | US government work, public domain | yes | analysis only (fieldshift-hq), not yet in the app: ENSO phase of each season; skill of the official outlook | candidate |
| NMME (North American Multi-Model Ensemble) | NOAA CPC and partner centres | https://www.cpc.ncep.noaa.gov/products/NMME/ (files on the CPC FTP/HTTP server, no account) | cite Kirtman et al. (2014); license text not found | check | analysis only (fieldshift-hq), not yet in the app: Niño-3.4 hindcasts of 6 models, 1982–2022 | candidate |
| IRI ENSO forecast (plume and objective probabilities) | IRI, Columbia University | https://iri.columbia.edu/our-expertise/climate/forecasts/enso/current/ | page CC BY 4.0; IRI states it no longer provides forecast data (values read from its figures) | yes, with attribution | analysis only (fieldshift-hq), not yet in the app: skill of ENSO forecasts 2003–2026 | candidate |
| BCB SICOR, rural credit data matrix (`CusteioMunicipioProduto`) | Banco Central do Brasil | https://dadosabertos.bcb.gov.br/dataset/matrizdadoscreditorural | ODbL (attribution; a derived database must stay under ODbL) | yes, under ODbL | analysis only (fieldshift-hq), not yet in the app: financed wheat and oat area by municipality, 2016 → | candidate |
| Atlas Digital de Desastres no Brasil | MIDR / SEDEC (Brazil) | https://atlasdigital.mdr.gov.br/paginas/downloads.xhtml | **license not declared** on the download page | **check** | analysis only (fieldshift-hq), not yet in the app: disaster records (drought, flash floods, windstorms, heavy rain, hail) of 18 municipalities of the Planalto Médio (RS), 1991–2025 | candidate |
| INPE BDC (CBERS-4/4A, Amazonia-1) | INPE / AEB | https://data.inpe.br/stac/browser/ | CBERS/Amazonia: CC BY 4.0; Sentinel-2/Landsat cubes follow ESA/USGS terms | yes | — | candidate |
| ISRIC SoilGrids 2.0 | ISRIC | https://soilgrids.org | CC BY 4.0 (not confirmed in this session); point REST queries returned `null` on 2026-11-14 (use WCS/VRT) | check | — | candidate |
| **HWSD v2.0** | FAO / IIASA | https://www.fao.org/soils-portal/data-hub/soil-maps-and-databases/harmonized-world-soil-database-v20/en/ | **license not confirmed** (catalog says "Unknown"; possibly CC BY-NC-SA 3.0 IGO): treat as non-commercial | **no** | — | candidate |
| **FAO GAEZ v4 / v5** | FAO / IIASA | https://gaez.fao.org/ | **non-commercial use only** (GAEZ v4 terms; CC BY-NC-SA 3.0 IGO per a secondary source): incompatible with committing to an Apache-2.0 repo | **no** | — | candidate |
| FAOSTAT | FAO | https://www.fao.org/faostat/ | CC BY 4.0 (not confirmed); bulk download open, API needs a token | check | — | candidate |
| FAO WaPOR v3 | FAO | https://data.apps.fao.org/wapor/ | CC BY 4.0 (not confirmed) | check | — | candidate |
| Open-Meteo Historical | Open-Meteo (serves ERA5) | https://open-meteo.com/en/terms | data CC BY 4.0; **free API is non-commercial only**, < 10,000 calls/day | yes (data), API terms apply | — | candidate |
| Embrapa SATVeg / AgroAPI | Embrapa (derived from NASA MODIS: NDVI/EVI, 250 m, 16-day, 2000 →) | https://www.satveg.cnptia.embrapa.br/ | portal terms: all rights reserved (Brazilian Law 9.610); the API needs app registration, a consumer key/secret and an access token, under AgroAPI's "Termo de Acesso e Uso" ([AgroAPI](https://www.agroapi.cnptia.embrapa.br/), checked 2026-11-14) | **no** | — | candidate |
| **CEPEA/ESALQ price indicators** | CEPEA (USP) | https://cepea.org.br/br/politica-de-direitos-autorais-1.aspx | **restricted**: retransmission requires formal authorization | **no** | — | candidate |
| SAGE crop calendar (Sacks et al. 2010) | University of Wisconsin–Madison | https://sage.nelson.wisc.edu/data-and-models/datasets/crop-calendar-dataset/ | no explicit license on the page; authors ask for an email | **no** (until confirmed) | — | candidate |
| USDA Cropland Data Layer (US only) | USDA NASS | https://www.nass.usda.gov/Research_and_Science/Cropland/SARS1a.php | US government, public domain (not confirmed) | check | — | candidate (Nevada site) |
| SSURGO / Web Soil Survey (US only) | USDA NRCS | https://websoilsurvey.nrcs.usda.gov/ | US government, public domain (not confirmed) | check | — | candidate (Nevada site) |
| OpenET (30 m; 48 US states since 2025-12-15, per [NASA Science](https://science.nasa.gov/blogs/science-news/2025/12/16/expanding-crucial-water-tracking/)) | OpenET | https://etdata.org/ | **conflicting terms** (checked 2026-11-14): the [OpenET Terms of Service](https://etdata.org/terms-of-service/) grant a personal, non-commercial licence to the services (API key required); the Earth Engine catalogue lists the data as CC BY 4.0. Resolve with OpenET before committing any derived value | **no** (until resolved) | — | candidate (Nevada site) |
| Cover crop selectors: MCCC, NECCC, WCCC (US) | Midwest / Northeast / Western Cover Crops Councils | https://midwestcovercrops.org/decision-tool/ · https://northeastcovercrops.com/decision-tool/ · https://westerncovercrops.org/decision-tools/ | **no licence statement for the species data** found on the tools or council sites (checked 2026-11-14); the selector code ([precision-sustainable-ag/dst-selector](https://github.com/precision-sustainable-ag/dst-selector)) is MIT, which covers code only. Cite as related work; do not copy species ratings | **no** | related work (`content/related-work.md`) | reference only |
| USGS Water Data (US only) | USGS | https://api.waterdata.usgs.gov/ | US government, public domain (not confirmed); legacy NWIS `gwlevels` service is off | check | — | candidate (Nevada site) |

Also restricted, never commit (details in the team's source map): CEAGESP (all rights reserved), Agritempo (raw data restricted), EPAGRI/CIRAM, Infoagro and CIIAGRO (no open license), CABI (CC BY-NC-ND). Personal data is never committed raw (rural insurance PSR, SICAR per property, water-rights owners, GBIF/iNaturalist observer names): aggregates only.

## Tools and libraries

Versions as pinned in the lockfiles (`package-lock.json`, `services/science/uv.lock`); licenses read from each package's metadata (npm / PyPI).

| Tool / library | Version | License | URL | Used for |
|---|---|---|---|---|
| Next.js | 16.4.6 | MIT | https://nextjs.org | web app (static generation) |
| React / React DOM | 19.3.1 | MIT | https://react.dev | UI |
| TypeScript | 6.0.3 | Apache-2.0 | https://www.typescriptlang.org | types |
| Tailwind CSS | 4.3.5 | MIT | https://tailwindcss.com | styles |
| shadcn (CLI) | 4.23.0 | MIT | https://ui.shadcn.com | component scaffolding |
| radix-ui | 1.8.1 | MIT | https://www.radix-ui.com | accessible UI primitives |
| lucide-react | 1.73.0 | ISC | https://lucide.dev | icons |
| class-variance-authority | 0.7.1 | Apache-2.0 | https://cva.style | component variants |
| cn | 0.5.2 | MIT | https://www.npmjs.com/package/cn | class name helper |
| tw-animate-css | 1.4.0 | MIT | https://www.npmjs.com/package/tw-animate-css | animations |
| react-markdown + remark-gfm | 10.1.0 + 4.0.1 | MIT | https://github.com/remarkjs/react-markdown | Data & Methods page rendered from this file, `SI-USAGE.md` and `content/` (no raw HTML) |
| gray-matter | 4.0.3 | MIT | https://github.com/jonschlinkert/gray-matter | front-matter of `content/methods/*.md` |
| yaml | 2.9.1 | ISC | https://eemeli.org/yaml/ | reading `content/glossary.yaml` |
| ESLint + eslint-config-next | 9.39.5 + 16.4.6 | MIT | https://eslint.org | lint |
| Vitest | 5.1.0 | MIT | https://vitest.dev | unit tests |
| Vite + @vitejs/plugin-react | 8.3.8 + 6.3.0 | MIT | https://vite.dev | test transform (Vitest) |
| Testing Library (react, dom) | 16.3.3, 10.4.2 | MIT | https://testing-library.com | component tests |
| jsdom | 29.1.1 | MIT | https://github.com/jsdom/jsdom | DOM for unit tests |
| Playwright | 1.65.1 | Apache-2.0 | https://playwright.dev | end-to-end tests (Chromium) |
| Node.js | 24.x | MIT | https://nodejs.org | runtime |
| Python | 3.12 | PSF-2.0 | https://www.python.org | science pipeline |
| uv | 0.11.3 | MIT OR Apache-2.0 | https://docs.astral.sh/uv/ | Python packaging |
| pydantic | 2.14.3 | MIT | https://docs.pydantic.dev | data contracts and validation |
| httpx | 0.28.1 | BSD-3-Clause | https://www.python-httpx.org | NASA POWER REST client (pipeline only) |
| PyYAML | 6.0.3 | MIT | https://pyyaml.org | reading human-written `site.yaml` |
| FAO-56 Penman-Monteith (method) | Allen et al. 1998 | FAO publication | https://www.fao.org/4/x0490e/x0490e00.htm | daily ET0 from NASA POWER (`fieldshift.indices.et0`) |
| ETCCDI climate extremes indices (method) | Zhang et al. 2011, doi:10.1002/wcc.147 | scientific publication | https://etccdi.pacificclimate.org/list_27_indices.shtml | heat/frost day form and P95 extreme precipitation (R95p, R95pTOT) (`fieldshift.indices.climate`) |
| Growing degree-days, method 1 (method) | McMaster & Wilhelm 1997, doi:10.1016/S0168-1923(97)00027-0 | scientific publication | https://doi.org/10.1016/S0168-1923(97)00027-0 | GDD with configurable base (`fieldshift.indices.climate`) |
| Sample quantiles, type 7 (method) | Hyndman & Fan 1996, doi:10.1080/00031305.1996.10473566 | scientific publication | https://doi.org/10.1080/00031305.1996.10473566 | P95 threshold (`fieldshift.indices.climate`) |
| pytest | 9.2.0 | MIT | https://pytest.org | Python tests |
| Ruff | 0.17.5 | MIT | https://docs.astral.sh/ruff/ | Python lint and format |
| gitleaks | 8.30.1 | MIT | https://github.com/gitleaks/gitleaks | secret scan in CI |
| GitHub Actions | — | service terms | https://github.com/features/actions | CI |

## AI usage
See [SI-USAGE.md](SI-USAGE.md).
