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
```

- **Source:** `GET https://power.larc.nasa.gov/api/temporal/daily/point`, community `AG`, one request per site (11 parameters), retry with exponential backoff on network errors, 429 and 5xx; 4xx fails at once. No credentials.
- **Cache:** the raw response, wrapped with the request URL and the access time (BRT), goes to `data/cache/power/<site>/daily_<start>_<end>.json`. An existing file wins (idempotent); `--refresh` downloads again. A payload is checked (point, parameters, native units) before it is cached. The CI never calls the network: tests use `tests/fixtures/power/` and the committed cache.
- **Outputs:** `series.json` (`SeriesBundle`) and `provenance.json` (`ProvenanceRegistry`), contracts v1.0.0, in `data/sites/<id>/output/` for real sites and in `data/dev/<id>/output/` for DEV sites (`dev-*`), which `scripts/sync-data.mjs` does not publish.
- **Monthly rule (ADR-3):** sum for precipitation and ET0, mean for the rest. A month gets a value only when every day of it is valid; otherwise `null` with `q: "gap"` and a `known_gaps` entry. POWER's fill value `-999` is read as missing, never as a number.
- **ET0:** FAO-56 Penman-Monteith, daily, in plain Python (`fieldshift.indices.et0`), tested against FAO-56 Examples 8 and 18. pyet 1.5.0 was not used: it requires `pandas<3.0` and xarray (stack: pandas 3.1.1). Inputs: Tmax, Tmin, dewpoint (ea, eq. 14), wind at 2 m, all-sky shortwave, surface pressure, and the elevation of the POWER cell. Its provenance record is `computed`, with `inputs` pointing to the six POWER records and `method.doc_anchor = "et0-fao56"`.
- **Event indices:** `fieldshift.indices.events` flags heat days (threshold per site, from `site.yaml`) and frost days (Tmin ≤ 0 °C) on daily data, to be counted per month before aggregation. They are not written yet: the contract has no `VariableKey` for them (they belong in `ClimateIndices`).
- **Dev point:** `dev-floripa` (−27.6, −48.5) is for development only and is NOT a demo site. Real sites (brasil, nevada) come from SURGEON (issue #8). `dev-cruz-alta` is a candidate location (issue #26), also DEV only, written to `data/dev/cruz-alta/`.

## IBGE PAM (issue #26)

```bash
uv run fieldshift fetch ibge-pam --municipality 4306106 --out-dir ../../data/dev/cruz-alta/ibge [--product 2713] [--offline] [--refresh]
```

`fieldshift.sources.ibge_pam` reads SIDRA table 1612 (IBGE aggregates API v3, no credentials): planted and harvested area, production and yield of one temporary crop (default soybean, category 2713) in one municipality, every year. It writes the wrapped raw response, a CSV and a plain provenance JSON. SIDRA `-` is zero; `..`, `...`, `X` are empty. Official statistics have no data type or units in contracts v1.0.0, so these are not contract files.

### Why `EVPTRNS` is not ingested

Live checks on 2026-11-14 (POWER Daily API v2.10.3, community AG, year 2023):

| Point | `EVPTRNS` Jan / Jul mean (MJ/m²/day) | `EVLAND` Jan / Jul mean (mm/day) |
|---|---|---|
| −27.6, −48.5 (dev point) | 0.001 / 0.0 | 4.35 / 1.53 |
| −27.6, −49.2 (next cell west) | 10.07 / 2.63 | 5.91 / 1.93 |
| −27.6, −48.0 (next cell east) | 0.0 / 0.0 | 4.55 / 1.75 |
| 42.0, −93.6 (US Midwest probe) | 0.002 / 2.97 | 0.31 / 3.03 |

The monthly endpoint gave 0.0 for all 117 months of 2015–2023 at the dev point. POWER names it "Evapotranspiration Energy Flux", but in the MERRA-2 land diagnostics `EVPTRNS` is the transpiration energy flux only (bare-soil and interception evaporation are separate variables). The values swing between neighbouring cells and disagree with `EVLAND` in the same cell, so the parameter is not usable as "ET" for a site. `EVLAND` (modeled land evaporation, mm/day) looks plausible but has no contract key; adding it would be a contract change.
