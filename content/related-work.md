---
title: Related work
checked: "2026-11-14"
---

<!-- SI-assisted: compiled with Claude Code (Anthropic) from web sources checked on 2026-11-14; human review pending (see SI-USAGE.md). Facts only. "How we differ": the bold positioning line is the team's own wording (event rule C1); the prior-art facts under it were compiled with Claude Code from the Embrapa page, IN SPA/MAPA 2/2025 and the team's prior-art research (15 November 2026). -->

Tools, models and projects close to this challenge, grouped in the 11 categories of our competitive scan. Each entry says what the work is, in the words of its own source, with a link. Sources were checked on 2026-11-14.

## How we differ

**Not a new rating — a free preview of the official soil level, early enough to change the winter.**

The official ZarcNM level (NM1–NM4) is computed only by Embrapa's SINM, from data that accredited operators register at insurance time. Embrapa lists nine accredited geoprocessing operators that compute the satellite indicators field by field for insurers, banks and cooperatives: Audsat, Ensoag Consultoria Agrícola, Funarbe, Mapfre Seguros Gerais, Ruralservice, Satellus, The Soil Company, Visiona Tecnologia Espacial and 2M Inteligência Artificial ([Embrapa, Níveis de Manejo](https://www.embrapa.br/rede-zarc-embrapa/niveis-de-manejo), read 2026-11-15). The rule itself forbids a classification while any indicator is missing (IN SPA/MAPA 2/2025, Annex, item 2.2), and three of its six indicators need a soil laboratory. Embrapa Soja's [Documentos 454](https://www.infoteca.cnptia.embrapa.br/infoteca/bitstream/doc/1156802/1/DOC-454.pdf) (Franchini et al. 2023) publishes the remote-sensing method for the same three satellite indicators.

We did not find anyone offering that satellite half free and in public, for every property of the rural-property registry, before the season, and comparing winter strategies (searches of 15 November 2026; not found is not proof of absence). FieldShift does not classify: it shows which winter can reach NM3–NM4 on the satellite side and points to the soil laboratory and the accredited operators that close the official classification.

## 1. Cover crop selectors

- **[MCCC Cover Crop Decision Tool](https://midwestcovercrops.org/decision-tool/)** (Midwest Cover Crops Council). Cover crop selection for the US Midwest states and Ontario listed on the tool's credits page.
- **[NECCC Cover Crop Species Selector](https://northeastcovercrops.com/decision-tool/)** (Northeast Cover Crops Council). Helps users "narrow down which cover crops might work" for them in the US Northeast.
- **[WCCC Species Selector](https://westerncovercrops.org/decision-tools/)** (Western Cover Crops Council, with Precision Sustainable Agriculture; funded by USDA NRCS). Covers 13 western states, Nevada included ([UC ANR announcement](https://ucanr.edu/blog/food-blog/article/new-online-tool-helps-growers-choose-cover-crops)). It uses soil and climate data auto-populated for a location plus up to three user goals; species rankings come from expert ratings.
- **[Managing Cover Crops Profitably, 3rd edition](https://www.sare.org/resources/managing-cover-crops-profitably-3rd-edition/)** (SARE Outreach, 2007). Reference book on cover crop species, free to download.

Reuse note: none of the three selectors states a licence for its species data. The selector code ([precision-sustainable-ag/dst-selector](https://github.com/precision-sustainable-ag/dst-selector)) is MIT-licensed; that covers the code only.

## 2. Crop rotation generators

- **ROTAT**: Dogliotti, Rossing and van Ittersum (2003). "ROTAT, a tool for systematically generating crop rotations." *European Journal of Agronomy* 19(2), 239–250. [doi:10.1016/S1161-0301(02)00047-3](https://doi.org/10.1016/S1161-0301(02)00047-3)
- **ROTOR**: Bachinger and Zander (2007). Generation and assessment of crop rotations for organic farming systems. *European Journal of Agronomy* 26(2), 130–143. [doi:10.1016/j.eja.2006.09.002](https://doi.org/10.1016/j.eja.2006.09.002)
- **CropRota**: Schönhart, Schmid and Schneider (2011). "CropRota – A crop rotation model to support integrated land use assessments." *European Journal of Agronomy* 34, 263–277. [doi:10.1016/j.eja.2011.02.004](https://doi.org/10.1016/j.eja.2011.02.004)
- **Fenz et al. (2023)**: Fenz, Neubauer, Friedel and Wohlmuth. "AI- and data-driven crop rotation planning." *Computers and Electronics in Agriculture* 212, 108160. [doi:10.1016/j.compag.2023.108160](https://doi.org/10.1016/j.compag.2023.108160). A reinforcement-learning planner. In its limitations the paper says the suitability of a crop "may depend on the weather conditions, soil quality, or pest infestation of a specific year", inputs it treated as fixed, and that it did not consider more than one crop in the same field in the same year.

## 3. Crop simulation models

- **[AquaCrop-OS](https://github.com/aquacropos/aquacrop-matlab)**: "a free, open-source implementation of AquaCrop", the FAO crop-water productivity model (Apache-2.0). Not used in this project; listed as a candidate for future validation.
- **[APSIM](https://www.apsim.info/)**: agricultural systems simulation. Access is through licence agreements: free for general use, with fees for special (commercial) use ([download terms](https://www.apsim.info/download-apsim/)).
- **[DSSAT](https://dssat.net/)**: "dynamic crop growth simulation models for over 45 crops"; the cropping system model source is open under the BSD 3-Clause licence ([open source](https://dssat.net/about/open-source/)).

## 4. Sustainability and conservation practices

- **[COMET-Planner](https://comet-planner.com/)** (Colorado State University). Evaluates potential carbon sequestration and greenhouse gas reductions from adopting NRCS conservation practices.
- **[Fieldprint Platform](https://fieldtomarket.org/)** (Field to Market). Measures farm performance on eight environmental indicators.
- **[RUSLE2](https://www.nrcs.usda.gov/resources/tech-tools/water-erosion-rusle2)** (USDA NRCS; USDA ARS lead developer). "Estimates soil loss caused by rainfall and its associated overland flow."

## 5. Climate tools for agriculture

- **[U2U AgClimate View](https://mygeohub.org/groups/u2u/purdue_acv)** (Useful to Usable, hosted on MyGeoHub). Historical climate and crop yield data for the US Corn Belt.
- **[MRCC Corn GDD tool](https://mrcc.purdue.edu/tools/corngdd)** (Midwestern Regional Climate Center). Tracks real-time and historical growing degree day accumulation and spring and fall frost risk for corn.
- **[Cornell Climate Smart Farming](https://climatesmartfarming.org/)** (Northeast Regional Climate Center, Cornell University). Free, location-specific climate and weather tools for farmers in the US Northeast. The Water Deficit Calculator cited in our earlier notes was not found in the current tool list.

## 6. Water and evapotranspiration

- **[OpenET](https://etdata.org/)**: satellite-based evapotranspiration at 30 m. Data for 48 US states became available across all its tools on 15 December 2025 ([NASA Science](https://science.nasa.gov/blogs/science-news/2025/12/16/expanding-crucial-water-tracking/)). Terms: OpenET's [Terms of Service](https://etdata.org/terms-of-service/) grant a personal, non-commercial licence to its services; the Earth Engine catalogue lists the data as CC BY 4.0.
- **[FAO WaPOR](https://www.fao.org/in-action/remote-sensing-for-water-productivity/wapor-data-access/en)**: FAO's portal for water productivity from remote sensing (version 3 and version 2 available). Licence statements differ between sources; check before reuse.

## 7. Commercial and open satellite platforms

- **[OneSoil](https://onesoil.ai/)**: "turns satellite data and AI into practical, day-to-day farming decisions."
- **[EOSDA Crop Monitoring](https://eos.com/products/crop-monitoring/)**: remote field monitoring with satellite vegetation indices and weather data.
- **[OpTIS](https://www.ctic.org/OpTIS)** (co-developed by CTIC, Regrow and The Nature Conservancy): "an automated system to map tillage, residue cover, winter cover" across the contiguous US, published for 2015–2021.
- **[Climate FieldView](https://climate.com/)** (Climate LLC): farm data platform.
- **[Agrosmart](https://agrosmart.com.br/)**: climate and agronomic data and intelligence platform in Brazil.
- **[FarmVibes.AI](https://github.com/microsoft/farmvibes-ai)** (Microsoft Research, MIT licence): toolkit to "develop rich geospatial insights for agriculture and sustainability."

## 8. Brazilian public ecosystem

- **[ZARC](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico)** (Brazil's National Agricultural Climate Risk Zoning Programme, Ministry of Agriculture, with Embrapa): indicates planting periods by municipality and crop based on agroclimatic risk. **ZarcNM** (Management Levels) adds a classification of production areas into management levels, with methodology defined by Embrapa ([Instrução Normativa SPA/MAPA nº 2, 8 July 2025](https://www.gov.br/agricultura/pt-br/assuntos/riscos-seguro/programa-nacional-de-zoneamento-agricola-de-risco-climatico)).
- **[MapBiomas Agricultural Use](https://brasil.mapbiomas.org/)** (Collection 11): annual agricultural use maps of Brazil, 1985–2025, from 30 m land cover, plus a second-crop product. Public, open and free with attribution (CC BY 4.0).
- **[Embrapa SATVeg](https://www.satveg.cnptia.embrapa.br/)**: NDVI and EVI time series from MODIS (Terra and Aqua), 250 m, 16-day, since 2000, for Brazil and South America. API access through [Embrapa AgroAPI](https://www.agroapi.cnptia.embrapa.br/) requires app registration and an access token.
- **[Embrapa Comunicado Técnico 181](https://www.infoteca.cnptia.embrapa.br/handle/doc/1097400)** (Carvalho et al., Embrapa Cerrados, 2018): cover crops recommended for the corn off-season under no-till in the Cerrado.

## 9. AI for rural extension

- **[Farmer.Chat](https://digitalgreen.org/farmer.chat/)** (Digital Green): helps smallholder farmers "access trusted agricultural knowledge instantly", with advice tuned to local soils, crops and climate.

## 10. NASA programmes

Cited by name only, as related programmes; no endorsement is implied.

- **[NASA Acres](https://www.nasaacres.org/)**: an agriculture consortium launched in 2023 and led by the University of Maryland.
- **[NASA Harvest](https://www.nasaharvest.org/)**: "NASA's Global Food Supply and Agriculture Consortium."

## 11. NASA Space Apps 2024

From the [2024 Global Winners announcement](https://www.nasa.gov/learning-resources/stem-engagement-at-nasa/nasa-international-space-apps-challenge-announces-2024-global-winners/) (16 January 2025):

- **[NVS-knot, "2plant"](https://www.spaceappschallenge.org/nasa-space-apps-2024/find-a-team/nvs-knot/)**, Galactic Impact Award: assessed planting conditions using surface soil moisture (SMAP) and evapotranspiration (OpenET) data in an app to help farmers manage planting risk.
- **[GaamaRamma, "WaterWise"](https://www.spaceappschallenge.org/nasa-space-apps-2024/find-a-team/gaamaramma/)**, Best Use of Data Award: helps farmers manage water availability in the face of drought, pests and disease.
