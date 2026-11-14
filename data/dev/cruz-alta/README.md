# Cruz Alta (RS): candidate location (DEV ONLY)

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See [`SI-USAGE.md`](../../../SI-USAGE.md).

**Status: CANDIDATE, not a demo site.** Teammates are working with Cruz Alta (RS) and soybean (issue #26). This folder prepares the location so the team can decide; it decides nothing. Whether it becomes a site, and what the product does with it, is a human decision (D-001, issue #8, rule C1). Nothing here is under `data/sites/`, so `scripts/sync-data.mjs` does not publish it to the app.

## What is here

| File | What | Source |
|---|---|---|
| `ibge/localidades_municipio_4306106.json` | municipality record: **IBGE code 4306106** = Cruz Alta, RS (confirmed on the RS list of 497 municipalities; only one "Cruz Alta") | IBGE localidades API v1 |
| `ibge/malha_municipio_4306106_2022.geojson` | official municipal boundary, 2022 mesh, maximum quality (1 Polygon, 993 vertices) | IBGE malhas API v3 |
| `ibge/malha_municipio_4306106_2022.metadados.json` | IBGE centroid (−28.703, −53.5626) and area (1,360.548 km²) | IBGE malhas API v3 |
| `ibge/geo.provenance.json` | URLs, mesh version, sha256, access times (BRT), centroid cross-check | — |
| `ibge/pam_1612_4306106_2713.{raw.json,csv,provenance.json}` | soybean planted/harvested area, production and yield, 1974–2025 | IBGE PAM, SIDRA table 1612 |
| `output/series.json`, `output/provenance.json` | NASA POWER daily 1981-01-01 → 2026-10-31 at the centroid, as monthly series + ET0 (contracts v1.0.0, every record marked "DEV ONLY") | NASA POWER Daily API, community AG |
| `drought_check.py` | prints the yield/rainfall table below from the committed files | — |

The raw POWER response (3.0 MB) is in `data/cache/power/dev-cruz-alta/`.

**POWER point.** The CLI site id is `dev-cruz-alta` (the `dev-` prefix is what keeps it out of `data/sites/`). The point is the IBGE centroid rounded to the 3 decimals POWER echoes back: (−28.703, −53.563), about 40 m from the IBGE value. POWER returns the value of the grid cell that contains it (meteorology 0.5° × 0.625°, radiation 1° × 1°), a regional signal, not a field measurement.

**PAM table.** Table 1612 is the right one: "Área plantada, área colhida, quantidade produzida, rendimento médio e valor da produção das lavouras temporárias", annual 1974–2025, last updated 23/10/2026 (metadata checked on 2026-11-14). Soybean is category 2713 ("Soja (em grão)") of classification 81. Variables: 109 planted area (ha), 216 harvested area (ha), 214 production (t), 112 average yield (kg/ha). Planted area has no value (SIDRA "...") for 1974–1987. A PAM year is the harvest year: 2022 is the 2021/22 season.

## Regenerate

```bash
cd services/science
uv run fieldshift fetch power --site dev-cruz-alta --offline        # from the committed cache
uv run fieldshift fetch ibge-pam --municipality 4306106 --out-dir ../../data/dev/cruz-alta/ibge --offline
uv run python ../../data/dev/cruz-alta/drought_check.py              # tables below
```

Drop `--offline` (and add `--refresh`) to download again. The boundary files were downloaded with the URLs in `ibge/geo.provenance.json`.

## Drought figures quoted by a teammate: check

Claim: "2022 with 1,337 kg/ha against 3,920 kg/ha the year before" and "drought in 4 of the last 14 seasons".

Windows used for this check (an analysis convention here, not a project decision): rainfall summed over Nov–Mar and Dec–Feb of the season that ends in the PAM year; reference = the 1991–2020 mean of the same window in the same POWER series (Nov–Mar 738.8 mm, Dec–Feb 455.0 mm). Precipitation is `PRECTOTCORR`, no gaps in 1981-01 → 2026-10.

| Harvest year (safra) | Yield kg/ha | % of 2012–2025 median | Nov–Mar mm | % of 1991–2020 | Dec–Feb mm | % of 1991–2020 |
|---|---|---|---|---|---|---|
| 2012 (2011/12) | 960 | 33% | 319.2 | 43% | 204.4 | 45% |
| 2013 (2012/13) | 2720 | 93% | 670.7 | 91% | 433.9 | 95% |
| 2014 (2013/14) | 2456 | 84% | 681.5 | 92% | 380.7 | 84% |
| 2015 (2014/15) | 3149 | 107% | 659.3 | 89% | 495.6 | 109% |
| 2016 (2015/16) | 3514 | 120% | 1131.9 | 153% | 738.7 | 162% |
| 2017 (2016/17) | 3567 | 122% | 816.4 | 111% | 488.1 | 107% |
| 2018 (2017/18) | 3507 | 120% | 816.8 | 111% | 435.3 | 96% |
| 2019 (2018/19) | 3639 | 124% | 781.9 | 106% | 387.6 | 85% |
| 2020 (2019/20) | 2142 | 73% | 465.7 | 63% | 241.5 | 53% |
| 2021 (2020/21) | 3920 | 134% | 475.7 | 64% | 302.1 | 66% |
| 2022 (2021/22) | 1337 | 46% | 442.9 | 60% | 181.5 | 40% |
| 2023 (2022/23) | 1943 | 66% | 309.9 | 42% | 185.2 | 41% |
| 2024 (2023/24) | 3671 | 125% | 1021.3 | 138% | 460.0 | 101% |
| 2025 (2024/25) | 2389 | 81% | 472.6 | 64% | 322.7 | 71% |

Median yield 2012–2025: 2,934.5 kg/ha. Sources: IBGE PAM table 1612 (accessed 2026-11-14 14:40 BRT); NASA POWER Daily API v2.10.3, community AG (accessed 2026-11-14 14:39 BRT).

**Verdict.**

1. **2022 = 1,337 kg/ha and 2021 = 3,920 kg/ha: confirmed** by PAM (−66%). Harvested area was about the same (91,500 ha → 92,200 ha); production fell from 358,650 t to 123,240 t. In POWER, 2021/22 had 60% of the 1991–2020 Nov–Mar rainfall and 40% of the Dec–Feb rainfall.
2. **"Drought in 4 of the last 14 seasons": not confirmed as a fixed fact; the count depends on the definition**, and none is given. With the data above: yield below 70% of the 2012–2025 median gives 3 seasons (2012, 2022, 2023); below 75% gives 4 (adds 2020); Nov–Mar rainfall below 70% of 1991–2020 gives 6 (2012, 2020, 2021, 2022, 2023, 2025); Dec–Feb below 70% gives 5 (2012, 2020, 2021, 2022, 2023). Requiring both yield below 75% of the median and Nov–Mar rainfall below 70% gives exactly 4: **2012, 2020, 2022, 2023**. 2025 is borderline (81% yield, 64% Nov–Mar rain).
3. Rainfall totals alone do not line up with yield every year: 2020/21 had 64% of normal Nov–Mar rainfall in POWER and the highest yield of the 14 years (3,920 kg/ha). Season totals hide timing within the season, and the POWER cell is regional. These data show co-occurrence, not cause.

## Candidate retrospective event (Story 2.5)

**CANDIDATE, pending the team (D-001/#8):** soybean season 2021/22 in Cruz Alta (RS), IBGE 4306106.

- Yield 1,337 kg/ha (2022) vs 3,920 kg/ha (2021) and a 2012–2025 median of 2,934.5 kg/ha (IBGE PAM 1612).
- NASA POWER at the municipal centroid: Nov 2021–Mar 2022 rainfall 442.9 mm (60% of the 1991–2020 mean); Dec 2021–Feb 2022 181.5 mm (40%).
- Other low seasons in the same window, for comparison: 2011/12 (960 kg/ha; 43% Nov–Mar rain) and 2022/23 (1,943 kg/ha; 42%).
- Not checked here: whether the event is used, which window or index defines it, and any official drought declaration for the municipality.

Data: NASA POWER (see `RESOURCES.md` for the citation and terms) and IBGE (public data; cite IBGE as the source).
