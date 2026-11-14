# Science service (EECOM + GUIDO)

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See `SI-USAGE.md` at the repo root.

Offline Python pipeline (`fieldshift` CLI), managed with [uv](https://docs.astral.sh/uv/) on Python 3.12. Layout follows the architecture v0.1: code in `src/fieldshift/`, tests in `tests/`.

```bash
uv sync                      # create .venv from uv.lock
uv run fieldshift --version
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
```

- `ingest/`: NASA data ingestion and harmonization (EECOM) — moved under `src/fieldshift/` (`sources/`, `harmonize/`, `indices/`, `provenance/`, `io/`, `pipeline.py`) by the POWER story (#11)
- `model/`: scoring, uncertainty, explanations (GUIDO) — to be moved under `src/fieldshift/`

## NASA POWER layer (Story 2.2, issue #11)

```bash
uv run fieldshift fetch power --site dev-floripa             # DEV point, 1981-01-01 → end of last month (BRT)
uv run fieldshift fetch power --site dev-floripa --offline   # rebuild from data/cache only (what the CI checks)
uv run fieldshift fetch power --site <id>                    # real site: reads data/sites/<id>/input/site.yaml
uv run fieldshift fetch power --site dev-x --lat <lat> --lon <lon> [--start YYYY-MM-DD] [--end YYYY-MM-DD]
uv run fieldshift validate --all                             # contracts + VL1 data layer over data/ (CI step)
```

- **Source:** `GET https://power.larc.nasa.gov/api/temporal/daily/point`, community `AG`, one request per site (13 parameters, including modeled `GWETPROF` and `EVLAND` since contracts v1.1.0), retry with exponential backoff on network errors, 429 and 5xx; 4xx fails at once. No credentials.
- **Cache:** the raw response, wrapped with the request URL and the access time (BRT), goes to `data/cache/power/<site>/daily_<start>_<end>.json`. An existing file wins (idempotent); `--refresh` downloads again. A payload is checked (point, parameters, native units) before it is cached. The CI never calls the network: tests use `tests/fixtures/power/` and the committed cache.
- **Outputs:** `series.json` (`SeriesBundle`), `provenance.json` (`ProvenanceRegistry`) and `indices.json` (`ClimateIndices`), contracts v1.1.0, in `data/sites/<id>/output/` for real sites and in `data/dev/<id>/output/` for DEV sites (`dev-*`), which `scripts/sync-data.mjs` does not publish.
- **Monthly rule (ADR-3):** sum for precipitation and ET0, mean for the rest. A month gets a value only when every day of it is valid; otherwise `null` with `q: "gap"` and a `known_gaps` entry. POWER's fill value `-999` is read as missing, never as a number.
- **ET0:** FAO-56 Penman-Monteith, daily, in plain Python (`fieldshift.indices.et0`), tested against FAO-56 Examples 8 and 18. pyet 1.5.0 was not used: it requires `pandas<3.0` and xarray (stack: pandas 3.1.1). Inputs: Tmax, Tmin, dewpoint (ea, eq. 14), wind at 2 m, all-sky shortwave, surface pressure, and the elevation of the POWER cell. Its provenance record is `computed`, with `inputs` pointing to the six POWER records and `method.doc_anchor = "et0-fao56"`.
- **Climate indices (issue #22, `fieldshift.indices.climate`):** computed on daily data, then summed per month (ADR-3), each with a `computed` provenance record whose `method.parameters` holds the thresholds and whose `inputs` point to the POWER/ET0 records:

  | Index (`variable_key` / `index_key`) | Daily rule | Monthly | Reference |
  |---|---|---|---|
  | `heat_days` | Tmax > `heat_tmax_c` | count (days) | ETCCDI form (SU uses 25 °C) |
  | `frost_days` | Tmin ≤ `frost_tmin_c` (0 °C) | count (days) | architecture; ETCCDI FD uses < 0 °C |
  | `growing_degree_days` | max(0, (Tmax + Tmin)/2 − `gdd_base_c`) | sum (degC_d) | McMaster & Wilhelm 1997, method 1 |
  | `water_deficit` | ET0 − precipitation (> 0 = deficit) | sum (mm) | FAO-56 ET0 |
  | `extreme_precip_days` / `extreme_precip_total` | precip > P95 of wet days (≥ 1 mm) in 1991–2020 | count / sum (mm) | ETCCDI R95p / R95pTOT (Zhang et al. 2011); percentile Hyndman & Fan type 7 |

  `indices.json` holds, for each index and for ET0, the 1991–2020 profile by civil month and the annual mean (a month or a year is null/omitted unless every year of the baseline has a value), plus the P95 threshold itself. The extreme indices are skipped when the record does not cover the whole baseline.
- **Thresholds are parameters, not decisions.** Defaults: heat 35 °C (architecture example), frost 0 °C, GDD base 10 °C, wet day 1 mm, P95, baseline 1991–2020. A real site overrides `heat_tmax_c`, `frost_tmin_c` and `gdd_base_c` in `data/sites/<id>/input/site.yaml`:

  ```yaml
  indices:
    heat_tmax_c: 34      # agronomist, per site
    gdd_base_c: 10       # per crop once the crops are decided (D9)
  ```
  When a default is used, the provenance says so ("generic default, not a crop- or site-specific value"). Unknown keys fail.
- **`fieldshift validate --all`** (ADR-8 layer 1, CI): every JSON under `data/sites` and `data/dev` must have a known file name and match its contract; `schema_version` same major and not newer than the code; site id = folder; every `provenance_id`/`provenance_ids` and every record `inputs` exists in the site registry, without cycles; FR19 fields per data type; a series/metric/profile has the `data_type` of its record. A `method.doc_anchor` without a page in `content/methods/` is a warning here (the web unit test from #24 makes it a failure). The indices are documented in `content/methods/climate-indices.md`.
- **Provenance merge:** `fetch power` merges `provenance.json` by `provenance_id` (records of other stages, e.g. rotation, are kept; same id is replaced).
- **Dev point:** `dev-floripa` (−27.6, −48.5) is for development only and is NOT a demo site. Real sites (brasil, nevada) come from SURGEON (issue #8).

### Why `EVPTRNS` is not ingested

Live checks on 2026-11-14 (POWER Daily API v2.10.3, community AG, year 2023):

| Point | `EVPTRNS` Jan / Jul mean (MJ/m²/day) | `EVLAND` Jan / Jul mean (mm/day) |
|---|---|---|
| −27.6, −48.5 (dev point) | 0.001 / 0.0 | 4.35 / 1.53 |
| −27.6, −49.2 (next cell west) | 10.07 / 2.63 | 5.91 / 1.93 |
| −27.6, −48.0 (next cell east) | 0.0 / 0.0 | 4.55 / 1.75 |
| 42.0, −93.6 (US Midwest probe) | 0.002 / 2.97 | 0.31 / 3.03 |

The monthly endpoint gave 0.0 for all 117 months of 2015–2023 at the dev point. POWER names it "Evapotranspiration Energy Flux", but in the MERRA-2 land diagnostics `EVPTRNS` is the transpiration energy flux only (bare-soil and interception evaporation are separate variables). The values swing between neighbouring cells and disagree with `EVLAND` in the same cell, so the parameter is not usable as "ET" for a site. `EVLAND` (modeled land evaporation, mm/day) looks plausible and is ingested as `evap_land_modeled` (monthly sum, `modeled`) since contracts v1.1.0, with a limitation saying it is not the field's actual ET.
