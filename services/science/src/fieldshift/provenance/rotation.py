# SI-assisted: Claude Code (Anthropic); review: pending (see SI-USAGE.md)
"""FR19 provenance for the current rotation (agronomist input) and its soil-cover timeline."""

from __future__ import annotations

from fieldshift.contracts import LocalizedText, Period, Provenance, Ref
from fieldshift.contracts.provenance import (
    ProvenanceMethod,
    ProvenanceSpatial,
    ProvenanceTemporal,
    ProvenanceVariable,
)

SOIL_COVER_METHOD = "soil-cover-derivation v1"
SOIL_COVER_DOC_ANCHOR = "soil-cover-derivation"  # content/methods must define it; see the PR
SOIL_COVER_REF = Ref(
    label="FieldShift architecture, Data Models: soil-cover derivation rule v1",
    citation=(
        "Monthly soil state from the rotation calendar: establishment months are 'transition', "
        "overlaps keep the most protective state, months without a segment are 'bare'."
    ),
)


def _text(en: str) -> LocalizedText:
    return LocalizedText(en=en)


def rotation_prov_id(site_id: str) -> str:
    return f"prov:user:{site_id}:rotation-current"


def soil_cover_prov_id(site_id: str) -> str:
    return f"prov:computed:{site_id}:soil-cover:monthly"


def _unique_refs(refs: list[Ref]) -> list[Ref]:
    seen: set[tuple] = set()
    out: list[Ref] = []
    for ref in refs:
        key = (ref.label, ref.url, ref.doi, ref.citation)
        if key not in seen:
            seen.add(key)
            out.append(ref)
    return out


def rotation_record(
    site_id: str, authored_by: str, refs: list[Ref], period: Period, dev: bool = False
) -> Provenance:
    limitations = [
        _text(
            "Reference rotation of a typical year, written by the agronomist; actual planting and "
            "harvest dates vary from year to year and are not observed here."
        ),
        _text("Monthly granularity: a crop planted or harvested on any day counts for that month."),
    ]
    if dev:
        limitations.insert(0, _text("DEV ONLY: development site, not a demo site."))
    return Provenance(
        id=rotation_prov_id(site_id),
        data_type="user_provided",
        title=_text("Current crop rotation (planting and harvest calendar)"),
        variable=ProvenanceVariable(
            code="rotation_segment", name=_text("Crop rotation segments"), unit="1"
        ),
        spatial=ProvenanceSpatial(resolution="field", support="polygon"),
        temporal=ProvenanceTemporal(resolution="monthly", period=period),
        aggregation=_text("Planting and harvest months per crop, as written by the agronomist."),
        authored_by=authored_by,
        refs=_unique_refs(refs),
        limitations=limitations,
    )


def soil_cover_record(site_id: str, period: Period, dev: bool = False) -> Provenance:
    limitations = [
        _text(
            "Derived from the rotation calendar only: it is not a satellite observation of bare "
            "soil."
        ),
        _text(
            "A month with no crop, cover crop or residue in the rotation is counted as bare soil."
        ),
    ]
    if dev:
        limitations.insert(0, _text("DEV ONLY: development site, not a demo site."))
    return Provenance(
        id=soil_cover_prov_id(site_id),
        data_type="computed",
        title=_text("Monthly soil cover of the current rotation"),
        variable=ProvenanceVariable(
            code="soil_state",
            name=_text("Soil state (covered, residue, transition, bare)"),
            unit="1",
        ),
        spatial=ProvenanceSpatial(resolution="field", support="polygon"),
        temporal=ProvenanceTemporal(resolution="monthly", period=period),
        aggregation=_text(
            "One state per month of the agricultural year; bare-soil months per year = bare "
            "months divided by the cycle length in years."
        ),
        method=ProvenanceMethod(
            name=SOIL_COVER_METHOD, ref=SOIL_COVER_REF, doc_anchor=SOIL_COVER_DOC_ANCHOR
        ),
        inputs=[rotation_prov_id(site_id)],
        limitations=limitations,
    )
