# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Rotation stage: input/rotation-current.yaml + site ag year -> output/rotation-current.json.

The two provenance records (agronomist input, derived timeline) are merged into the site's
output/provenance.json, keeping the records other stages wrote there.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from fieldshift.contracts import (
    SCHEMA_VERSION,
    ProvenanceRegistry,
    Rotation,
    RotationFile,
)
from fieldshift.errors import PipelineError
from fieldshift.io.store import write_model
from fieldshift.provenance.rotation import (
    rotation_prov_id,
    rotation_record,
    soil_cover_record,
)
from fieldshift.rotation.inputs import RotationInput, load_ag_year, load_rotation_input
from fieldshift.rotation.timeline import derive_timeline
from fieldshift.sites import DEV_PREFIX, SITE_ID

ROTATION_FILE = "rotation-current.yaml"
OUTPUT_FILE = "rotation-current.json"


@dataclass(frozen=True)
class RotationOutputs:
    rotation_path: Path
    provenance_path: Path
    file: RotationFile


def site_dir(data_dir: Path, site_id: str) -> Path:
    if not SITE_ID.match(site_id):
        raise PipelineError(f"invalid site id {site_id!r} (expected {SITE_ID.pattern})")
    return data_dir / ("dev" if site_id.startswith(DEV_PREFIX) else "sites") / site_id


def build_rotation(
    site_id: str, spec: RotationInput, start_month: int
) -> tuple[RotationFile, ProvenanceRegistry]:
    """Pure step: validated input -> RotationFile and its two provenance records (no I/O)."""
    dev = site_id.startswith(DEV_PREFIX)
    rotation = Rotation(
        id=spec.id,
        site_id=site_id,
        name=spec.name,
        kind="current",
        cycle_years=spec.cycle_years,
        segments=spec.segments,
        data_type="user_provided",
        provenance_id=rotation_prov_id(site_id),
    )
    try:
        timeline = derive_timeline(rotation, start_month, reference_ag_year=spec.reference_ag_year)
    except ValueError as exc:
        raise PipelineError(f"{site_id}/{ROTATION_FILE}: {exc}") from exc
    period = timeline.bare_months_per_year.period
    refs = [ref for seg in spec.segments for ref in seg.refs]
    records = {
        r.id: r
        for r in (
            rotation_record(site_id, spec.authored_by, refs, period, dev),
            soil_cover_record(site_id, period, dev),
        )
    }
    file = RotationFile(
        schema_version=SCHEMA_VERSION, site_id=site_id, rotation=rotation, timeline=timeline
    )
    return file, ProvenanceRegistry(schema_version=SCHEMA_VERSION, site_id=site_id, records=records)


def merge_registry(path: Path, new: ProvenanceRegistry) -> ProvenanceRegistry:
    """Existing records stay; records with the same id are replaced by the new ones."""
    if not path.is_file():
        return new
    old = ProvenanceRegistry.model_validate(json.loads(path.read_text(encoding="utf-8")))
    if old.site_id != new.site_id:
        raise PipelineError(f"{path}: site_id {old.site_id!r} != {new.site_id!r}")
    return ProvenanceRegistry(
        schema_version=SCHEMA_VERSION,
        site_id=new.site_id,
        records={**old.records, **new.records},
    )


def run_rotation(site_id: str, *, data_dir: Path) -> RotationOutputs:
    base = site_dir(data_dir, site_id)
    ag_year = load_ag_year(base / "input" / "site.yaml", site_id)
    spec = load_rotation_input(base / "input" / ROTATION_FILE)
    file, registry = build_rotation(site_id, spec, ag_year.start_month)
    out = base / "output"
    provenance_path = out / "provenance.json"
    merged = merge_registry(provenance_path, registry)
    return RotationOutputs(
        rotation_path=write_model(file, out / OUTPUT_FILE),
        provenance_path=write_model(merged, provenance_path),
        file=file,
    )
