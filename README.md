# FieldShift

Team **FieldShift** · NASA Space Apps Challenge 2026 · *Field Shift: Adapting Farms with NASA Data* · Local Event: Florianópolis, Brazil.

> Work in progress during the hackathon (Nov 14–15, 2026). Project description, demo and live link will be added here.

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

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md). AI assistants: read [AGENTS.md](AGENTS.md).

## License
[Apache-2.0](LICENSE)
