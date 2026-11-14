"""`fieldshift contracts export` (ADR-4): pydantic → JSON Schema 2020-12, $defs compartilhados."""

import json
import re
from pathlib import Path

from fieldshift.cli import main
from fieldshift.contracts import SCHEMA_VERSION, TOP_LEVEL_MODELS
from fieldshift.contracts.export import build_schema

REPO_ROOT = Path(__file__).resolve().parents[3]

EXPECTED_DEFS = {
    # documentos de topo
    "ProvenanceRegistry", "Site", "SitesIndex", "SeriesBundle", "ClimateIndices",
    "RotationFile", "StrategySet", "SiteManifest", "ValidationFile",
    # modelos citados no Data Models
    "Provenance", "TimeSeries", "Metric", "MonthlyProfile", "Rotation", "RotationSegment",
    "RotationTimeline", "Evidence", "Confidence", "Strategy", "RetrospectiveCheck",
    "LocalizedText", "Ref", "Period", "GeoJSONPolygon", "LayerStatus",
    # aliases semânticos
    "SiteId", "ProvenanceId", "SeriesId", "DataType", "CanonicalUnit", "VariableKey",
    "LayerId", "LayerReasonCode", "Month", "SchemaVersion", "IndexKey",
}  # fmt: skip


def test_schema_has_all_defs():
    schema = build_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    missing = EXPECTED_DEFS - set(schema["$defs"])
    assert not missing, missing


def test_crop_and_ranker_are_not_contracts_yet():
    # ⏸ D9/D7: dependem do conceito (DECISIONS.md)
    assert not {"Crop", "Ranker", "RankedStrategy"} & set(build_schema()["$defs"])


def test_top_level_documents_carry_schema_version():
    schema = build_schema()
    for model in TOP_LEVEL_MODELS:
        props = schema["$defs"][model.__name__]
        assert "schema_version" in props["required"], model.__name__


def test_field_titles_are_dropped():
    # títulos de campo virariam aliases inúteis no TS gerado (json2ts)
    text = json.dumps(build_schema())
    assert '"title": "Start Month"' not in text


def test_refs_resolve():
    schema = build_schema()
    refs = set(re.findall(r'"\$ref": "#/\$defs/([^"]+)"', json.dumps(schema)))
    assert refs <= set(schema["$defs"])


def test_cli_writes_schema(tmp_path):
    out = tmp_path / "contracts.schema.json"
    assert main(["contracts", "export", "--out", str(out)]) == 0
    raw = out.read_bytes()
    assert b"\r\n" not in raw and raw.endswith(b"\n")
    assert json.loads(raw) == build_schema()


def test_export_is_deterministic(tmp_path):
    a, b = tmp_path / "a.json", tmp_path / "b.json"
    main(["contracts", "export", "--out", str(a)])
    main(["contracts", "export", "--out", str(b)])
    assert a.read_bytes() == b.read_bytes()


def test_ts_contract_major_matches_python():
    index_ts = (REPO_ROOT / "packages" / "contracts" / "ts" / "index.ts").read_text("utf-8")
    match = re.search(r"CONTRACT_MAJOR\s*=\s*(\d+)", index_ts)
    assert match, "CONTRACT_MAJOR missing in packages/contracts/ts/index.ts"
    assert int(match.group(1)) == int(SCHEMA_VERSION.split(".")[0])
