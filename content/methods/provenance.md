---
anchor: provenance
title: Provenance and data types
order: 50
refs:
  - label: "Project data contract: Provenance (v1.0.0)"
    url: https://github.com/FieldShift-SpaceApp/fieldshift/blob/main/packages/contracts/schema/contracts.schema.json
limitations:
  - "The automatic check that every number on screen has provenance runs on the pages that show site data; documentation pages such as this one describe datasets and do not show data values."
---

<!-- SI-assisted: written with Claude Code (Anthropic) from the PRD (FR9, FR19) and the project architecture (Provenance contract, ADR-8); human review pending (see SI-USAGE.md). -->

**Every number has a source.** Each number the app shows from data points to a provenance record. Clicking the number opens the record, and its source link is one more click away. A record holds:

- dataset and provider; product and version (or collection ID);
- variable and unit;
- spatial and temporal resolution; period;
- how the value was aggregated;
- data type (below);
- access date; link or DOI; terms of use;
- for computed values, the method and the records it was computed from;
- known limitations.

**Data types.** Every value carries one of four labels, always as text:

| Label | Meaning | Required in its record |
|---|---|---|
| Satellite-observed | measured by a satellite instrument and processed into a product | source with version or collection ID; access link, date and terms |
| Modeled | produced by a model or reanalysis that combines observations with physics | source with version or collection ID; access link, date and terms |
| Computed | calculated by this project from other values | the method (a section on this page) and at least one input record |
| User-provided | entered by a person, such as the site's current crop rotation | who provided it and at least one reference |

**Automatic checks.** The data pipeline validates every record when it writes it. Tests check that every value points to an existing record and that every method link points to a section on this page. On site pages, a browser test checks that every number on screen sits inside an element that carries provenance.
