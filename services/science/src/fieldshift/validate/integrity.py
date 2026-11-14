# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""`fieldshift validate --all`: contracts and VL1 data layer over every JSON in data/ (ADR-8).

Checks, per site folder (`data/sites/<id>/output/` and `data/dev/<id>/output/`):
1. every JSON file has a known contract (by file name) and validates against it (pydantic);
2. `schema_version` has the major of the code and is not newer than the code;
3. the document's site id matches its folder;
4. every `provenance_id` / `provenance_ids` / record `inputs` points to a record in the site's
   `provenance.json`, and the lineage graph has no cycle;
5. every record has the FR19 fields required for its data type (stated here again, field by
   field, so the report says which field is missing);
6. a series, metric or profile has the same `data_type` as the record it points to.

`method.doc_anchor` values without a page in `content/methods/` are reported as warnings: the
method pages (VL6) belong to GUIDO + SURGEON and are not written yet.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from fieldshift.contracts import (
    SCHEMA_VERSION,
    ClimateIndices,
    Provenance,
    ProvenanceRegistry,
    RotationFile,
    SeriesBundle,
    Site,
    SiteManifest,
    SitesIndex,
    StrategySet,
    ValidationFile,
)

# Published file names (architecture, API Specification).
SITE_FILES: dict[str, type[BaseModel]] = {
    "manifest.json": SiteManifest,
    "site.json": Site,
    "provenance.json": ProvenanceRegistry,
    "series.json": SeriesBundle,
    "indices.json": ClimateIndices,
    "rotation-current.json": RotationFile,
    "validation.json": ValidationFile,
    "strategies.json": StrategySet,
}
SITES_INDEX = "index.json"  # data/sites/index.json -> SitesIndex
TRACED_TYPES = ("series", "metrics", "profiles")  # items whose data_type must match the record


@dataclass
class Report:
    checked: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def render(self) -> str:
        lines = [f"validate: {len(self.checked)} file(s) checked"]
        lines += [f"  ok      {p}" for p in self.checked]
        lines += [f"  ERROR   {e}" for e in self.errors]
        lines += [f"  warning {w}" for w in self.warnings]
        verdict = "FAILED" if self.errors else "passed"
        counts = f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"
        lines.append(f"validate: {verdict} ({counts})")
        return "\n".join(lines)


def _version_problem(version: str) -> str | None:
    have = tuple(int(x) for x in version.split("."))
    code = tuple(int(x) for x in SCHEMA_VERSION.split("."))
    if have[0] != code[0]:
        return f"schema_version {version}: major differs from the code ({SCHEMA_VERSION})"
    if have > code:
        return f"schema_version {version} is newer than the code ({SCHEMA_VERSION})"
    return None


def iter_refs(node: Any, path: str = "") -> Iterator[tuple[str, str]]:
    """Every (json path, provenance id) under `node`: `provenance_id` and `provenance_ids` keys."""
    if isinstance(node, dict):
        for key, value in node.items():
            here = f"{path}.{key}" if path else key
            if key == "provenance_id" and isinstance(value, str):
                yield here, value
            elif key == "provenance_ids" and isinstance(value, list):
                yield from ((f"{here}[{i}]", v) for i, v in enumerate(value) if isinstance(v, str))
            else:
                yield from iter_refs(value, here)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from iter_refs(value, f"{path}[{i}]")


def fr19_problems(rec: Provenance) -> list[str]:
    """FR19 fields by data type (architecture, Provenance completeness table)."""
    out: list[str] = []

    def need(ok: bool, what: str) -> None:
        if not ok:
            out.append(f"{rec.id} ({rec.data_type}): missing {what}")

    need(bool(rec.title.en.strip()), "title")
    need(bool(rec.variable.code and rec.variable.name.en.strip()), "variable code/name")
    need(bool(rec.spatial.resolution.strip()), "spatial.resolution")
    need(bool(rec.aggregation.en.strip()), "aggregation")
    if rec.data_type in ("satellite_observed", "modeled"):
        src, acc = rec.source, rec.access
        need(src is not None and all(s.strip() for s in (src.dataset, src.provider, src.product)),
             "source dataset/provider/product")  # fmt: skip
        need(src is not None and bool(src.version or src.collection_id),
             "source.version or source.collection_id")  # fmt: skip
        need(acc is not None and bool(acc.url or acc.doi), "access.url or access.doi")
        need(acc is not None and bool(acc.accessed_at), "access.accessed_at")
        need(acc is not None and bool(acc.terms_url), "access.terms_url")
    elif rec.data_type == "computed":
        need(rec.method is not None and bool(rec.method.doc_anchor), "method.doc_anchor")
        need(bool(rec.inputs), "inputs (>= 1)")
    elif rec.data_type == "user_provided":
        need(bool(rec.authored_by), "authored_by")
        need(bool(rec.refs), "refs (>= 1)")
    return out


def _cycles(records: dict[str, Provenance]) -> list[str]:
    state: dict[str, int] = {}  # 1 = visiting, 2 = done
    found: list[str] = []

    def visit(node: str, trail: list[str]) -> None:
        if state.get(node) == 2 or node not in records:
            return
        if state.get(node) == 1:
            found.append(" -> ".join([*trail[trail.index(node) :], node]))
            return
        state[node] = 1
        for nxt in records[node].inputs:
            visit(nxt, [*trail, node])
        state[node] = 2

    for rid in sorted(records):
        visit(rid, [])
    return found


FRONT_MATTER = re.compile(r"^---\s*\n(.*?)\n---\s*(?:\n|$)", flags=re.S)


def method_anchors(methods_dir: Path) -> set[str]:
    """`anchor` values in the YAML front matter of content/methods/*.md."""
    anchors: set[str] = set()
    if not methods_dir.is_dir():
        return anchors
    for md in sorted(methods_dir.glob("*.md")):
        m = FRONT_MATTER.match(md.read_text(encoding="utf-8"))
        if not m:
            continue
        try:
            front = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError:
            continue
        if isinstance(front, dict) and isinstance(front.get("anchor"), str):
            anchors.add(front["anchor"].strip())
    return anchors


def _load(path: Path, model: type[BaseModel], label: str, report: Report) -> BaseModel | None:
    try:
        doc = model.model_validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        first = "; ".join(
            f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in exc.errors()[:5]
        )
        report.errors.append(f"{label}: does not match {model.__name__}: {first}")
        return None
    except (OSError, ValueError) as exc:
        report.errors.append(f"{label}: unreadable JSON ({exc})")
        return None
    problem = _version_problem(doc.schema_version)
    if problem:
        report.errors.append(f"{label}: {problem}")
    return doc


def validate_site_dir(out_dir: Path, site_id: str, root: Path, report: Report) -> set[str]:
    """Validate one output folder. Returns the doc anchors its records use."""
    docs: dict[str, BaseModel] = {}
    for path in sorted(out_dir.glob("*.json")):
        label = path.relative_to(root).as_posix()
        model = SITE_FILES.get(path.name)
        if model is None:
            report.errors.append(f"{label}: unknown file name, no contract for it")
            continue
        doc = _load(path, model, label, report)
        if doc is None:
            continue
        doc_site = doc.id if isinstance(doc, Site) else doc.site_id
        if doc_site != site_id:
            report.errors.append(f"{label}: site id {doc_site!r} != folder {site_id!r}")
        docs[path.name] = doc
        report.checked.append(label)

    prefix = out_dir.relative_to(root).as_posix()
    registry = docs.get("provenance.json")
    records: dict[str, Provenance] = registry.records if registry is not None else {}
    used_anchors: set[str] = set()
    for rid, rec in records.items():
        for problem in fr19_problems(rec):
            report.errors.append(f"{prefix}/provenance.json: FR19 {problem}")
        for inp in rec.inputs:
            if inp not in records:
                report.errors.append(f"{prefix}/provenance.json: {rid} input {inp} has no record")
        if rec.method is not None:
            used_anchors.add(rec.method.doc_anchor)
    for cycle in _cycles(records):
        report.errors.append(f"{prefix}/provenance.json: lineage cycle {cycle}")

    for name, doc in docs.items():
        if name == "provenance.json":
            continue
        dumped = doc.model_dump(mode="json")
        for where, ref in iter_refs(dumped):
            if ref not in records:
                report.errors.append(f"{prefix}/{name}: {where} -> {ref} has no provenance record")
        for kind in TRACED_TYPES:
            for i, item in enumerate(dumped.get(kind, []) if isinstance(dumped, dict) else []):
                rec = records.get(item.get("provenance_id", ""))
                if rec is not None and item.get("data_type") not in (None, rec.data_type):
                    report.errors.append(
                        f"{prefix}/{name}: {kind}[{i}] data_type {item['data_type']!r} != "
                        f"record {rec.id} data_type {rec.data_type!r}"
                    )
    return used_anchors


def validate_all(data_dir: Path, methods_dir: Path) -> Report:
    report = Report()
    root = data_dir.parent
    anchors = method_anchors(methods_dir)
    used: set[str] = set()
    site_dirs: list[tuple[Path, str]] = []
    for group in ("sites", "dev"):
        base = data_dir / group
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.json")):
            rel = path.relative_to(base)
            if group == "sites" and rel.as_posix() == SITES_INDEX:
                if _load(path, SitesIndex, path.relative_to(root).as_posix(), report):
                    report.checked.append(path.relative_to(root).as_posix())
            elif len(rel.parts) != 3 or rel.parts[1] != "output":
                report.errors.append(
                    f"{path.relative_to(root).as_posix()}: JSON outside <site>/output/, "
                    "no contract for it"
                )
        for site in sorted(p for p in base.iterdir() if p.is_dir()):
            if (site / "output").is_dir():
                site_dirs.append((site / "output", site.name))
    for out_dir, site_id in site_dirs:
        used |= validate_site_dir(out_dir, site_id, root, report)
    for anchor in sorted(used - anchors):
        report.warnings.append(
            f"method.doc_anchor {anchor!r} has no page in content/methods/ yet "
            "(VL6; GUIDO + SURGEON)"
        )
    if not report.checked and not report.errors:
        report.warnings.append("no JSON found under data/sites or data/dev")
    return report
