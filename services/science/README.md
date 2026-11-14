# Science service (EECOM + GUIDO)

Offline Python pipeline (`fieldshift` CLI), managed with [uv](https://docs.astral.sh/uv/) on Python 3.12. Layout follows the architecture v0.1: code in `src/fieldshift/`, tests in `tests/`.

```bash
uv sync                      # create .venv from uv.lock
uv run fieldshift --version
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
```

- `ingest/`: NASA data ingestion and harmonization (EECOM) — to be moved under `src/fieldshift/` by the first data story
- `model/`: scoring, uncertainty, explanations (GUIDO) — idem
