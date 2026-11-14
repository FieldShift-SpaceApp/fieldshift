# DEV data (not demo sites)

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See [`SI-USAGE.md`](../../SI-USAGE.md).

**Everything under `data/dev/` is for development only.** These are not demo sites, are not listed in `data/sites/index.json` and are not copied to the app by `scripts/sync-data.mjs` (which publishes `data/sites/*/output` only). Every provenance record here carries the limitation "DEV ONLY: development point, not a demo site."

| Site id | Point (lat, lon) | Why | Regenerate |
|---|---|---|---|
| `dev-floripa` | −27.6, −48.5 | develop and test the NASA POWER layer (issue #11) while the real sites come from SURGEON (issue #8) | `cd services/science && uv run fieldshift fetch power --site dev-floripa --offline` (from the committed cache) or without `--offline` and with `--refresh` (new download) |
| `dev-cruz-alta` (folder `cruz-alta/`) | −28.703, −53.563 (IBGE centroid of municipality 4306106) | CANDIDATE location teammates are working with (issue #26): IBGE boundary, NASA POWER, IBGE PAM soybean; pending D-001/#8 | see [`cruz-alta/README.md`](cruz-alta/README.md) |

The raw POWER responses are in `data/cache/power/<site id>/`. Data: NASA POWER (see `RESOURCES.md` for the citation and terms).
