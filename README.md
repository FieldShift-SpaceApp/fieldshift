# FieldShift

> **SI-assisted:** written with Claude Code (Anthropic); human review pending. See `SI-USAGE.md` at the repo root.

Team **FieldShift** · NASA Space Apps Challenge 2026 · *Field Shift: Adapting Farms with NASA Data* · Local Event: Florianópolis, Brazil.

> Work in progress during the hackathon (Nov 14–15, 2026). **Live app (farmer-facing):** https://fieldshift-spaceapp.vercel.app · **Data & Methods (pipeline, provenance):** https://fieldshift-data.vercel.app/data-methods — project description and demo will be added here.

## Repository layout

| Path | What |
|---|---|
| `apps/web/` | Web app |
| `services/science/` | Data ingestion and model |
| `packages/contracts/` | Data contracts between pipeline and app (generated JSON Schema + TS types, fixtures) |
| `data/crops/` | Curated crop base, every attribute with a source |
| `data/sites/` | Per-site inputs (written by people) and pipeline outputs |
| `data/cache/` | Small raw extracts from the sources (large raw files are not committed) |
| `content/methods/` | Methods and limitations |
| `RESOURCES.md` | Datasets, resources and tools, with licenses |
| `DECISIONS.md` | Human decisions log |
| `coord/` | Team coordination: status per front |
| `SI-USAGE.md` | How AI ("SI") tools were used |

## Run locally

Prerequisites: Node.js 24 (`.nvmrc`), npm 11, [uv](https://docs.astral.sh/uv/) ≥ 0.11 (installs Python 3.12 by itself).

```bash
npm ci                                   # JS dependencies (npm workspaces: apps/*, packages/*)
npm run dev                              # web app on http://localhost:3000
uv sync --directory services/science     # Python 3.12 venv for the science pipeline
uv run --directory services/science fieldshift --version
```

Checks (same as CI): `npm run lint`, `npm run typecheck`, `npm run build`, `npm run py:lint`, `npm run py:test`, `npm run hygiene`.

## NASA data and credits

The app's climate base is [NASA POWER](https://power.larc.nasa.gov/) (Daily API, community `AG`). Every dataset, library and font, with its license, is in [RESOURCES.md](RESOURCES.md); methods and limitations are in [`content/methods/`](content/methods/); AI use is in [SI-USAGE.md](SI-USAGE.md).

> The data was obtained from National Aeronautics and Space Administration (NASA) Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project funded through the NASA Earth Science Division. The data was obtained from the POWER Project's Daily 2.10.3 version on 2026/11/14.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). AI assistants: read [AGENTS.md](AGENTS.md).

## License
[Apache-2.0](LICENSE)
