# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""Human-written inputs of the rotation stage (architecture, "Entradas escritas por humanos").

`rotation-current.yaml` is written by the agronomist (SURGEON, issue #8). It is validated here and
every error names the file, the line and the field. Nothing in this module has a default value for
an agronomic decision.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import ConfigDict, Field, ValidationError, model_validator

from fieldshift.contracts.common import Contract, LocalizedText
from fieldshift.contracts.rotation import RotationSegment
from fieldshift.contracts.site import AgYear
from fieldshift.errors import PipelineError


class RotationInput(Contract):
    """`data/sites/<id>/input/rotation-current.yaml`."""

    id: str = Field(min_length=1)
    name: LocalizedText
    cycle_years: int = Field(ge=1)
    # Agricultural year the cycle starts in (e.g. 2025 = the 2025/26 season when it is split).
    # Only dates the bare-soil metric; the monthly states do not depend on it.
    reference_ag_year: int = Field(ge=1900, le=2100)
    authored_by: str = Field(min_length=1)
    segments: list[RotationSegment] = Field(min_length=1)

    @model_validator(mode="after")
    def _every_segment_cites_a_source(self) -> RotationInput:
        # Story 2.3, AC3: each crop and each planting/harvest window cites its source.
        missing = [s.id for s in self.segments if not s.refs]
        if missing:
            raise ValueError(f"segments without refs (Story 2.3, AC3): {', '.join(missing)}")
        return self


class _SiteAgYear(Contract):
    """The only part of site.yaml this stage reads; other keys are validated by their stage."""

    model_config = ConfigDict(extra="ignore")
    id: str
    ag_year: AgYear


def _line_of(root: yaml.Node | None, loc: tuple[Any, ...]) -> int | None:
    """1-based line of the deepest YAML node that `loc` reaches (pydantic error location)."""
    node, line = root, (root.start_mark.line + 1) if root is not None else None
    for part in loc:
        child = None
        if isinstance(node, yaml.MappingNode):
            child = next((v for k, v in node.value if k.value == str(part)), None)
        elif isinstance(node, yaml.SequenceNode) and isinstance(part, int):
            child = node.value[part] if 0 <= part < len(node.value) else None
        if child is None:
            break
        node, line = child, child.start_mark.line + 1
    return line


def load_yaml_model[M: Contract](path: Path, model: type[M]) -> M:
    """Parse and validate a human-written YAML file; errors carry `file:line field: message`."""
    if not path.is_file():
        raise PipelineError(f"{path} not found")
    text = path.read_text(encoding="utf-8")
    try:
        raw = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise PipelineError(f"{path}: invalid YAML: {exc}") from exc
    try:
        return model.model_validate(raw if raw is not None else {})
    except ValidationError as exc:
        root = yaml.compose(text)
        lines = []
        for err in exc.errors():
            loc = tuple(err["loc"])
            field = ".".join(str(p) for p in loc) or "(document)"
            lines.append(f"  {path.name}:{_line_of(root, loc)} {field}: {err['msg']}")
        raise PipelineError(f"{path} is not valid:\n" + "\n".join(lines)) from exc


def load_rotation_input(path: Path) -> RotationInput:
    return load_yaml_model(path, RotationInput)


def load_ag_year(path: Path, site_id: str) -> AgYear:
    site = load_yaml_model(path, _SiteAgYear)
    if site.id != site_id:
        raise PipelineError(f"{path}: id {site.id!r} != {site_id!r}")
    return site.ag_year
