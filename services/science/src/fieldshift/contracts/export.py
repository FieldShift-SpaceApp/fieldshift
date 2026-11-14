"""`fieldshift contracts export`: pydantic -> JSON Schema 2020-12 with shared $defs (ADR-4).

TypeScript is generated from this file by json-schema-to-typescript
(`npm run gen -w packages/contracts`). Both artifacts are committed; CI checks drift with
`git diff --exit-code`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic.json_schema import GenerateJsonSchema, models_json_schema

from fieldshift.contracts import SCHEMA_VERSION, TOP_LEVEL_MODELS

SCHEMA_RELPATH = Path("packages") / "contracts" / "schema" / "contracts.schema.json"


class _ContractsJsonSchema(GenerateJsonSchema):
    def field_title_should_be_set(self, schema: Any) -> bool:
        # A per-field title becomes a useless alias in the generated TS ("export type StartMonth").
        return False


def build_schema() -> dict[str, Any]:
    _, schema = models_json_schema(
        [(model, "validation") for model in TOP_LEVEL_MODELS],
        ref_template="#/$defs/{model}",
        schema_generator=_ContractsJsonSchema,
    )
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "FieldShiftContracts",
        "description": (
            f"FieldShift data contracts v{SCHEMA_VERSION}. Generated from the pydantic models in "
            "services/science/src/fieldshift/contracts by `fieldshift contracts export`. "
            "Do not edit by hand."
        ),
        "$defs": dict(sorted(schema["$defs"].items())),
    }


def render(schema: dict[str, Any]) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False) + "\n"


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "packages" / "contracts" / "package.json").is_file():
            return candidate
    raise FileNotFoundError(f"repo root (packages/contracts) not found above {start}")


def export(out: Path | None = None) -> Path:
    target = out if out is not None else find_repo_root(Path.cwd()) / SCHEMA_RELPATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(build_schema()))
    return target
